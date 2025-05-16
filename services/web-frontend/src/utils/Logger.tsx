import log from 'loglevel';


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

// Карта значений числовых уровней для сравнения
const LogLevelValue: Record<LogLevel, number> = {
    [LogLevel.TRACE]: 0,
    [LogLevel.DEBUG]: 1,
    [LogLevel.INFO]: 2,
    [LogLevel.WARN]: 3,
    [LogLevel.ERROR]: 4
};

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
    service: string;
    sessionId: string;
    data?: any;
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
    private currentLogLevel: LogLevel;
    
    constructor() {
        this.sessionId = generateUUID();
        this.endpoint = process.env.REACT_APP_LOGS_ENDPOINT;
        this.serviceName = process.env.REACT_APP_SERVICE_NAME;
        this.nodeEnv = process.env.NODE_ENV;
        
        // Получаем размер пакета логов из переменной окружения или используем значение по умолчанию
        const batchSizeStr = process.env.REACT_APP_LOGS_BATCH_SIZE || '10';
        this.batchSize = parseInt(batchSizeStr, 10);
        if (isNaN(this.batchSize) || this.batchSize < 1) {
            this.batchSize = 10; // Значение по умолчанию, если парсинг не удался
        }
        
        this.flushInterval = 5000; // Отправка каждые 5 секунд
        
        // Настраиваем loglevel в зависимости от окружения
        this.currentLogLevel = this.nodeEnv === 'production'
            ? LogLevel.INFO 
            : LogLevel.DEBUG;
            
        // Устанавливаем уровень для библиотеки loglevel
        const logLevelKey = LogLevelMap[this.currentLogLevel];
        if (logLevelKey) {
            log.setLevel(log.levels[logLevelKey]);
        }
        
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
                error: event.error?.stack || event.error?.toString(),
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.error('Unhandled promise rejection', {
                reason: event.reason?.stack || event.reason?.toString(),
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href
            });
        });
        
        this.info('Logger initialized', { 
            environment: this.nodeEnv,
            endpoint: this.endpoint,
            batchSize: this.batchSize,
            logLevel: this.currentLogLevel
        });
    }
    
    /**
     * Проверяет, должен ли лог с указанным уровнем быть обработан
     */
    private shouldLog(level: LogLevel): boolean {
        return LogLevelValue[level] >= LogLevelValue[this.currentLogLevel];
    }
    
    /**
     * Логирование без ограничения частоты (замена throttled)
     * @param key - Уникальный ключ для группы логов (не используется, оставлен для совместимости)
     * @param level - Уровень логирования
     * @param message - Сообщение лога
     * @param data - Дополнительные данные
     */
    public log(key: string, level: LogLevel, message: any, data?: any): void {
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
    }
    
    /**
     * Оставляем метод throttled для обратной совместимости,
     * но внутри просто вызываем log без ограничения частоты
     */
    public throttled(key: string, level: LogLevel, message: any, data?: any, interval: number = 1000): void {
        this.log(key, level, message, data);
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
            // Используем индексную сигнатуру для допустимости дополнительных свойств
            const errorDetails: { 
                timestamp: string; 
                args: any[]; 
                [key: string]: any; 
            } = {
                timestamp: new Date().toISOString(),
                args: args.slice(1)
            };
            
            // Проверяем, есть ли в аргументах объект ошибки
            const errorObjects = args.filter(arg => arg instanceof Error);
            if (errorObjects.length > 0) {
                // Добавляем информацию из ошибок
                errorDetails.errors = errorObjects.map(error => ({
                    message: error.message,
                    name: error.name,
                    stack: error.stack
                }));
            }
            
            this.error(args[0], errorDetails);
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
        this.currentLogLevel = level;
        
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
    
    /**
     * Возвращает текущий уровень логирования
     */
    public getCurrentLevel(): LogLevel {
        return this.currentLogLevel;
    }
    
    public trace(message: any, data?: any) {
        log.trace(message);
        if (this.shouldLog(LogLevel.TRACE)) {
            this.addToQueue(this.createLogEntry('TRACE', message, data));
        }
    }
    
    public debug(message: any, data?: any) {
        log.debug(message);
        if (this.shouldLog(LogLevel.DEBUG)) {
            this.addToQueue(this.createLogEntry('DEBUG', message, data));
        }
    }
    
    public info(message: any, data?: any) {
        log.info(message);
        if (this.shouldLog(LogLevel.INFO)) {
            this.addToQueue(this.createLogEntry('INFO', message, data));
        }
    }
    
    public warn(message: any, data?: any) {
        log.warn(message);
        if (this.shouldLog(LogLevel.WARN)) {
            this.addToQueue(this.createLogEntry('WARN', message, data));
        }
    }
    
    public error(message: any, data?: any) {
        log.error(message);
        if (this.shouldLog(LogLevel.ERROR)) {
            const enhancedData = {
                ...data,
                timestamp: new Date().toISOString(),
                url: window.location.href
            };
            this.addToQueue(this.createLogEntry('ERROR', message, enhancedData));
        }
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