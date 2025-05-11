import { GameClient } from './client/GameClient';
import logger from './logger/Logger';

// // Расширяем интерфейс Window для TypeScript
// declare global {
//     interface Window {
//         NODE_ENV: string;
//         LOGS_ENDPOINT: string;
//         SERVICE_NAME: string;
//         SOCKET_URL: string;
//         SOCKET_PATH: string;
//     }
// }
//
// // Установка глобальных переменных для Logger
// window.NODE_ENV = window.NODE_ENV || 'development';
// window.LOGS_ENDPOINT = window.LOGS_ENDPOINT || '/logs';
// window.SERVICE_NAME = window.SERVICE_NAME || 'web-frontend';
// window.SOCKET_URL = window.SOCKET_URL || 'http://localhost';
// window.SOCKET_PATH = window.SOCKET_PATH || '/socket.io';

// Запуск приложения после загрузки DOM
window.addEventListener('load', () => {
    logger.info('Приложение запущено', {
        environment: window.NODE_ENV,
        endpoint: window.LOGS_ENDPOINT,
        service: window.SERVICE_NAME,
        socketUrl: window.SOCKET_URL,
        socketPath: window.SOCKET_PATH,
    });

    try {
        const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
        if (!canvas) {
            throw new Error('Элемент canvas с id="game" не найден');
        }
        
        const gameClient = new GameClient(canvas);
        gameClient.start();
        
        logger.info('Игровой клиент инициализирован');
    } catch (error) {
        logger.error('Ошибка при инициализации игры', { error });
    }
});
