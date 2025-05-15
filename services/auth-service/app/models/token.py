from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from pydantic import BaseModel, Field
from typing import Any, Optional
from fastapi import Form

from ..database import Base

# SQLAlchemy модель для токенов обновления
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<RefreshToken user_id={self.user_id}>"

# Pydantic модели для токенов

class TokenData(BaseModel):
    sub: str = Field(..., description="ID пользователя (subject)")
    exp: int = Field(..., description="Время истечения токена (Unix timestamp)")
    role: str = Field(..., description="Роль пользователя")
    username: str = Field(..., description="Имя пользователя")
    is_verified: bool = Field(..., description="Подтвержден ли email пользователя")
    jti: str = Field(..., description="Уникальный ID токена")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT токен доступа")
    refresh_token: str = Field(..., description="Токен обновления")
    token_type: str = Field("bearer", description="Тип токена")
    expires_in: int = Field(..., description="Время истечения токена в секундах")

class TokenPayload(BaseModel):
    sub: str | None = None
    exp: float | None = None
    role: str | None = None
    username: str | None = None
    is_verified: bool | None = None
    jti: str | None = None

# Модели для аутентификации

class LoginForm(BaseModel):
    username: str = Field(..., description="Имя пользователя или email")
    password: str = Field(..., description="Пароль")
    remember_me: bool = Field(False, description="Запомнить меня (увеличивает срок жизни refresh_token)")

    @classmethod
    def as_form(
            cls,
            username: str = Form(...),
            password: str = Form(...),
            remember_me: bool = Form(False),
    ) -> "LoginForm":
        return cls(username=username, password=password, remember_me=remember_me)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh токен для обновления access токена")

class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="Email пользователя для сброса пароля")

class PasswordReset(BaseModel):
    token: str = Field(..., description="Токен сброса пароля")
    new_password: str = Field(..., min_length=8, description="Новый пароль")
    
class OAuthResponse(BaseModel):
    access_token: str | None = Field(None, description="JWT токен доступа")
    id_token: str | None = Field(None, description="ID токен (для OpenID Connect)")
    token_type: str | None = Field(None, description="Тип токена")
    expires_in: int | None = Field(None, description="Время истечения токена в секундах")
    refresh_token: str | None = Field(None, description="Токен обновления (для OAuth)")
    scope: str | None = Field(None, description="Разрешенные scope")
    
class UserInfo(BaseModel):
    sub: str | None = Field(None, description="ID пользователя")
    name: str | None = Field(None, description="Полное имя пользователя")
    given_name: str | None = Field(None, description="Имя пользователя")
    family_name: str | None = Field(None, description="Фамилия пользователя")
    email: str | None = Field(None, description="Email пользователя")
    email_verified: bool | None = Field(None, description="Подтвержден ли email пользователя")
    picture: str | None = Field(None, description="URL изображения профиля")
    locale: str | None = Field(None, description="Локаль пользователя")
    
    # Дополнительные поля для других провайдеров
    id: str | None = Field(None, description="ID пользователя (для некоторых провайдеров)")
    login: str | None = Field(None, description="Логин пользователя (для GitHub)")
    
    # Гибкое поле для любых дополнительных данных
    additional_data: dict[str, Any] | None = Field(None, description="Дополнительные данные профиля") 