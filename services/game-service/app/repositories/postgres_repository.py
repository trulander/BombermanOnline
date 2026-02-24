from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from contextlib import asynccontextmanager
import sqlalchemy.ext.asyncio as sa_asyncio
from app.config import settings
import logging


logger = logging.getLogger(__name__)

# Создаем базовый класс для моделей
Base = declarative_base()



class PostgresRepository:
    def __init__(self) -> None:

        self.engine = None
        self.async_session = None

    async def _ensure_connected(self) -> None:
        """Обеспечивает подключение к базе данных с автореконнектом"""
        try:
            if not self.async_session:
                await self.connect()
            # Проверяем состояние SQLAlchemy engine
            if self.engine is None:
                await self.connect()
        except Exception as e:
            logger.warning(f"Connection check failed, reconnecting: {e}")
            await self.connect()

    async def connect(self) -> None:
        """Подключение к базе данных"""
        try:
            # Создаем движок SQLAlchemy для асинхронной работы
            self.engine = sa_asyncio.create_async_engine(
                settings.ASYNC_DATABASE_URI,
                future=True,
            )

            # Создаем сессию
            self.async_session = sa_asyncio.async_sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
            
            # Проверяем подключение SQLAlchemy
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Connected to PostgreSQL database")

        except Exception as e:
            logger.error(f"Error connecting to database: {e}", exc_info=True)
            raise

    async def disconnect(self) -> None:
        """Отключение от базы данных"""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("Disconnected from PostgreSQL database")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}", exc_info=True)
            raise

    @asynccontextmanager
    async def get_session(self):
        """Получение сессии для работы с базой данных через SQLAlchemy"""
        await self._ensure_connected()
            
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
