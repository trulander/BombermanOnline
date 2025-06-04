import json
import logging
import uuid
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import select, insert, update, delete, and_, or_, func

from ..models.map_models import (
    MapTemplate, MapGroup, MapChain,
    MapTemplateORM, MapGroupORM, MapChainORM,
    MapTemplateCreate, MapTemplateUpdate,
    MapGroupCreate, MapGroupUpdate,
    MapChainCreate, MapChainUpdate,
    MapTemplateFilter, MapGroupFilter, MapChainFilter
)

if TYPE_CHECKING:
    from .redis_repository import RedisRepository
    from .postgres_repository import PostgresRepository



logger = logging.getLogger(__name__)


class MapRepository:
    """Репозиторий для работы с картами в PostgreSQL и Redis"""
    
    def __init__(self, redis_repository:"RedisRepository", postgres_repository:"PostgresRepository"):
        self.postgres_repository = postgres_repository
        self.redis_repository = redis_repository
        self.cache_ttl = 3600  # 1 час

    
    # CRUD операции для MapTemplate
    async def create_map_template(self, template_data: MapTemplateCreate, created_by: str) -> MapTemplate:
        """Создать новый шаблон карты"""
        try:
            template_id = str(uuid.uuid4())
            
            async with self.postgres_repository.get_session() as session:
                new_template = MapTemplateORM(
                    id=template_id,
                    name=template_data.name,
                    description=template_data.description,
                    width=template_data.width,
                    height=template_data.height,
                    grid_data=template_data.grid_data,
                    difficulty=template_data.difficulty,
                    max_players=template_data.max_players,
                    min_players=template_data.min_players,
                    estimated_play_time=template_data.estimated_play_time,
                    tags=template_data.tags,
                    created_by=created_by,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(new_template)
                await session.flush()
                
                result = MapTemplate.from_orm(new_template)
                
                # Кешируем в Redis
                cache_key = f"map_template:{template_id}"
                template_dict = result.dict()
                template_dict['created_at'] = template_dict['created_at'].isoformat()
                template_dict['updated_at'] = template_dict['updated_at'].isoformat()
                await self.redis_repository.set(cache_key, template_dict, expire=self.cache_ttl)
                
                logger.info(f"Map template created: {template_id}")
                return result
                
        except Exception as e:
            logger.error(f"Error creating map template: {e}", exc_info=True)
            raise
    
    async def get_map_template(self, map_id: str) -> Optional[MapTemplate]:
        """Получить шаблон карты по ID"""
        try:
            # Сначала проверяем кеш
            cache_key = f"map_template:{map_id}"
            cached_data = await self.redis_repository.get(cache_key)
            
            if cached_data:
                # Восстанавливаем datetime объекты
                cached_data['created_at'] = datetime.fromisoformat(cached_data['created_at'])
                cached_data['updated_at'] = datetime.fromisoformat(cached_data['updated_at'])
                logger.debug(f"Map template {map_id} loaded from cache")
                return MapTemplate(**cached_data)
            
            # Если нет в кеше, запрашиваем из базы
            async with self.postgres_repository.get_session() as session:
                result = await session.execute(
                    select(MapTemplateORM).where(
                        and_(MapTemplateORM.id == map_id, MapTemplateORM.is_active == True)
                    )
                )
                row = result.scalar_one_or_none()
                
                if not row:
                    logger.debug(f"Map template {map_id} not found")
                    return None
                
                map_template = MapTemplate.from_orm(row)
                
                # Кешируем результат
                template_dict = map_template.dict()
                template_dict['created_at'] = template_dict['created_at'].isoformat()
                template_dict['updated_at'] = template_dict['updated_at'].isoformat()
                await self.redis_repository.set(cache_key, template_dict, expire=self.cache_ttl)
                
                logger.debug(f"Map template {map_id} loaded from database and cached")
                return map_template
                
        except Exception as e:
            logger.error(f"Error getting map template {map_id}: {e}", exc_info=True)
            return None
    
    async def update_map_template(self, map_id: str, template_data: MapTemplateUpdate) -> Optional[MapTemplate]:
        """Обновить шаблон карты"""
        try:
            async with self.postgres_repository.get_session() as session:
                # Обновляем только переданные поля
                update_data = template_data.dict(exclude_unset=True)
                if update_data:
                    update_data['updated_at'] = datetime.utcnow()
                    
                    await session.execute(
                        update(MapTemplateORM)
                        .where(MapTemplateORM.id == map_id)
                        .values(**update_data)
                    )
                
                # Получаем обновленную запись
                result = await session.execute(
                    select(MapTemplateORM).where(MapTemplateORM.id == map_id)
                )
                row = result.scalar_one_or_none()
                
                if not row:
                    return None
                
                map_template = MapTemplate.from_orm(row)
                
                # Обновляем кеш
                cache_key = f"map_template:{map_id}"
                template_dict = map_template.dict()
                template_dict['created_at'] = template_dict['created_at'].isoformat()
                template_dict['updated_at'] = template_dict['updated_at'].isoformat()
                await self.redis_repository.set(cache_key, template_dict, expire=self.cache_ttl)
                
                logger.info(f"Map template updated: {map_id}")
                return map_template
                
        except Exception as e:
            logger.error(f"Error updating map template {map_id}: {e}", exc_info=True)
            raise
    
    async def delete_map_template(self, map_id: str) -> bool:
        """Удалить шаблон карты (мягкое удаление)"""
        try:
            async with self.postgres_repository.get_session() as session:
                result = await session.execute(
                    update(MapTemplateORM)
                    .where(MapTemplateORM.id == map_id)
                    .values(is_active=False, updated_at=datetime.utcnow())
                )
                
                if result.rowcount == 0:
                    return False
                
                # Удаляем из кеша
                cache_key = f"map_template:{map_id}"
                await self.redis_repository.delete(cache_key)
                
                logger.info(f"Map template deleted: {map_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting map template {map_id}: {e}", exc_info=True)
            return False
    
    async def list_map_templates(self, filter_params: MapTemplateFilter) -> List[MapTemplate]:
        """Получить список шаблонов карт с фильтрацией"""
        try:
            async with self.postgres_repository.get_session() as session:
                query = select(MapTemplateORM).where(MapTemplateORM.is_active == True)
                
                # Применяем фильтры
                if filter_params.name:
                    query = query.where(MapTemplateORM.name.ilike(f"%{filter_params.name}%"))
                
                if filter_params.difficulty_min is not None:
                    query = query.where(MapTemplateORM.difficulty >= filter_params.difficulty_min)
                
                if filter_params.difficulty_max is not None:
                    query = query.where(MapTemplateORM.difficulty <= filter_params.difficulty_max)
                
                if filter_params.max_players_min is not None:
                    query = query.where(MapTemplateORM.max_players >= filter_params.max_players_min)
                
                if filter_params.max_players_max is not None:
                    query = query.where(MapTemplateORM.max_players <= filter_params.max_players_max)
                
                if filter_params.created_by:
                    query = query.where(MapTemplateORM.created_by == filter_params.created_by)
                
                # Пагинация
                query = query.offset(filter_params.offset).limit(filter_params.limit)
                query = query.order_by(MapTemplateORM.created_at.desc())
                
                result = await session.execute(query)
                rows = result.scalars().all()
                
                templates = [MapTemplate.from_orm(row) for row in rows]
                logger.debug(f"Retrieved {len(templates)} map templates")
                return templates
                
        except Exception as e:
            logger.error(f"Error listing map templates: {e}", exc_info=True)
            return []
    
    # Аналогичные методы для MapGroup и MapChain
    async def create_map_group(self, group_data: MapGroupCreate, created_by: str) -> MapGroup:
        """Создать новую группу карт"""
        try:
            group_id = str(uuid.uuid4())
            
            async with self.postgres_repository.get_session() as session:
                new_group = MapGroupORM(
                    id=group_id,
                    name=group_data.name,
                    description=group_data.description,
                    map_ids=group_data.map_ids,
                    created_by=created_by,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(new_group)
                await session.flush()
                
                result = MapGroup.from_orm(new_group)
                
                # Кешируем в Redis
                cache_key = f"map_group:{group_id}"
                group_dict = result.dict()
                group_dict['created_at'] = group_dict['created_at'].isoformat()
                group_dict['updated_at'] = group_dict['updated_at'].isoformat()
                await self.redis_repository.set(cache_key, group_dict, expire=self.cache_ttl)
                
                logger.info(f"Map group created: {group_id}")
                return result
                
        except Exception as e:
            logger.error(f"Error creating map group: {e}", exc_info=True)
            raise
    
    async def get_map_group(self, group_id: str) -> Optional[MapGroup]:
        """Получить группу карт по ID"""
        try:
            cache_key = f"map_group:{group_id}"
            cached_data = await self.redis_repository.get(cache_key)
            
            if cached_data:
                cached_data['created_at'] = datetime.fromisoformat(cached_data['created_at'])
                cached_data['updated_at'] = datetime.fromisoformat(cached_data['updated_at'])
                logger.debug(f"Map group {group_id} loaded from cache")
                return MapGroup(**cached_data)
            
            async with self.postgres_repository.get_session() as session:
                result = await session.execute(
                    select(MapGroupORM).where(
                        and_(MapGroupORM.id == group_id, MapGroupORM.is_active == True)
                    )
                )
                row = result.scalar_one_or_none()
                
                if not row:
                    return None
                
                map_group = MapGroup.from_orm(row)
                
                # Кешируем результат
                group_dict = map_group.model_dump()
                group_dict['created_at'] = group_dict['created_at'].isoformat()
                group_dict['updated_at'] = group_dict['updated_at'].isoformat()
                await self.redis_repository.set(cache_key, group_dict, expire=self.cache_ttl)
                
                return map_group
                
        except Exception as e:
            logger.error(f"Error getting map group {group_id}: {e}", exc_info=True)
            return None
    
    async def create_map_chain(self, chain_data: MapChainCreate, created_by: str) -> MapChain:
        """Создать новую цепочку карт"""
        try:
            chain_id = str(uuid.uuid4())
            
            async with self.postgres_repository.get_session() as session:
                new_chain = MapChainORM(
                    id=chain_id,
                    name=chain_data.name,
                    description=chain_data.description,
                    map_ids=chain_data.map_ids,
                    difficulty_progression=chain_data.difficulty_progression,
                    created_by=created_by,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(new_chain)
                await session.flush()
                
                result = MapChain.from_orm(new_chain)
                
                # Кешируем в Redis
                cache_key = f"map_chain:{chain_id}"
                chain_dict = result.dict()
                chain_dict['created_at'] = chain_dict['created_at'].isoformat()
                chain_dict['updated_at'] = chain_dict['updated_at'].isoformat()
                await self.redis_repository.set(cache_key, chain_dict, expire=self.cache_ttl)
                
                logger.info(f"Map chain created: {chain_id}")
                return result
                
        except Exception as e:
            logger.error(f"Error creating map chain: {e}", exc_info=True)
            raise
    
    async def get_map_chain(self, chain_id: str) -> Optional[MapChain]:
        """Получить цепочку карт по ID"""
        try:
            cache_key = f"map_chain:{chain_id}"
            cached_data = await self.redis_repository.get(cache_key)
            
            if cached_data:
                cached_data['created_at'] = datetime.fromisoformat(cached_data['created_at'])
                cached_data['updated_at'] = datetime.fromisoformat(cached_data['updated_at'])
                logger.debug(f"Map chain {chain_id} loaded from cache")
                return MapChain(**cached_data)
            
            async with self.postgres_repository.get_session() as session:
                result = await session.execute(
                    select(MapChainORM).where(
                        and_(MapChainORM.id == chain_id, MapChainORM.is_active == True)
                    )
                )
                row = result.scalar_one_or_none()
                
                if not row:
                    return None
                
                map_chain = MapChain.from_orm(row)
                
                # Кешируем результат
                chain_dict = map_chain.model_dump()
                chain_dict['created_at'] = chain_dict['created_at'].isoformat()
                chain_dict['updated_at'] = chain_dict['updated_at'].isoformat()
                await self.redis_repository.set(cache_key, chain_dict, expire=self.cache_ttl)
                
                return map_chain
                
        except Exception as e:
            logger.error(f"Error getting map chain {chain_id}: {e}", exc_info=True)
            return None
    
    async def get_maps_by_difficulty(self, min_difficulty: int, max_difficulty: int) -> List[MapTemplate]:
        """Получить карты по уровню сложности"""
        try:
            async with self.postgres_repository.get_session() as session:
                result = await session.execute(
                    select(MapTemplateORM)
                    .where(
                        and_(
                            MapTemplateORM.difficulty.between(min_difficulty, max_difficulty),
                            MapTemplateORM.is_active == True
                        )
                    )
                    .order_by(MapTemplateORM.difficulty, MapTemplateORM.name)
                )
                
                maps = []
                for row in result.scalars():
                    map_template = MapTemplate.from_orm(row)
                    maps.append(map_template)
                
                return maps
                
        except Exception as e:
            logger.error(f"Error getting maps by difficulty {min_difficulty}-{max_difficulty}: {e}", exc_info=True)
            return []

    # Добавляем недостающие методы для Groups и Chains
    async def list_map_groups(self, filter_params: MapGroupFilter) -> List[MapGroup]:
        """Получить список групп карт с фильтрацией"""
        try:
            async with self.postgres_repository.get_session() as session:
                query = select(MapGroupORM).where(MapGroupORM.is_active == True)
                
                # Применяем фильтры
                if filter_params.name:
                    query = query.where(MapGroupORM.name.ilike(f"%{filter_params.name}%"))
                
                if filter_params.created_by:
                    query = query.where(MapGroupORM.created_by == filter_params.created_by)
                
                # Пагинация
                query = query.offset(filter_params.offset).limit(filter_params.limit)
                query = query.order_by(MapGroupORM.created_at.desc())
                
                result = await session.execute(query)
                rows = result.scalars().all()
                
                groups = [MapGroup.from_orm(row) for row in rows]
                logger.debug(f"Retrieved {len(groups)} map groups")
                return groups
                
        except Exception as e:
            logger.error(f"Error listing map groups: {e}", exc_info=True)
            return []

    async def list_map_chains(self, filter_params: MapChainFilter) -> List[MapChain]:
        """Получить список цепочек карт с фильтрацией"""
        try:
            async with self.postgres_repository.get_session() as session:
                query = select(MapChainORM).where(MapChainORM.is_active == True)
                
                # Применяем фильтры
                if filter_params.name:
                    query = query.where(MapChainORM.name.ilike(f"%{filter_params.name}%"))
                
                if filter_params.created_by:
                    query = query.where(MapChainORM.created_by == filter_params.created_by)
                
                # Пагинация
                query = query.offset(filter_params.offset).limit(filter_params.limit)
                query = query.order_by(MapChainORM.created_at.desc())
                
                result = await session.execute(query)
                rows = result.scalars().all()
                
                chains = [MapChain.from_orm(row) for row in rows]
                logger.debug(f"Retrieved {len(chains)} map chains")
                return chains
                
        except Exception as e:
            logger.error(f"Error listing map chains: {e}", exc_info=True)
            return [] 