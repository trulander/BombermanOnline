from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta, UTC
import logging
import uuid
import secrets
from jose import jwt, JWTError
from typing import Optional

from ..models.user import User
from ..models.token import RefreshToken, Token, TokenData
from ..config import settings
from ..redis_client import redis_client

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Создает JWT токен доступа"""
        to_encode = data.copy()
        
        # Если срок истечения не указан, используем значение из настроек
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Устанавливаем время истечения
        expire = datetime.now(UTC) + expires_delta
        to_encode.update({"exp": expire.timestamp()})
        
        # Генерируем уникальный ID токена
        to_encode.update({"jti": str(uuid.uuid4())})
        
        # Создаем токен
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    async def create_tokens_for_user(self, user: User, remember_me: bool = False, ip_address: str = None, user_agent: str = None) -> Token:
        """Создает пару токенов - access и refresh - для пользователя"""
        try:
            # Создаем данные для токена
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
                "is_verified": user.is_verified
            }
            
            # Создаем access token
            access_token = self._create_access_token(token_data)
            
            # Устанавливаем срок действия refresh токена
            expires_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
            if remember_me:
                expires_days = expires_days * 2  # Увеличиваем срок для "Запомнить меня"
            
            expires_at = datetime.now(UTC) + timedelta(days=expires_days)
            
            # Создаем refresh токен
            refresh_token_value = secrets.token_urlsafe(64)
            
            # Сохраняем refresh токен в БД
            refresh_token = RefreshToken(
                user_id=user.id,
                token=refresh_token_value,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(refresh_token)
            await self.db.commit()
            
            # Вычисляем время жизни токена в секундах
            expires_in = int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())
            
            logger.info(f"Created tokens for user {user.id}")
            
            # Возвращаем модель с токенами
            return Token(
                access_token=access_token,
                refresh_token=refresh_token_value,
                token_type="bearer",
                expires_in=expires_in
            )
            
        except Exception as e:
            logger.error(f"Error creating tokens: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def refresh_tokens(self, refresh_token: str, ip_address: str = None, user_agent: str = None) -> Optional[Token]:
        """Обновляет пару токенов по refresh токену"""
        try:
            # Находим refresh токен в БД
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.token == refresh_token,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.now(UTC)
                )
            )
            token_record = result.scalars().first()
            
            if not token_record:
                logger.warning(f"Attempt to use invalid or expired refresh token")
                return None
            
            # Получаем пользователя
            user_id = token_record.user_id
            
            # Удаляем использованный токен
            await self.db.delete(token_record)
            await self.db.commit()
            
            # Получаем пользователя по ID
            from .user_service import UserService
            user_service = UserService(self.db)
            user = await user_service.get_by_id(user_id)
            
            if not user or not user.is_active:
                logger.warning(f"User {user_id} not found or inactive during token refresh")
                return None
            
            # Создаем новую пару токенов
            return await self.create_tokens_for_user(user, ip_address=ip_address, user_agent=user_agent)
            
        except Exception as e:
            logger.error(f"Error refreshing tokens: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """Добавляет токен в черный список"""
        try:
            # Пробуем декодировать токен, чтобы узнать время истечения
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )
                
                token_data = TokenData(**payload)
                
                # Вычисляем оставшееся время жизни токена
                if token_data.exp:
                    now = datetime.now(UTC).timestamp()
                    time_left = max(int(token_data.exp - now), 0)
                    
                    # Добавляем токен в черный список в Redis с таким же сроком истечения
                    await redis_client.block_token(token, time_left)
                    logger.info(f"Token for user {token_data.sub} revoked and blacklisted")
                    return True
                
            except JWTError:
                logger.warning("Could not decode token during revocation")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}", exc_info=True)
            return False
    
    async def revoke_all_user_tokens(self, user_id: str | uuid.UUID) -> bool:
        """Отзывает все refresh токены пользователя"""
        try:
            # Находим все refresh токены пользователя
            result = await self.db.execute(
                select(RefreshToken).where(RefreshToken.user_id == user_id)
            )
            tokens = result.scalars().all()
            
            # Отмечаем все токены как отозванные
            for token in tokens:
                token.is_revoked = True
            
            await self.db.commit()
            logger.info(f"All tokens for user {user_id} revoked")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking all user tokens: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def cleanup_expired_tokens(self) -> int:
        """Удаление просроченных refresh токенов из БД"""
        try:
            # Находим и удаляем просроченные токены
            result = await self.db.execute(
                delete(RefreshToken).where(
                    RefreshToken.expires_at < datetime.now(UTC)
                )
            )
            
            deleted_count = result.rowcount
            await self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} expired refresh tokens")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}", exc_info=True)
            await self.db.rollback()
            return 0 