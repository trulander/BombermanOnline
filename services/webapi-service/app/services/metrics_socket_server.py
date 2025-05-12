import time
import json
from typing import Any, Callable, Dict, Optional
import socketio
from aioprometheus import Counter, Gauge, Histogram
import logging

logger = logging.getLogger(__name__)

class MetricsSocketServer(socketio.AsyncServer):
    """Socket.IO сервер с автоматическим сбором метрик Prometheus (асинхронная версия)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_metrics()

        
    def _init_metrics(self):
        """Инициализация метрик Prometheus с использованием aioprometheus"""
        # Метрики подключений
        self.active_connections = Gauge(
            'socketio_active_connections', 
            'Number of active Socket.IO connections'
        )
        self.connections_total = Counter(
            'socketio_connections_total', 
            'Total number of Socket.IO connections'
        )
        self.disconnections_total = Counter(
            'socketio_disconnections_total', 
            'Total number of Socket.IO disconnections'
        )
        
        # Метрики для событий
        self.events_total = Counter(
            'socketio_events_total', 
            'Total number of Socket.IO events'
        )
        
        # Метрики для времени обработки
        self.event_processing_time = Histogram(
            'socketio_event_processing_time', 
            'Event processing time in seconds',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        # Метрики для размера сообщений
        self.message_size_bytes = Histogram(
            'socketio_message_size_bytes', 
            'Size of Socket.IO messages in bytes',
            buckets=[10, 100, 1000, 5000, 10000, 50000, 100000]
        )
        
        # Метрика для игровых комнат
        self.active_games = Gauge(
            'socketio_active_games', 
            'Number of active game rooms'
        )
        
    # Переопределяем ключевые методы класса socketio.AsyncServer
    
    async def emit(self, event, data=None, room=None, skip_sid=None, namespace=None, 
                   callback=None, **kwargs):
        """Переопределенный метод emit для сбора метрик исходящих сообщений"""
        event_type = event
        
        # Увеличить счетчик исходящих событий
        self.events_total.inc({'event_type': event_type, 'direction': 'outgoing'})
        
        # Замерить размер данных
        if data is not None:
            try:
                data_size = len(json.dumps(data).encode('utf-8'))
                self.message_size_bytes.observe({'event_type': event_type, 'direction': 'outgoing'}, data_size)
            except:
                pass
        
        # Вызвать оригинальный метод emit родительского класса
        return await super().emit(event, data, room, skip_sid, namespace, callback, **kwargs)
    
    async def _trigger_event(self, event, *args, **kwargs):
        """Переопределенный метод _trigger_event для сбора метрик входящих событий"""
        event_type = event
        sid = args[0] if args else "unknown"
        
        # Обработка событий подключения/отключения
        if event == 'connect':
            logger.debug(f"Connection event for SID: {sid}")
            self.active_connections.inc({})
            self.connections_total.inc({})
        elif event == 'disconnect':
            logger.debug(f"Disconnect event for SID: {sid}")
            self.active_connections.dec({})
            self.disconnections_total.inc({})
        
        # Увеличить счетчик входящих событий
        self.events_total.inc({'event_type': event_type, 'direction': 'incoming'})
        
        # Замерить размер данных
        if len(args) > 1 and args[1] is not None:
            try:
                data_size = len(json.dumps(args[1]).encode('utf-8'))
                self.message_size_bytes.observe({'event_type': event_type, 'direction': 'incoming'}, data_size)
            except:
                pass
        
        # Измерение времени выполнения обработчика
        start_time = time.time()
        try:
            # Вызвать оригинальный метод родительского класса
            result = await super()._trigger_event(event, *args, **kwargs)
            return result
        finally:
            # Замерить время выполнения
            self.event_processing_time.observe({'event_type': event_type}, time.time() - start_time)
    
    # Добавим методы для ручного изменения счетчика игр
    def increment_games(self):
        """Увеличить счетчик активных игр"""
        self.active_games.inc({})
        
    def decrement_games(self):
        """Уменьшить счетчик активных игр"""
        self.active_games.dec({})