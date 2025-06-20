import { io, Socket as IOSocket } from 'socket.io-client';
import { InputHandler } from '../services/InputHandler';
import { Renderer } from './Renderer';
import { Socket } from '../types/Socket';
import logger, { LogLevel } from '../utils/Logger';
import { tokenService } from '../services/tokenService';
import {GameState, GameUpdateEvent, ResponseGameState} from "../types/Game";
import { EntitiesInfo } from "../types/EntitiesParams";

export class GameClient {
    private canvas: HTMLCanvasElement;
    private socket?: IOSocket;
    private inputHandler: InputHandler;
    private renderer: Renderer;
    private gameId: string | null = null;
    private playerId: string | null;
    private gameState: GameState | null = null;
    private animationFrameId: number = 0;
    private isConnected: boolean = false;
    private lastUpdateTime: number = 0;
    
    // Новые свойства для URL и пути сокета
    private socketUrl: string | undefined;
    private socketPath: string | undefined;

    // Кеш полной карты для обновлений с изменениями
    private cachedMapGrid: number[][] | null = null;

    // Колбек для уведомления о проблемах с авторизацией
    private onAuthenticationFailed?: () => void;

    // Новый колбек для уведомления о присоединении к игре
    private onGameJoined?: (success: boolean) => void;

    // Система управления кнопками
    private buttons: Array<{
        x: number;
        y: number;
        width: number;
        height: number;
        onClick: () => void;
    }> = [];
    private clickHandler?: (e: MouseEvent) => void;

    constructor(
        canvas: HTMLCanvasElement,
        entitiesInfo: EntitiesInfo,
        initialPlayerId: string | null = null
    ) {
        this.canvas = canvas;
        this.playerId = initialPlayerId;
        
        // Получаем URL и путь из переменных окружения и сохраняем как свойства экземпляра
        this.socketUrl = process.env.REACT_APP_SOCKET_URL;
        this.socketPath = process.env.REACT_APP_SOCKET_PATH;
        
        const accessToken = tokenService.getAccessToken();

        // Initialize socket connection to Python backend
        // Теперь НЕ передаем auth параметр, полагаемся на cookie
        this.socket = io(this.socketUrl, {
            transports: ['websocket'],
            path: this.socketPath ? this.socketPath : undefined
            // auth параметр удален - используем cookie
        });
        
        this.inputHandler = new InputHandler();
        this.renderer = new Renderer(canvas, entitiesInfo);
        
        // Создаем единый обработчик для кликов по canvas
        this.setupCanvasClickHandler();
        
        this.setupSocketEvents();
        
        logger.info('GameClient initialized', {
            socketUrl: this.socketUrl,
            socketPath: this.socketPath,
            hasToken: !!accessToken,
            canvasWidth: canvas.width,
            canvasHeight: canvas.height
        });
    }

    // Настройка единого обработчика кликов по canvas
    private setupCanvasClickHandler(): void {
        this.clickHandler = (e: MouseEvent) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            // Проверяем, попал ли клик в какую-то из активных кнопок
            for (const button of this.buttons) {
                if (
                    mouseX >= button.x - button.width / 2 && 
                    mouseX <= button.x + button.width / 2 && 
                    mouseY >= button.y - button.height / 2 && 
                    mouseY <= button.y + button.height / 2
                ) {
                    button.onClick();
                    break; // Выходим после первого найденного совпадения
                }
            }
        };
        
        this.canvas.addEventListener('click', this.clickHandler);
    }

    // Очистка активных кнопок
    private clearButtons(): void {
        this.buttons = [];
    }

    private setupSocketEvents(): void {
        if (!this.socket) {
            return;
        }
        
        // Connection events
        this.socket.on('connect', () => {
            logger.info('Connected to server', {
                socketUrl: this.socketUrl,
                socketPath: this.socketPath
            });
            this.isConnected = true;
            this.showMenu();
        });

        this.socket.on('disconnect', () => {
            logger.info('Disconnected from server', {
                gameId: this.gameId,
                playerId: this.playerId
            });
            this.isConnected = false;
            this.showDisconnectedMessage();
        });

        // Обработка ошибок подключения
        this.socket.on('connect_error', (error: any) => {
            logger.error('Socket connection error', {
                error: error.message,
                description: error.description,
                context: error.context
            });
            
            // Если ошибка связана с авторизацией
            if (error.message?.includes('Authentication') || error.message?.includes('Unauthorized')) {
                this.handleAuthError();
            } else {
                this.isConnected = false;
                this.showDisconnectedMessage();
            }
        });

        // Обработка ошибок авторизации от сервера
        this.socket.on('auth_error', (data: any) => {
            logger.error('Authentication error from server', data);
            this.handleAuthError();
        });

        // Game events
        this.socket.on('game_state', (gameState: GameState) => {
            logger.debug('Получено событие game_state', {
                hasGrid: !!gameState.map?.grid,
                playersCount: Object.keys(gameState.players).length,
            });
            this.processFullGameStateUpdate(gameState);
        });

        // Добавляем обработчик для game_update
        this.socket.on('game_update', (gameUpdate: GameUpdateEvent) => {
            logger.debug('Получено событие game_update', {
                hasGrid: !!gameUpdate?.map_update,
            });
            this.processGameStateUpdate(gameUpdate);
        });

        this.socket.on('player_disconnected', (data: { player_id: string }) => {
            logger.info(`Player ${data.player_id} disconnected`, {
                gameId: this.gameId,
                remainingPlayers: this.gameState ? Object.keys(this.gameState.players).filter(id => id !== data.player_id).length : 0
            });
            
            // Update UI to show player disconnect if needed
            if (this.gameState && this.gameState.players[data.player_id]) {
                // Remove player from local state until next game_update
                delete this.gameState.players[data.player_id];
            }
        });

        this.socket.on('game_over', () => {
            logger.info('Game over', {
                gameId: this.gameId,
                playerId: this.playerId,
            });
            this.showGameOver();
        });
    }

    // Обработка ошибок авторизации
    private handleAuthError(): void {
        logger.error('Socket authentication failed', {
            gameId: this.gameId,
            playerId: this.playerId
        });
        
        // Пытаемся обновить токен и переподключиться
        this.refreshTokenAndReconnect();
    }

    // Обновление токена и переподключение
    private async refreshTokenAndReconnect(): Promise<void> {
        try {
            const tokenData = await tokenService.refreshToken();
            
            if (tokenData && this.socket) {
                // Cookie уже обновлена через tokenService.saveTokens()
                // Просто переподключаемся - новая cookie будет отправлена автоматически
                this.socket.disconnect();
                this.socket.connect();
            } else {
                this.redirectToLogin();
            }
        } catch (error) {
            logger.error('Error refreshing token', { error });
            this.redirectToLogin();
        }
    }

    // Перенаправление на страницу авторизации
    private redirectToLogin(): void {
        logger.info('Redirecting to login page due to authentication failure');
        
        // Очищаем токены через сервис
        tokenService.clearTokens();
        
        // Уведомляем родительский компонент об ошибке авторизации
        // Вместо прямого перенаправления
        this.onAuthenticationFailed?.();
    }

    // Функция для обработки результата запроса состояния игры
    private handleGetGameStateResponse(response: ResponseGameState): void {
        if (response.success) {
            logger.debug('Получено состояние игры и полная карта', {
                hasFullMap: !!(response.game_state && response.game_state.map),
                hasGameState: !!response.game_state
            });
            
            // Сохраняем полную карту в кеш
            if (response.game_state.map && response.game_state.map.grid) {
                logger.debug('Получена полная карта', {
                    width: response.game_state.map.width,
                    height: response.game_state.map.height
                });
                this.cachedMapGrid = JSON.parse(JSON.stringify(response.game_state.map.grid));
            } else {
                logger.error('Не удалось получить карту из запроса состояния', {
                    message: response.message,
                    gameId: this.gameId,
                    playerId: this.playerId,
                    responseData: response
                });
            }
            
            // Сохраняем состояние игры
            this.gameState = response.game_state;
        } else {
            logger.error('Ошибка получения состояния игры', {
                message: response.message,
                gameId: this.gameId,
                playerId: this.playerId,
                responseData: response
            });
        }
    }

    // Запрос полного состояния игры
    private requestGameState(): void {
        logger.debug('Запрашиваем состояние игры', {
            gameId: this.gameId,
            playerId: this.playerId
        });
        this.socket?.emit('get_game_state', {
            game_id: this.gameId
        }, this.handleGetGameStateResponse.bind(this));

    }

    // Обработка обновлений игры
    private processFullGameStateUpdate(gameState: GameState): void {
        this.lastUpdateTime = performance.now();

        // Сохраняем обновленное состояние
        this.gameState = gameState;

        // Обновляем информацию в header
        this.updateGameInfo();
    }

    // Обработка обновлений игры частичными изменениями
    private processGameStateUpdate(gameUpdate: GameUpdateEvent): void {
        this.lastUpdateTime = performance.now();
        
        // Применяем изменения к кешированной карте
        if (gameUpdate?.map_update && this.cachedMapGrid) {
            const changes = gameUpdate.map_update;
            
            // Применяем изменения к кешированной карте
            for (const cell of changes) {
                // Проверяем корректность индексов
                if (cell.y >= 0 && this.cachedMapGrid.length > 0 && 
                    cell.y < this.cachedMapGrid.length &&
                    cell.x >= 0 && cell.x < this.cachedMapGrid[0].length) {
                    this.cachedMapGrid[cell.y][cell.x] = cell.type;
                } else {
                    logger.warn('Неверные координаты ячейки', {
                        x: cell.x,
                        y: cell.y,
                        type: cell.type,
                        mapWidth: this.cachedMapGrid[0]?.length,
                        mapHeight: this.cachedMapGrid.length
                    });
                }
            }

        } else if (gameUpdate?.map_update && !this.cachedMapGrid) {
            // Если нет кешированной карты, но есть изменения, запрашиваем полное состояние
            logger.warn('Получены изменения, но нет кешированной карты', {
                changesCount: gameUpdate?.map_update.length,
                gameId: this.gameId,
                playerId: this.playerId
            });
            this.requestGameState();
            return;
        }
        
        // Сохраняем обновленное состояние
        if (this.gameState == null){
            this.requestGameState()
        }else{
            this.gameState.map.grid = this.cachedMapGrid;
        }

        // Обновляем информацию в header
        this.updateGameInfo();
    }

    public start(): void {
        if (!this.socket) {
            logger.error('Cannot start game: socket not available');
            return;
        }
        
        logger.info('Запуск игрового клиента', {
            canvasWidth: this.canvas.width,
            canvasHeight: this.canvas.height
        });
        this.showMenu();
        this.startGameLoop();
    }

    private startGameLoop(): void {
        const gameLoop = () => {
            // Отправляем входные данные на сервер, если мы в игре
            if (this.gameId && this.playerId) {
                this.sendInputs();
            }
            
            this.update();
            this.animationFrameId = requestAnimationFrame(gameLoop);
        };
        this.animationFrameId = requestAnimationFrame(gameLoop);
    }

    private update(): void {
        // Проверяем время последнего обновления
        const currentTime = performance.now();
        const timeSinceLastUpdate = currentTime - this.lastUpdateTime;
        
        // Если прошло больше 3 секунд без обновлений и мы в игре, запрашиваем состояние
        if (this.gameId && this.playerId && this.lastUpdateTime > 0 && timeSinceLastUpdate > 3000) {
            logger.warn('Давно не было обновлений, запрашиваем состояние игры', {
                timeSinceLastUpdate: Math.round(timeSinceLastUpdate),
                gameId: this.gameId,
                playerId: this.playerId
            });
            // Запрашиваем новое состояние игры
            this.requestGameState();
            this.lastUpdateTime = currentTime; // Обновляем время, чтобы не спамить запросами
        }

        // Если у нас есть состояние игры и ID игрока, рендерим
        if (this.gameState && this.playerId) {
            // Проверяем, есть ли данные карты
            if (!this.gameState.map || !this.gameState.map.grid) {
                logger.warn('Нет данных карты для рендеринга', {
                    hasMap: !!this.gameState.map,
                    hasGrid: !!(this.gameState.map && this.gameState.map.grid),
                    hasCachedGrid: !!this.cachedMapGrid
                });
                
                // Если у нас есть кешированная карта, используем её
                if (this.cachedMapGrid) {
                    if (!this.gameState.map) {
                        this.gameState.map = {
                            width: this.cachedMapGrid[0].length,
                            height: this.cachedMapGrid.length,
                            grid: this.cachedMapGrid
                        };
                    } else {
                        this.gameState.map.grid = this.cachedMapGrid;
                    }
                    logger.debug('Используем кешированную карту для рендеринга', {
                        width: this.cachedMapGrid[0].length,
                        height: this.cachedMapGrid.length
                    });
                } else {
                    // Запрашиваем полное состояние игры, если нет данных
                    this.requestGameState();
                    return;
                }
            }
            
            // Передаем состояние игры и ID текущего игрока в рендерер
            this.renderer.render(this.gameState, this.playerId);
        } else {
            // Если есть gameId, но нет gameState, запрашиваем состояние
            if (this.gameId && this.playerId && !this.gameState) {
                this.requestGameState();
            }
        }
    }

    private showMenu(): void {
        // Очищаем предыдущие кнопки
        this.clearButtons();
        
        // Clear canvas
        const ctx = this.canvas.getContext('2d')!;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Show menu
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        ctx.fillStyle = 'white';
        ctx.font = '40px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('BOMBERMAN ONLINE', this.canvas.width / 2, this.canvas.height / 2 - 80);
        
        if (this.isConnected) {
            // Join game button (no create game here)
            this.drawButton(ctx, 'JOIN GAME', this.canvas.width / 2, this.canvas.height / 2, 200, 50, () => {
                this.promptGameId();
            });
        } else {
            ctx.fillStyle = 'red';
            ctx.font = '20px Arial';
            ctx.fillText('Not connected to server', this.canvas.width / 2, this.canvas.height / 2 + 20);
        }
    }

    private drawButton(
        ctx: CanvasRenderingContext2D, 
        text: string, 
        x: number, 
        y: number, 
        width: number, 
        height: number, 
        onClick: () => void
    ): void {
        // Draw button
        ctx.fillStyle = '#555';
        ctx.fillRect(x - width / 2, y - height / 2, width, height);
        
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.strokeRect(x - width / 2, y - height / 2, width, height);
        
        // Draw text
        ctx.fillStyle = 'white';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, x, y);
        
        // Добавляем кнопку в массив активных кнопок
        this.buttons.push({ x, y, width, height, onClick });
    }

    private promptGameId(): void {
        const gameId = prompt('Enter Game ID:');
        if (gameId) {
            logger.info('Попытка присоединиться к игре', {gameId});
            this.joinGame(gameId, this.playerId || '');
        } else {
            this.showMenu();
        }
    }

    public joinGame(gameId: string, playerId: string): void {
        if (!this.socket) {
            logger.error('Socket is not initialized.');
            return;
        }

        if (!gameId) {
            logger.error('Cannot join game: gameId is not provided.');
            return;
        }

        if (!playerId) {
            logger.error('Cannot join game: playerId is not provided.');
            return;
        }

        logger.info(`Attempting to join game ${gameId} as player ${playerId}`);
        this.socket.emit('join_game', { game_id: gameId, player_id: playerId }, (response: any) => {
            if (response.success) {
                this.gameId = gameId;
                this.playerId = playerId;
                
                // Очищаем кнопки меню, так как игра начинается
                this.clearButtons();
                
                // Сбрасываем кэш карты при присоединении к новой игре
                this.cachedMapGrid = null;
                
                logger.info('Присоединение к игре успешно', {
                    gameId: this.gameId,
                    playerId: this.playerId
                });
                
                // Уведомляем родительский компонент, что игра успешно присоединена
                this.onGameJoined?.(true);
                
                // Отправляем Game ID в header через DOM event
                this.updateGameId(gameId);
                
                // Получаем начальное состояние игры
                if (response.game_state && response.game_state.map && response.game_state.map.grid_data) {
                    logger.debug('Начальное состояние получено с картой', {
                        width: response.game_state.map.grid_data[0].length,
                        height: response.game_state.map.grid_data.length
                    });
                    
                    // Сохраняем состояние и кэшируем карту
                    this.gameState = response.game_state;
                    this.cachedMapGrid = response.game_state.map.grid_data;
                    
                    // Обновляем UI в header
                    this.updateGameInfo();
                } else {
                    logger.warn('Получено неполное начальное состояние игры', {
                        hasGameState: !!response.game_state,
                        hasMap: !!(response.game_state && response.game_state.map),
                        hasGrid: !!(response.game_state && response.game_state.map && response.game_state.map.grid_data)
                    });
                    
                    // Явно запрашиваем полное состояние игры
                    this.requestGameState();
                }
            } else {
                logger.error('Не удалось присоединиться к игре', {
                    gameId,
                    playerId,
                    message: response.message
                });
                alert(`Failed to join game: ${response.message}`);
                // No longer show menu here, as joinGame is called from GameCanvas
                // this.showMenu(); // Removed
            }
        });
    }

    // Добавляем методы для обновления информации в header
    private updateGameId(gameId: string): void {
        window.dispatchEvent(new CustomEvent('gameIdUpdate', { detail: gameId }));
    }

    private updateGameInfo(): void {
        if (this.gameState) {
            window.dispatchEvent(new CustomEvent('levelUpdate', { detail: this.gameState.level }));
        }
    }

    private showDisconnectedMessage(): void {
        const ctx = this.canvas.getContext('2d')!;
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        ctx.fillStyle = 'red';
        ctx.font = '30px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('DISCONNECTED FROM SERVER', this.canvas.width / 2, this.canvas.height / 2 - 20);
        
        ctx.fillStyle = 'white';
        ctx.font = '20px Arial';
        ctx.fillText('Please refresh the page to reconnect', this.canvas.width / 2, this.canvas.height / 2 + 20);
    }

    private showGameOver(): void {
        // Очищаем предыдущие кнопки
        this.clearButtons();
        
        const ctx = this.canvas.getContext('2d')!;
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        ctx.fillStyle = 'white';
        ctx.font = '40px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', this.canvas.width / 2, this.canvas.height / 2 - 20);
        
        // if (this.gameState) {
        //     ctx.font = '20px Arial';
        //     ctx.fillText(`Final Score: ${this.gameState.score}`, this.canvas.width / 2, this.canvas.height / 2 + 20);
        // }
        
        // Back to menu button
        this.drawButton(ctx, 'BACK TO MENU', this.canvas.width / 2, this.canvas.height / 2 + 70, 200, 50, () => {
            logger.info('Возврат в главное меню после окончания игры', {
                gameId: this.gameId,
            });
            this.gameId = null;
            this.playerId = null;
            this.gameState = null;
            
            // Очищаем информацию в header
            this.updateGameId('');
            window.dispatchEvent(new CustomEvent('levelUpdate', { detail: 1 }));
            
            this.showMenu();
        });
    }

    public stop(): void {
        logger.info('Остановка игрового клиента');
        cancelAnimationFrame(this.animationFrameId);
        
        // Очищаем обработчик событий
        if (this.clickHandler) {
            this.canvas.removeEventListener('click', this.clickHandler);
        }
        
        if (this.socket) {
            this.socket.disconnect();
        }
    }

    // Метод для отправки входных данных на сервер
    private sendInputs(): void {
        if (!this.socket || !this.gameId) {
            return;
        }
        
        const inputs = this.inputHandler.getInput();
        
        // Отправляем ввод игрока в соответствии с форматом, ожидаемым сервером
        this.socket?.emit('input', {
            game_id: this.gameId,
            inputs: {
                up: inputs.up,
                down: inputs.down,
                left: inputs.left,
                right: inputs.right
            }
        });
        
        // Отправляем команду установки бомбы отдельно
        if (inputs.bomb) {
            this.socket?.emit('place_bomb', {
                game_id: this.gameId
            });
            
            // Сбрасываем ввод бомбы, чтобы предотвратить многократные установки от одного нажатия
            this.inputHandler.resetBombInput();
        }
    }

    public setAuthenticationFailedHandler(handler: () => void): void {
        this.onAuthenticationFailed = handler;
    }
    
    // Новый метод для установки обработчика успешного присоединения к игре
    public setGameJoinedHandler(handler: (success: boolean) => void): void {
        this.onGameJoined = handler;
    }
} 