from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from typing import Optional
import uuid
import logging
from passlib.context import CryptContext
from datetime import datetime, UTC
import secrets

from ..models.user import User, UserCreate, UserResponse, UserUpdate, UserSearchResponse, UserRole
from ..config import settings

logger = logging.getLogger(__name__)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)
    
    async def get_by_id(self, user_id: str | uuid.UUID) -> Optional[User]:
        """Получение пользователя по ID"""
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None
        
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalars().first()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по имени пользователя"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()
    
    async def authenticate(self, username_or_email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по имени пользователя/email и паролю"""
        # Проверяем, это email или username
        if "@" in username_or_email:
            user = await self.get_by_email(username_or_email)
        else:
            user = await self.get_by_username(username_or_email)
        
        if not user:
            return None
        
        # Проверяем пароль
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Обновляем дату последнего входа
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        
        return user
    
    async def create(self, user_data: UserCreate) -> Optional[User]:
        """Создание нового пользователя"""
        try:
            # Проверяем, что пользователь с таким email не существует
            existing_email = await self.get_by_email(user_data.email)
            if existing_email:
                logger.warning(f"Attempt to create user with existing email: {user_data.email}")
                return None
            
            # Проверяем, что пользователь с таким username не существует
            existing_username = await self.get_by_username(user_data.username)
            if existing_username:
                logger.warning(f"Attempt to create user with existing username: {user_data.username}")
                return None
            
            # Хешируем пароль
            hashed_password = self.hash_password(user_data.password)
            
            # Создаем нового пользователя
            user = User(
                email=user_data.email.lower(),
                username=user_data.username,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                profile_image=user_data.profile_image,
                role=UserRole.USER.value,  # По умолчанию роль - user
                verification_token=secrets.token_urlsafe(32)
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Created user with id {user.id}")
            return user
            
        except IntegrityError as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            await self.db.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def update(self, user_id: str | uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """Обновление данных пользователя"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            # Обновляем поля, которые переданы в запросе
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            
            if user_data.profile_image is not None:
                user.profile_image = user_data.profile_image
            
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Updated user with id {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating user: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def update_password(self, user_id: str | uuid.UUID, new_password: str) -> bool:
        """Обновление пароля пользователя"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # Хешируем новый пароль
            hashed_password = self.hash_password(new_password)
            user.hashed_password = hashed_password
            
            await self.db.commit()
            
            logger.info(f"Updated password for user with id {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating password: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def delete(self, user_id: str | uuid.UUID) -> bool:
        """Удаление пользователя"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            await self.db.delete(user)
            await self.db.commit()
            
            logger.info(f"Deleted user with id {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def update_role(self, user_id: str | uuid.UUID, role: str) -> Optional[User]:
        """Обновление роли пользователя"""
        try:
            # Проверяем, что роль корректная
            if role not in [r.value for r in UserRole]:
                logger.warning(f"Attempt to set invalid role: {role}")
                return None
            
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            user.role = role
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Updated role to {role} for user with id {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating user role: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def verify_email(self, token: str) -> bool:
        """Подтверждение email пользователя"""
        try:
            result = await self.db.execute(
                select(User).where(User.verification_token == token)
            )
            user = result.scalars().first()
            
            if not user:
                return False
            
            user.is_verified = True
            user.verification_token = None
            await self.db.commit()
            
            logger.info(f"Verified email for user with id {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying email: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def regenerate_verification_token(self, user_id: str | uuid.UUID) -> Optional[str]:
        """Генерация нового токена подтверждения email"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            new_token = secrets.token_urlsafe(32)
            user.verification_token = new_token
            await self.db.commit()
            
            logger.info(f"Regenerated verification token for user with id {user.id}")
            return new_token
            
        except Exception as e:
            logger.error(f"Error regenerating verification token: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def create_oauth_user(self, email: str, username: str, provider: str, 
                               name: str = None, picture: str = None) -> Optional[User]:
        """Создание или обновление пользователя, аутентифицированного через OAuth"""
        try:
            # Проверяем, существует ли пользователь с таким email
            user = await self.get_by_email(email)
            
            if user:
                # Пользователь существует, обновляем данные OAuth
                user.is_oauth_user = True
                user.oauth_provider = provider
                user.last_login_at = datetime.now(UTC)
                
                # Обновляем профиль, если данные переданы
                if name and not user.full_name:
                    user.full_name = name
                if picture and not user.profile_image:
                    user.profile_image = picture
                
                await self.db.commit()
                await self.db.refresh(user)
                logger.info(f"Updated OAuth user with id {user.id}")
                return user
                
            else:
                # Создаем нового пользователя
                # Проверяем уникальность username и генерируем новый при необходимости
                base_username = username or email.split('@')[0]
                username = base_username
                counter = 1
                
                while await self.get_by_username(username):
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Создаем пользователя
                user = User(
                    email=email.lower(),
                    username=username,
                    full_name=name,
                    profile_image=picture,
                    is_oauth_user=True,
                    oauth_provider=provider,
                    role=UserRole.USER.value,
                    is_verified=True  # OAuth пользователи сразу верифицированы
                )
                
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
                
                logger.info(f"Created OAuth user with id {user.id}")
                return user
                
        except IntegrityError as e:
            logger.error(f"Error creating/updating OAuth user: {e}", exc_info=True)
            await self.db.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error with OAuth user: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def search(self, query: str = None, page: int = 1, size: int = 10) -> UserSearchResponse:
        """Поиск пользователей по имени, имени пользователя или email"""
        try:
            # Создаем базовый запрос
            base_query = select(User)
            count_query = select(func.count()).select_from(User)
            
            # Добавляем фильтры поиска, если есть запрос
            if query:
                search_filter = (
                    User.username.ilike(f"%{query}%") |
                    User.email.ilike(f"%{query}%") |
                    User.full_name.ilike(f"%{query}%")
                )
                base_query = base_query.where(search_filter)
                count_query = count_query.where(search_filter)
            
            # Выполняем запрос на подсчет общего количества
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Добавляем пагинацию
            base_query = base_query.offset((page - 1) * size).limit(size)
            
            # Выполняем запрос с пагинацией
            result = await self.db.execute(base_query)
            users = result.scalars().all()
            
            # Вычисляем общее количество страниц
            pages = (total + size - 1) // size
            
            # Преобразуем результаты в модель ответа
            return UserSearchResponse(
                items=[UserResponse(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name,
                    profile_image=user.profile_image,
                    role=user.role,
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    created_at=user.created_at
                ) for user in users],
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error searching users: {e}", exc_info=True)
            # В случае ошибки возвращаем пустой результат
            return UserSearchResponse(
                items=[],
                total=0,
                page=page,
                size=size,
                pages=0
            ) 