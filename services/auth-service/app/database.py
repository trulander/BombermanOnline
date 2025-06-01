from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
from contextlib import asynccontextmanager
import sqlalchemy.ext.asyncio as sa_asyncio
import logging

logger = logging.getLogger(__name__)

#TODO убрать DATABASE_URL код отсюда и использовать settings файл, там есть все что нужно для этого

# Создаем URL для подключения к базе данных
DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Создаем движок SQLAlchemy для асинхронной работы
engine = sa_asyncio.create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Создаем сессию
async_session = sa_asyncio.async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Создаем базовый класс для моделей
Base = declarative_base()

# Класс для работы с базой данных
class Database:
    def __init__(self) -> None:
        self.engine = engine
        self.async_session = async_session
    
    async def connect(self) -> None:
        """Подключение к базе данных"""
        try:
            async with self.engine.begin() as conn:
                # Проверка соединения
                # await conn.execute(sa_asyncio.text("SELECT 1"))
                logger.info("Connected to PostgreSQL database")
                
                # В разработке можно создать таблицы автоматически
                if settings.DEBUG:
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}", exc_info=True)
            raise
    
    async def disconnect(self) -> None:
        """Отключение от базы данных"""
        try:
            await self.engine.dispose()
            logger.info("Disconnected from PostgreSQL database")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}", exc_info=True)
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Получение сессии для работы с базой данных"""
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()

db = Database() 