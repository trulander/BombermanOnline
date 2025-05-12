import time
import json
from typing import Any, Callable, Dict, Optional
import socketio
from prometheus_client import Counter, Gauge, Histogram

class MetricsSocketServer(socketio.AsyncServer):
    """Socket.IO сервер с автоматическим сбором метрик Prometheus"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_metrics()
        self._wrap_socketio_methods()
    
    def _init_metrics(self):
        """Инициализация метрик Prometheus"""
        # Метрики подключений
        self.active_connections = Gauge(
            'socketio_active_connections', 
            'Number of active Socket.IO connections'
        )
        self.connections_total = Counter(
            'socketio_connections_total', 
            'Total number of Socket.IO connections'
        )
        self.disconnections_total = Counter(
            'socketio_disconnections_total', 
            'Total number of Socket.IO disconnections'
        )
        
        # Метрики для событий
        self.events_total = Counter(
            'socketio_events_total', 
            'Total number of Socket.IO events',
            ['event_type', 'direction']  # direction: incoming/outgoing
        )
        
        # Метрики для времени обработки
        self.event_processing_time = Histogram(
            'socketio_event_processing_time', 
            'Event processing time in seconds',
            ['event_type'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
        )
        
        # Метрики для размера сообщений
        self.message_size_bytes = Histogram(
            'socketio_message_size_bytes', 
            'Size of Socket.IO messages in bytes',
            ['event_type', 'direction'],  # direction: incoming/outgoing
            buckets=(10, 100, 1000, 5000, 10000, 50000, 100000)
        )
        
        # Метрика для игровых комнат
        self.active_games = Gauge(
            'socketio_active_games', 
            'Number of active game rooms'
        )
    
    def _wrap_socketio_methods(self):
        """Переопределение методов Socket.IO для добавления метрик"""
        # Обернуть метод on для перехвата входящих сообщений
        original_on = self.on
        
        def wrapped_on(event, handler=None):
            """Обертка для метода on"""
            original_handler = handler
            
            async def metrics_handler(*args, **kwargs):
                start_time = time.time()
                event_type = event
                
                # Увеличить счетчик входящих событий
                self.events_total.labels(event_type=event_type, direction='incoming').inc()
                
                # Замерить размер данных
                if len(args) > 1 and args[1] is not None:
                    try:
                        data_size = len(json.dumps(args[1]).encode('utf-8'))
                        self.message_size_bytes.labels(event_type=event_type, direction='incoming').observe(data_size)
                    except:
                        pass
                
                # Выполнить оригинальный обработчик
                try:
                    result = await original_handler(*args, **kwargs)
                    return result
                finally:
                    # Замерить время выполнения
                    self.event_processing_time.labels(event_type=event_type).observe(time.time() - start_time)
            
            # Если обрабатываем connect/disconnect, добавляем логику для счетчиков подключений
            if event == 'connect':
                async def connect_handler(*args, **kwargs):
                    self.active_connections.inc()
                    self.connections_total.inc()
                    return await metrics_handler(*args, **kwargs)
                return original_on(event, connect_handler)
            elif event == 'disconnect':
                async def disconnect_handler(*args, **kwargs):
                    self.active_connections.dec()
                    self.disconnections_total.inc()
                    return await metrics_handler(*args, **kwargs)
                return original_on(event, disconnect_handler)
            else:
                return original_on(event, metrics_handler)
                
        self.on = wrapped_on
        
        # Обернуть метод emit для перехвата исходящих сообщений
        original_emit = self.emit
        
        async def wrapped_emit(event, data=None, room=None, skip_sid=None, namespace=None, callback=None, **kwargs):
            """Обертка для метода emit"""
            event_type = event
            
            # Увеличить счетчик исходящих событий
            self.events_total.labels(event_type=event_type, direction='outgoing').inc()
            
            # Замерить размер данных
            if data is not None:
                try:
                    data_size = len(json.dumps(data).encode('utf-8'))
                    self.message_size_bytes.labels(event_type=event_type, direction='outgoing').observe(data_size)
                except:
                    pass

            # # Отслеживание game_over событий для уменьшения счетчика активных игр
            # if event == 'game_over':
            #     self.active_games.dec()
                
            # Выполнить оригинальную отправку
            return await original_emit(event, data, room, skip_sid, namespace, callback, **kwargs)
            
        self.emit = wrapped_emit
        
    # Добавим методы для ручного изменения счетчика игр
    def increment_games(self):
        """Увеличить счетчик активных игр"""
        self.active_games.inc()
        
    def decrement_games(self):
        """Уменьшить счетчик активных игр"""
        self.active_games.dec()