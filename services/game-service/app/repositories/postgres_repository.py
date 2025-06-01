from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import sqlalchemy.ext.asyncio as sa_asyncio
import asyncpg
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем пул подключений asyncpg
async_pool: asyncpg.Pool = None


class PostgresRepository:
    def __init__(self) -> None:
        self._pool: asyncpg.Pool = None
        self.engine = None
        self.async_session = None

    async def connect(self) -> None:
        """Подключение к базе данных"""
        try:
            # Создаем движок SQLAlchemy для асинхронной работы
            self.engine = sa_asyncio.create_async_engine(
                settings.ASYNC_DATABASE_URI,
                echo=settings.DEBUG,
                future=True,
            )

            # Создаем сессию
            self.async_session = sa_asyncio.async_sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
            
            # Инициализируем пул подключений asyncpg
            self._pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=5,
                max_size=20
            )
            
            # Проверяем подключение SQLAlchemy
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Connected to PostgreSQL database")

                # В разработке можно создать таблицы автоматически
                if settings.DEBUG:
                    # Импортируем модели для создания таблиц
                    from app.models.map_models import Base as ModelsBase
                    await conn.run_sync(ModelsBase.metadata.create_all)
                    logger.info("Database tables created")
                    
        except Exception as e:
            logger.error(f"Error connecting to database: {e}", exc_info=True)
            raise

    async def disconnect(self) -> None:
        """Отключение от базы данных"""
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
                logger.info("AsyncPG pool closed")
                
            if self.engine:
                await self.engine.dispose()
                logger.info("Disconnected from PostgreSQL database")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}", exc_info=True)
            raise

    @asynccontextmanager
    async def get_session(self):
        """Получение сессии для работы с базой данных через SQLAlchemy"""
        if not self.async_session:
            raise RuntimeError("Database not connected. Call connect() first.")
            
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

    @asynccontextmanager
    async def get_connection(self):
        """Получение соединения для работы с базой данных через asyncpg"""
        if not self._pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self._pool.acquire() as connection:
            yield connection

    @property
    def pool(self) -> asyncpg.Pool:
        """Получение пула подключений"""
        if not self._pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        return self._pool


# Глобальный экземпляр репозитория
db = PostgresRepository()