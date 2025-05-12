import { GameClient } from './client/GameClient';
import logger, { LogLevel } from './logger/Logger';

// Запуск приложения после загрузки DOM
window.addEventListener('load', () => {
    logger.info('Приложение запущено', {
        environment: window.NODE_ENV,
        endpoint: window.LOGS_ENDPOINT,
        service: window.SERVICE_NAME,
        socketUrl: window.SOCKET_URL,
        socketPath: window.SOCKET_PATH,
        LOGS_BATCH_SIZE: window.LOGS_BATCH_SIZE,
        logLevel: logger.getCurrentLevel()
    });

    try {
        const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
        if (!canvas) {
            throw new Error('Элемент canvas с id="gameCanvas" не найден');
        }
        
        const gameClient = new GameClient(canvas);
        gameClient.start();
        
        logger.info('Игровой клиент инициализирован');
    } catch (error) {
        logger.error('Ошибка при инициализации игры', { error });
    }
});
