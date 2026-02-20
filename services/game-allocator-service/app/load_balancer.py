import asyncio
import logging
from typing import Optional

import consul
from prometheus_api_client import PrometheusConnect

logger = logging.getLogger(__name__)


class LoadBalancer:
    """
    Universal load balancer for selecting service instances based on load metrics.
    Supports round-robin rotation between equally loaded instances.
    """
    
    def __init__(
        self,
        consul_client: consul.Consul,
        prometheus_client: PrometheusConnect,
        load_threshold: float = 2.0
    ):
        """
        Initialize LoadBalancer.
        
        Args:
            consul_client: Consul client instance
            prometheus_client: Prometheus API client instance
            load_threshold: Absolute percentage difference threshold for equal load instances
        """
        self.consul = consul_client
        self.prom = prometheus_client
        self.load_threshold = load_threshold
        self._rotation_state: dict[str, int] = {}
        self._rotation_lock = asyncio.Lock()
        logger.info(f"LoadBalancer initialized with load_threshold={load_threshold}")

    def get_instance_load(self, service_name: str, instance_id: str, address: str) -> dict:
        """
        Get load metrics (CPU and RAM) for a service instance from Prometheus.
        
        Args:
            service_name: Name of the service (e.g., "game-service", "ai-service")
            instance_id: Consul service instance ID
            address: Instance address/hostname
            
        Returns:
            Dictionary with instance_id, cpu_usage, ram_usage, and address
        """
        logger.debug(f"get_instance_load - service_name:{service_name}, instance_id:{instance_id}, address:{address}")
        
        # CPU usage (PromQL) - rate over 5 minutes
        cpu_query = f'rate(container_cpu_usage_seconds_total{{container_label_com_docker_compose_service="{service_name}", instance=~".*{address}.*"}}[5m])'
        try:
            cpu_result = self.prom.custom_query(cpu_query)
            cpu_usage = float(cpu_result[0]["value"][1]) if cpu_result else 0.0
        except Exception as e:
            logger.warning(f"Failed to get CPU usage for {service_name} instance {address}: {e}")
            cpu_usage = 0.0

        # RAM usage
        ram_query = f'container_memory_usage_bytes{{container_label_com_docker_compose_service="{service_name}", instance=~".*{address}.*"}}'
        try:
            ram_result = self.prom.custom_query(ram_query)
            ram_usage = float(ram_result[0]["value"][1]) if ram_result else 0.0
        except Exception as e:
            logger.warning(f"Failed to get RAM usage for {service_name} instance {address}: {e}")
            ram_usage = 0.0

        result = {
            "instance_id": instance_id,
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage,
            "address": address
        }
        logger.debug(f"get_instance_load - result:{result}")
        return result

    def find_equal_load_instances(
        self,
        instance_loads: list[dict],
        resource_type: str = "cpu"
    ) -> list[dict]:
        """
        Find group of instances with approximately equal load (within threshold).
        
        Args:
            instance_loads: List of instance load dictionaries with cpu_usage and ram_usage
            resource_type: Type of resource to compare ("cpu" or "ram")
            
        Returns:
            List of equally loaded instances
        """
        if not instance_loads:
            return []
        
        # Sort instances by load
        sorted_loads = sorted(
            instance_loads,
            key=lambda x: x["cpu_usage"] if resource_type == "cpu" else x["ram_usage"]
        )
        
        # Find minimum load
        min_load = sorted_loads[0]["cpu_usage"] if resource_type == "cpu" else sorted_loads[0]["ram_usage"]
        
        # Find all instances within threshold
        threshold_value = min_load + self.load_threshold
        equal_load_instances = [
            inst for inst in sorted_loads
            if (inst["cpu_usage"] if resource_type == "cpu" else inst["ram_usage"]) <= threshold_value
        ]
        
        logger.debug(
            f"find_equal_load_instances - min_load:{min_load}, threshold:{threshold_value}, "
            f"equal_load_count:{len(equal_load_instances)}, total_count:{len(instance_loads)}"
        )
        
        return equal_load_instances

    async def select_instance_with_rotation(
        self,
        service_name: str,
        equal_load_instances: list[dict],
        resource_type: str = "cpu"
    ) -> dict:
        """
        Select instance from equal load group using round-robin rotation.
        
        Args:
            service_name: Name of the service
            equal_load_instances: List of equally loaded instances
            resource_type: Type of resource ("cpu" or "ram")
            
        Returns:
            Selected instance dictionary
        """
        if not equal_load_instances:
            raise ValueError("equal_load_instances cannot be empty")
        
        if len(equal_load_instances) == 1:
            return equal_load_instances[0]
        
        # Create rotation key from sorted addresses
        addresses = sorted([inst["address"] for inst in equal_load_instances])
        rotation_key = f"{service_name}:{resource_type}:{','.join(addresses)}"
        
        async with self._rotation_lock:
            # Get current rotation index
            current_index = self._rotation_state.get(rotation_key, 0)
            
            # Select instance by index
            selected_instance = equal_load_instances[current_index % len(equal_load_instances)]
            
            # Increment index for next request
            self._rotation_state[rotation_key] = (current_index + 1) % len(equal_load_instances)
            
            logger.debug(
                f"select_instance_with_rotation - service:{service_name}, "
                f"key:{rotation_key}, index:{current_index}, "
                f"selected:{selected_instance['address']}"
            )
            
            return selected_instance

    async def select_best_instance(
        self,
        service_name: str,
        instances: list[dict],
        resource_type: str = "cpu"
    ) -> Optional[dict]:
        """
        Select best instance for service using load balancing logic.
        
        Args:
            service_name: Name of the service
            instances: List of service instances from Consul (with Service dict)
            resource_type: Type of resource to optimize for ("cpu" or "ram")
            
        Returns:
            Selected instance dictionary with address, rest_port, grpc_port or None
        """
        if not instances:
            logger.warning(f"No instances provided for {service_name}")
            return None
        
        if len(instances) == 1:
            # Single instance - return it directly
            service = instances[0]["Service"]
            return {
                "address": service["Address"],
                "rest_port": int(service.get("Meta", {}).get("rest_api_port", 0)),
                "grpc_port": int(service.get("Meta", {}).get("grpc_port", 0)),
            }
        
        # Get load metrics for all instances
        instance_loads = []
        for instance in instances:
            service = instance["Service"]
            load_data = self.get_instance_load(
                service_name=service_name,
                instance_id=service["ID"],
                address=service["Address"]
            )
            instance_loads.append(load_data)
        
        # Find equally loaded instances
        equal_load_instances = self.find_equal_load_instances(
            instance_loads=instance_loads,
            resource_type=resource_type
        )
        
        if not equal_load_instances:
            logger.warning(f"No equal load instances found for {service_name}")
            return None
        
        if len(equal_load_instances) == 1:
            # Single equal load instance
            selected = equal_load_instances[0]
        else:
            # Multiple equal load instances - use round-robin
            selected = await self.select_instance_with_rotation(
                service_name=service_name,
                equal_load_instances=equal_load_instances,
                resource_type=resource_type
            )
        
        # Find corresponding instance with port information
        for instance in instances:
            service = instance["Service"]
            if service["Address"] == selected["address"]:
                return {
                    "address": service["Address"],
                    "rest_port": int(service.get("Meta", {}).get("rest_api_port", 0)),
                    "grpc_port": int(service.get("Meta", {}).get("grpc_port", 0)),
                }
        
        # Fallback if address not found (should not happen)
        logger.error(f"Selected instance address {selected['address']} not found in instances")
        return {
            "address": selected["address"],
            "rest_port": 0,
            "grpc_port": 0,
        }

