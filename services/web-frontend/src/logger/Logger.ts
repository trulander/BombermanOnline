import log from 'loglevel';
import { throttle } from 'lodash';

export enum LogLevel {
    TRACE = 'trace',
    DEBUG = 'debug',
    INFO = 'info',
    WARN = 'warn',
    ERROR = 'error'
}

// Обратная карта для получения LogLevel из строки
const LogLevelMap: Record<string, keyof typeof log.levels> = {
    'trace': 'TRACE',
    'debug': 'DEBUG',
    'info': 'INFO',
    'warn': 'WARN',
    'error': 'ERROR'
};

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
    service: string;
    sessionId: string;
    data?: any;
}

// Расширяем интерфейс Window для TypeScript
declare global {
    interface Window {
        NODE_ENV: string;
        LOGS_ENDPOINT: string;
        SERVICE_NAME: string;
    }
}

// Генерация простого UUID для сессии
function generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

class Logger {
    private sessionId: string;
    private endpoint: string;
    private serviceName: string;
    private batchSize: number;
    private flushInterval: number;
    private logQueue: LogEntry[] = [];
    private flushTimer: number | null = null;
    private nodeEnv: string;
    
    // Хэш-карта для хранения троттлированных функций логирования
    private throttledLogs: Map<string, (message: any, data?: any) => void> = new Map();
    
    constructor() {
        this.sessionId = generateUUID();
        // Используем глобально заданные константы
        this.endpoint = window.LOGS_ENDPOINT || '/logs';
        this.serviceName = window.SERVICE_NAME || 'web-frontend';
        this.nodeEnv = window.NODE_ENV || 'development';
        this.batchSize = 10; // Количество логов перед отправкой
        this.flushInterval = 5000; // Отправка каждые 5 секунд
        
        // Настраиваем loglevel в зависимости от окружения
        const defaultLevel = this.nodeEnv === 'production' 
            ? log.levels.INFO 
            : log.levels.DEBUG;
        log.setLevel(defaultLevel);
        
        // Перехватываем консоль
        this.interceptConsole();
        
        // Запускаем таймер для периодической отправки логов
        this.startFlushTimer();
        
        // Перехватываем необработанные ошибки
        window.addEventListener('error', (event) => {
            this.error('Unhandled error', { 
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error?.stack || event.error?.toString()
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.error('Unhandled promise rejection', {
                reason: event.reason?.stack || event.reason?.toString()
            });
        });
        
        this.info('Logger initialized', { 
            environment: this.nodeEnv,
            endpoint: this.endpoint 
        });
    }
    
    // Получение троттлированной функции логирования по ключу
    private getThrottledLog(key: string, level: LogLevel, interval: number = 1000): (message: any, data?: any) => void {
        const mapKey = `${level}:${key}:${interval}`;
        if (!this.throttledLogs.has(mapKey)) {
            this.throttledLogs.set(
                mapKey, 
                throttle((message: any, data?: any) => {
                    switch(level) {
                        case LogLevel.TRACE:
                            this.trace(message, data);
                            break;
                        case LogLevel.DEBUG:
                            this.debug(message, data);
                            break;
                        case LogLevel.INFO:
                            this.info(message, data);
                            break;
                        case LogLevel.WARN:
                            this.warn(message, data);
                            break;
                        case LogLevel.ERROR:
                            this.error(message, data);
                            break;
                    }
                }, interval)
            );
        }
        return this.throttledLogs.get(mapKey)!;
    }
    
    /**
     * Логирование с ограничением частоты
     * @param key - Уникальный ключ для группы логов
     * @param level - Уровень логирования
     * @param message - Сообщение лога
     * @param data - Дополнительные данные
     * @param interval - Интервал троттлинга в мс, по умолчанию 1000 (1 секунда)
     */
    public throttled(key: string, level: LogLevel, message: any, data?: any, interval: number = 1000): void {
        this.getThrottledLog(key, level, interval)(message, data);
    }
    
    private interceptConsole() {
        const originalConsole = {
            log: console.log,
            info: console.info,
            warn: console.warn,
            error: console.error,
            debug: console.debug
        };
        
        console.log = (...args: any[]) => {
            originalConsole.log.apply(console, args);
            this.info(args[0], args.slice(1));
        };
        
        console.info = (...args: any[]) => {
            originalConsole.info.apply(console, args);
            this.info(args[0], args.slice(1));
        };
        
        console.warn = (...args: any[]) => {
            originalConsole.warn.apply(console, args);
            this.warn(args[0], args.slice(1));
        };
        
        console.error = (...args: any[]) => {
            originalConsole.error.apply(console, args);
            this.error(args[0], args.slice(1));
        };
        
        console.debug = (...args: any[]) => {
            originalConsole.debug.apply(console, args);
            this.debug(args[0], args.slice(1));
        };
    }
    
    private createLogEntry(level: string, message: any, data?: any): LogEntry {
        return {
            timestamp: new Date().toISOString(),
            level,
            message: String(message),
            service: this.serviceName,
            sessionId: this.sessionId,
            data
        };
    }
    
    private addToQueue(entry: LogEntry) {
        this.logQueue.push(entry);
        
        // Если очередь достигла определенного размера, отправляем логи
        if (this.logQueue.length >= this.batchSize) {
            this.flush();
        }
    }
    
    private startFlushTimer() {
        this.flushTimer = window.setInterval(() => {
            if (this.logQueue.length > 0) {
                this.flush();
            }
        }, this.flushInterval);
    }
    
    private async flush() {
        if (this.logQueue.length === 0) return;
        
        const logsToSend = [...this.logQueue];
        this.logQueue = [];
        
        try {
            // Отправляем логи пакетом вместо отправки каждого лога отдельно
            await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    logs: logsToSend.map(entry => (entry))
                })
            });
        } catch (error) {
            // Если произошла ошибка при отправке, возвращаем логи в очередь
            console.error('Failed to send logs:', error);
            this.logQueue = [...logsToSend, ...this.logQueue];
        }
    }
    
    public setLevel(level: LogLevel) {
        if (typeof level === 'string') {
            const logLevelKey = LogLevelMap[level.toLowerCase()];
            if (logLevelKey) {
                log.setLevel(log.levels[logLevelKey]);
            }
        } else {
            // Если передан элемент перечисления
            const logLevelValue = LogLevel[level];
            const logLevelKey = LogLevelMap[logLevelValue];
            if (logLevelKey) {
                log.setLevel(log.levels[logLevelKey]);
            }
        }
    }
    
    public trace(message: any, data?: any) {
        log.trace(message);
        this.addToQueue(this.createLogEntry('TRACE', message, data));
    }
    
    public debug(message: any, data?: any) {
        log.debug(message);
        this.addToQueue(this.createLogEntry('DEBUG', message, data));
    }
    
    public info(message: any, data?: any) {
        log.info(message);
        this.addToQueue(this.createLogEntry('INFO', message, data));
    }
    
    public warn(message: any, data?: any) {
        log.warn(message);
        this.addToQueue(this.createLogEntry('WANR', message, data));
    }
    
    public error(message: any, data?: any) {
        log.error(message);
        this.addToQueue(this.createLogEntry('ERROR', message, data));
    }
    
    // Вызывается при закрытии страницы для отправки оставшихся логов
    public async destroy() {
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
            this.flushTimer = null;
        }
        
        if (this.logQueue.length > 0) {
            await this.flush();
        }
    }
}

// Создаем синглтон экземпляр логгера
const logger = new Logger();

// Добавляем обработчик для отправки оставшихся логов перед закрытием страницы
window.addEventListener('beforeunload', () => {
    logger.destroy();
});

export default logger; 