import logging
import httpx
import secrets
import uuid
from urllib.parse import urlencode
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.token import OAuthResponse, UserInfo
from .user_service import UserService
from .token_service import TokenService

logger = logging.getLogger(__name__)

class OAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.token_service = TokenService(db)
    
    def generate_oauth_state(self) -> str:
        """Генерирует случайное состояние для OAuth"""
        return secrets.token_urlsafe(32)
    
    def get_provider_authorize_url(self, provider: str, redirect_uri: str, state: str) -> Optional[str]:
        """Получает URL для авторизации через провайдера OAuth"""
        try:
            if provider not in settings.OAUTH2_PROVIDERS:
                logger.warning(f"Attempt to use unsupported OAuth provider: {provider}")
                return None
            
            provider_config = settings.OAUTH2_PROVIDERS[provider]
            
            # Параметры для запроса авторизации
            params = {
                "client_id": provider_config["client_id"],
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": provider_config["scope"],
                "state": state
            }
            
            # Дополнительные параметры для разных провайдеров
            if provider == "google":
                params["access_type"] = "offline"
                params["prompt"] = "consent"
            
            # Создаем URL для авторизации
            auth_url = f"{provider_config['authorize_endpoint']}?{urlencode(params)}"
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL for {provider}: {e}", exc_info=True)
            return None
    
    async def exchange_code_for_token(self, provider: str, code: str, redirect_uri: str) -> Optional[OAuthResponse]:
        """Обменивает код авторизации на токен доступа"""
        try:
            if provider not in settings.OAUTH2_PROVIDERS:
                logger.warning(f"Attempt to use unsupported OAuth provider: {provider}")
                return None
            
            provider_config = settings.OAUTH2_PROVIDERS[provider]
            
            # Параметры для обмена кода на токен
            data = {
                "client_id": provider_config["client_id"],
                "client_secret": provider_config["client_secret"],
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            
            # Отправляем запрос на обмен кода на токен
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    provider_config["token_endpoint"],
                    data=data,
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.warning(f"OAuth token exchange failed: {response.text}")
                    return None
                
                token_data = response.json()
                
                # Преобразуем ответ в модель
                oauth_response = OAuthResponse(
                    access_token=token_data.get("access_token"),
                    id_token=token_data.get("id_token"),
                    token_type=token_data.get("token_type"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope")
                )
                
                return oauth_response
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}", exc_info=True)
            return None
    
    async def get_user_info(self, provider: str, access_token: str) -> Optional[UserInfo]:
        """Получает информацию о пользователе от провайдера OAuth"""
        try:
            if provider not in settings.OAUTH2_PROVIDERS:
                logger.warning(f"Attempt to use unsupported OAuth provider: {provider}")
                return None
            
            provider_config = settings.OAUTH2_PROVIDERS[provider]
            
            # Отправляем запрос на получение информации о пользователе
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
                
                response = await client.get(
                    provider_config["userinfo_endpoint"],
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.warning(f"OAuth userinfo request failed: {response.text}")
                    return None
                
                user_data = response.json()
                
                # Преобразуем ответ в модель
                user_info = UserInfo(
                    sub=user_data.get("sub"),
                    name=user_data.get("name"),
                    given_name=user_data.get("given_name"),
                    family_name=user_data.get("family_name"),
                    email=user_data.get("email"),
                    email_verified=user_data.get("email_verified"),
                    picture=user_data.get("picture"),
                    locale=user_data.get("locale"),
                    id=user_data.get("id"),
                    login=user_data.get("login"),
                    additional_data=user_data
                )
                
                return user_info
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}", exc_info=True)
            return None
    
    async def authenticate_oauth_user(self, provider: str, user_info: UserInfo, 
                                     ip_address: str = None, user_agent: str = None) -> dict[str, Any]:
        """Аутентифицирует пользователя OAuth в системе"""
        try:
            if not user_info.email:
                logger.warning(f"OAuth user info missing email")
                return {"success": False, "message": "Email not provided by OAuth provider"}
            
            # Используем email в качестве основного идентификатора
            email = user_info.email
            # Используем sub или id или login в качестве имени пользователя
            username = user_info.sub or user_info.id or user_info.login or email.split('@')[0]
            # Полное имя пользователя
            name = user_info.name
            # URL изображения профиля
            picture = user_info.picture
            
            # Создаем или обновляем пользователя в системе
            user = await self.user_service.create_oauth_user(
                email=email,
                username=username,
                provider=provider,
                name=name,
                picture=picture
            )
            
            if not user:
                return {"success": False, "message": "Failed to create or update user"}
            
            # Создаем токены для пользователя
            tokens = await self.token_service.create_tokens_for_user(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_verified": user.is_verified
                },
                "tokens": {
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token,
                    "token_type": tokens.token_type,
                    "expires_in": tokens.expires_in
                }
            }
            
        except Exception as e:
            logger.error(f"Error authenticating OAuth user: {e}", exc_info=True)
            return {"success": False, "message": "Authentication failed"} 