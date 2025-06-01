from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Optional
import logging

from ..repositories.map_repository import MapRepository
from ..models.map_models import (
    MapTemplate, MapTemplateCreate, MapTemplateUpdate, MapTemplateFilter,
    MapGroup, MapGroupCreate, MapGroupUpdate, MapGroupFilter,
    MapChain, MapChainCreate, MapChainUpdate, MapChainFilter
)
from ..auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/maps", tags=["maps"])

# Зависимость для получения репозитория
async def get_map_repository() -> MapRepository:
    return MapRepository()


# Эндпоинты для Map Templates
@router.post("/templates", response_model=MapTemplate, status_code=status.HTTP_201_CREATED)
async def create_map_template(
    template_data: MapTemplateCreate,
    request: Request,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Создать новый шаблон карты"""
    try:
        created_by = current_user["id"]
        result = await map_repo.create_map_template(template_data, created_by)
        logger.info(f"Map template created by user {created_by}: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error creating map template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create map template"
        )


@router.get("/templates", response_model=List[MapTemplate])
async def list_map_templates(
    name: Optional[str] = Query(None, description="Фильтр по имени карты"),
    difficulty_min: Optional[int] = Query(None, ge=1, le=10, description="Минимальная сложность"),
    difficulty_max: Optional[int] = Query(None, ge=1, le=10, description="Максимальная сложность"),
    max_players_min: Optional[int] = Query(None, ge=1, le=8, description="Минимальное количество игроков"),
    max_players_max: Optional[int] = Query(None, ge=1, le=8, description="Максимальное количество игроков"),
    created_by: Optional[str] = Query(None, description="ID создателя"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей на страницу"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Получить список шаблонов карт с фильтрацией"""
    try:
        filter_params = MapTemplateFilter(
            name=name,
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            max_players_min=max_players_min,
            max_players_max=max_players_max,
            created_by=created_by,
            limit=limit,
            offset=offset
        )
        
        templates = await map_repo.list_map_templates(filter_params)
        logger.debug(f"Retrieved {len(templates)} map templates")
        return templates
    except Exception as e:
        logger.error(f"Error listing map templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve map templates"
        )


@router.get("/templates/{template_id}", response_model=MapTemplate)
async def get_map_template(
    template_id: str,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Получить шаблон карты по ID"""
    try:
        template = await map_repo.get_map_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map template not found"
            )
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting map template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve map template"
        )


@router.put("/templates/{template_id}", response_model=MapTemplate)
async def update_map_template(
    template_id: str,
    template_data: MapTemplateUpdate,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Обновить шаблон карты"""
    try:
        # Проверяем существование шаблона
        existing_template = await map_repo.get_map_template(template_id)
        if not existing_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map template not found"
            )
        
        # Проверяем права (только создатель или админ может редактировать)
        if existing_template.created_by != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to edit this template"
            )
        
        updated_template = await map_repo.update_map_template(template_id, template_data)
        if not updated_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map template not found"
            )
        
        logger.info(f"Map template updated by user {current_user['id']}: {template_id}")
        return updated_template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating map template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update map template"
        )


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_map_template(
    template_id: str,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Удалить шаблон карты (мягкое удаление)"""
    try:
        # Проверяем существование шаблона
        existing_template = await map_repo.get_map_template(template_id)
        if not existing_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map template not found"
            )
        
        # Проверяем права (только создатель или админ может удалять)
        if existing_template.created_by != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this template"
            )
        
        success = await map_repo.delete_map_template(template_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map template not found"
            )
        
        logger.info(f"Map template deleted by user {current_user['id']}: {template_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting map template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete map template"
        )


# Эндпоинты для Map Groups
@router.post("/groups", response_model=MapGroup, status_code=status.HTTP_201_CREATED)
async def create_map_group(
    group_data: MapGroupCreate,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Создать новую группу карт"""
    try:
        created_by = current_user["id"]
        result = await map_repo.create_map_group(group_data, created_by)
        logger.info(f"Map group created by user {created_by}: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error creating map group: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create map group"
        )


@router.get("/groups", response_model=List[MapGroup])
async def list_map_groups(
    name: Optional[str] = Query(None, description="Фильтр по имени группы"),
    created_by: Optional[str] = Query(None, description="ID создателя"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Получить список групп карт"""
    try:
        filter_params = MapGroupFilter(
            name=name,
            created_by=created_by,
            limit=limit,
            offset=offset
        )
        
        groups = await map_repo.list_map_groups(filter_params)
        logger.debug(f"Retrieved {len(groups)} map groups")
        return groups
    except Exception as e:
        logger.error(f"Error listing map groups: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve map groups"
        )


@router.get("/groups/{group_id}", response_model=MapGroup)
async def get_map_group(
    group_id: str,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Получить группу карт по ID"""
    try:
        group = await map_repo.get_map_group(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map group not found"
            )
        return group
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting map group {group_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve map group"
        )


# Эндпоинты для Map Chains
@router.post("/chains", response_model=MapChain, status_code=status.HTTP_201_CREATED)
async def create_map_chain(
    chain_data: MapChainCreate,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Создать новую цепочку карт"""
    try:
        created_by = current_user["id"]
        result = await map_repo.create_map_chain(chain_data, created_by)
        logger.info(f"Map chain created by user {created_by}: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error creating map chain: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create map chain"
        )


@router.get("/chains", response_model=List[MapChain])
async def list_map_chains(
    name: Optional[str] = Query(None, description="Фильтр по имени цепочки"),
    created_by: Optional[str] = Query(None, description="ID создателя"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Получить список цепочек карт"""
    try:
        filter_params = MapChainFilter(
            name=name,
            created_by=created_by,
            limit=limit,
            offset=offset
        )
        
        chains = await map_repo.list_map_chains(filter_params)
        logger.debug(f"Retrieved {len(chains)} map chains")
        return chains
    except Exception as e:
        logger.error(f"Error listing map chains: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve map chains"
        )


@router.get("/chains/{chain_id}", response_model=MapChain)
async def get_map_chain(
    chain_id: str,
    map_repo: MapRepository = Depends(get_map_repository),
    current_user: dict = Depends(get_current_user)
):
    """Получить цепочку карт по ID"""
    try:
        chain = await map_repo.get_map_chain(chain_id)
        if not chain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map chain not found"
            )
        return chain
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting map chain {chain_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve map chain"
        ) 