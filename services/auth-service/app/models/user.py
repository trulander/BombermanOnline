from datetime import datetime, UTC
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum as PyEnum
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

from database import Base

# Enum для ролей пользователей
class UserRole(PyEnum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    DEVELOPER = "developer"

# SQLAlchemy модель пользователя
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(100), nullable=True)
    profile_image = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default=UserRole.USER.value)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_oauth_user = Column(Boolean, default=False, nullable=False)
    oauth_provider = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    verification_token = Column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"

# Pydantic модели для валидации и сериализации

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", description="Имя пользователя")
    full_name: str | None = Field(None, max_length=100, description="Полное имя пользователя")
    profile_image: str | None = Field(None, description="URL изображения профиля")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError('Имя пользователя может содержать только латинские буквы, цифры, символы подчеркивания и дефисы')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Пароль пользователя (не менее 8 символов)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Пароль должен содержать не менее 8 символов')
        # Проверка на наличие хотя бы одной буквы и одной цифры
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError('Пароль должен содержать как минимум одну букву и одну цифру')
        return v

class UserResponse(UserBase):
    id: uuid.UUID = Field(..., description="ID пользователя")
    role: str = Field(..., description="Роль пользователя")
    is_active: bool = Field(..., description="Активен ли пользователь")
    is_verified: bool = Field(..., description="Подтвержден ли email пользователя")
    created_at: datetime = Field(..., description="Дата создания пользователя")

class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=100, description="Полное имя пользователя")
    profile_image: str | None = Field(None, description="URL изображения профиля")
    
class UserInDB(UserResponse):
    hashed_password: str | None = Field(None, description="Хэшированный пароль пользователя")
    is_oauth_user: bool = Field(..., description="Аутентифицирован ли пользователь через OAuth")
    oauth_provider: str | None = Field(None, description="Провайдер OAuth аутентификации")
    updated_at: datetime = Field(..., description="Дата обновления данных пользователя")
    last_login_at: datetime | None = Field(None, description="Дата последнего входа пользователя")

# Модель для ответа при поиске пользователей
class UserSearchResponse(BaseModel):
    items: list[UserResponse] = Field(..., description="Список пользователей")
    total: int = Field(..., description="Общее количество пользователей")
    page: int = Field(..., description="Текущая страница")
    size: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц") 