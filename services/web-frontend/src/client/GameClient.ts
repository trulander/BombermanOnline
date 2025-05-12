import { io } from 'socket.io-client';
import { InputHandler } from '../input/InputHandler';
import { Renderer } from './Renderer';
import { GameState } from '../types/GameState';
import { Socket } from '../types/Socket';
import logger, { LogLevel } from '../logger/Logger';

// Расширяем интерфейс Window для переменных окружения
declare global {
    interface Window {
        SOCKET_URL: string;
        SOCKET_PATH: string;
    }
}

export class GameClient {
    private canvas: HTMLCanvasElement;
    private socket: Socket;
    private inputHandler: InputHandler;
    private renderer: Renderer;
    private gameId: string | null = null;
    private playerId: string | null = null;
    private gameState: GameState | null = null;
    private animationFrameId: number = 0;
    private isConnected: boolean = false;
    private lastUpdateTime: number = 0;
    
    // Кеш полной карты для обновлений с изменениями
    private cachedMapGrid: number[][] | null = null;

    constructor(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        
        // Получаем URL и путь из переменных окружения
        const socketUrl = window.SOCKET_URL || 'http://localhost';
        const socketPath = window.SOCKET_PATH || 'socket.io';
        
        // Initialize socket connection to Python backend
        this.socket = io(socketUrl, {
            transports: ['websocket'],
            path: socketPath ? socketPath : undefined
        });
        
        this.inputHandler = new InputHandler();
        this.renderer = new Renderer(canvas);
        
        this.setupSocketEvents();
    }

    private setupSocketEvents(): void {
        // Connection events
        this.socket.on('connect', () => {
            logger.info('Connected to server', {
                socketUrl: window.SOCKET_URL,
                socketPath: window.SOCKET_PATH
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

        // Game events
        this.socket.on('game_state', (gameState: GameState) => {
            logger.debug('Получено событие game_state', {
                hasGrid: !!gameState.map?.grid,
                playersCount: Object.keys(gameState.players).length,
                mapChangesCount: gameState.map?.changedCells?.length || 0
            });
            this.processGameStateUpdate(gameState);
        });

        // Добавляем обработчик для game_update, так как сервер использует это событие в game_loop
        this.socket.on('game_update', (gameState: GameState) => {
            logger.debug('Получено событие game_update', {
                hasGrid: !!gameState.map?.grid,
                playersCount: Object.keys(gameState.players).length,
                mapChangesCount: gameState.map?.changedCells?.length || 0
            });
            this.processGameStateUpdate(gameState);
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
                score: this.gameState?.score || 0
            });
            this.showGameOver();
        });
    }

    // Функция для обработки результата запроса состояния игры
    private handleGetGameStateResponse(response: any): void {
        if (response.success) {
            logger.debug('Получено состояние игры и полная карта', {
                hasFullMap: !!(response.full_map && response.full_map.grid),
                hasGameState: !!response.game_state
            });
            
            // Сохраняем полную карту в кеш
            if (response.full_map && response.full_map.grid) {
                logger.debug('Получена полная карта', {
                    width: response.full_map.grid[0]?.length,
                    height: response.full_map.grid.length
                });
                this.cachedMapGrid = JSON.parse(JSON.stringify(response.full_map.grid));
            }
            
            // Сохраняем состояние игры
            this.gameState = response.game_state;
            
            // Убеждаемся, что у состояния игры есть полная карта из кеша
            if (this.gameState && this.gameState.map && this.cachedMapGrid) {
                this.gameState.map.grid = this.cachedMapGrid;
            }
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
        if (this.gameId && this.playerId) {
            logger.debug('Запрашиваем состояние игры', {
                gameId: this.gameId,
                playerId: this.playerId
            });
            this.socket.emit('get_game_state', { 
                game_id: this.gameId
            }, this.handleGetGameStateResponse.bind(this));
        } else {
            logger.warn('Невозможно запросить состояние игры', {
                gameId: this.gameId,
                playerId: this.playerId,
                isConnected: this.isConnected
            });
        }
    }

    // Обработка обновлений игры
    private processGameStateUpdate(gameState: GameState): void {
        this.lastUpdateTime = performance.now();
        
        // Логирование информации об обновлении
        const changesCount = gameState.map?.changedCells?.length || 0;
        if (changesCount > 0) {
            logger.debug('Получено обновление игры с изменениями', {
                changesCount,
                playersCount: Object.keys(gameState.players).length,
                bombsCount: gameState.bombs?.length || 0,
                enemiesCount: gameState.enemies?.length || 0
            });
        }
        
        // Применяем изменения к кешированной карте
        if (gameState.map?.changedCells && this.cachedMapGrid) {
            const changes = gameState.map.changedCells;
            
            if (changes.length > 0) {
                logger.debug('Применяем изменения к кешированной карте', {
                    changesCount: changes.length
                });
            }
            
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
            
            // Добавляем полную карту к игровому состоянию
            gameState.map.grid = this.cachedMapGrid;
        } else if (gameState.map?.changedCells && !this.cachedMapGrid) {
            // Если нет кешированной карты, но есть изменения, запрашиваем полное состояние
            logger.warn('Получены изменения, но нет кешированной карты', {
                changesCount: gameState.map.changedCells.length,
                gameId: this.gameId,
                playerId: this.playerId
            });
            this.requestGameState();
            return;
        }
        
        // Сохраняем обновленное состояние
        this.gameState = gameState;
    }

    public start(): void {
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
            requestAnimationFrame(gameLoop);
        };
        requestAnimationFrame(gameLoop);
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
                            cellSize: 40, // Значение по умолчанию, если не указано
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
            // Если у нас нет состояния игры или ID игрока, запрашиваем их
            if (!this.playerId) {
                logger.debug('Нет ID игрока для рендеринга');
            }
            if (!this.gameState) {
                logger.debug('Нет состояния игры для рендеринга');
                if (this.gameId && this.playerId) {
                    this.requestGameState();
                }
            }
        }
    }

    private showMenu(): void {
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
            // Create game button
            this.drawButton(ctx, 'CREATE GAME', this.canvas.width / 2, this.canvas.height / 2, 200, 50, () => {
                this.createGame();
            });
            
            // Join game button
            this.drawButton(ctx, 'JOIN GAME', this.canvas.width / 2, this.canvas.height / 2 + 70, 200, 50, () => {
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
        
        // Add click handler
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            if (
                mouseX >= x - width / 2 && 
                mouseX <= x + width / 2 && 
                mouseY >= y - height / 2 && 
                mouseY <= y + height / 2
            ) {
                onClick();
            }
        }, { once: true });
    }

    private createGame(): void {
        logger.info('Создание новой игры');
        this.socket.emit('create_game', {}, (response: { game_id: string }) => {
            this.gameId = response.game_id;
            logger.info('Игра успешно создана', {gameId: this.gameId});
            this.joinGame(this.gameId);
        });
    }

    private promptGameId(): void {
        const gameId = prompt('Enter Game ID:');
        if (gameId) {
            logger.info('Попытка присоединиться к игре', {gameId});
            this.joinGame(gameId);
        } else {
            this.showMenu();
        }
    }

    private joinGame(gameId: string): void {
        this.socket.emit('join_game', { game_id: gameId }, (response: any) => {
            if (response.success) {
                this.gameId = gameId;
                this.playerId = response.player_id;
                
                // Сбрасываем кэш карты при присоединении к новой игре
                this.cachedMapGrid = null;
                
                logger.info('Присоединение к игре успешно', {
                    gameId: this.gameId,
                    playerId: this.playerId
                });
                
                // Получаем начальное состояние игры
                if (response.game_state && response.game_state.map && response.game_state.map.grid) {
                    logger.debug('Начальное состояние получено с картой', {
                        width: response.game_state.map.grid[0].length,
                        height: response.game_state.map.grid.length
                    });
                    
                    // Сохраняем состояние и кэшируем карту
                    this.gameState = response.game_state;
                    this.cachedMapGrid = response.game_state.map.grid;
                } else {
                    logger.warn('Получено неполное начальное состояние игры', {
                        hasGameState: !!response.game_state,
                        hasMap: !!(response.game_state && response.game_state.map),
                        hasGrid: !!(response.game_state && response.game_state.map && response.game_state.map.grid)
                    });
                    
                    // Явно запрашиваем полное состояние игры
                    this.socket.emit('get_game_state', { 
                        game_id: gameId,
                        player_id: response.player_id 
                    }, (stateResponse: any) => {
                        logger.debug('Получен ответ на запрос состояния', {
                            success: stateResponse.success
                        });
                        if (stateResponse.success) {
                            this.gameState = stateResponse.game_state;
                            
                            // Сохраняем полную карту
                            if (this.gameState && this.gameState.map && this.gameState.map.grid) {
                                logger.debug('Карта из запроса состояния получена', {
                                    width: this.gameState.map.grid[0].length,
                                    height: this.gameState.map.grid.length
                                });
                                this.cachedMapGrid = this.gameState.map.grid;
                            } else {
                                logger.error('Не удалось получить карту из запроса состояния', {
                                    hasGameState: !!this.gameState,
                                    hasMap: !!(this.gameState && this.gameState.map)
                                });
                            }
                        }
                    });
                }
                
                // Show game ID on screen for others to join
                const gameIdElement = document.getElementById('gameId');
                if (gameIdElement) {
                    gameIdElement.textContent = `Game ID: ${gameId}`;
                    gameIdElement.style.display = 'block';
                }
            } else {
                logger.error('Не удалось присоединиться к игре', {
                    gameId,
                    message: response.message
                });
                alert(`Failed to join game: ${response.message}`);
                this.showMenu();
            }
        });
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
        const ctx = this.canvas.getContext('2d')!;
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        ctx.fillStyle = 'white';
        ctx.font = '40px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', this.canvas.width / 2, this.canvas.height / 2 - 20);
        
        if (this.gameState) {
            ctx.font = '20px Arial';
            ctx.fillText(`Final Score: ${this.gameState.score}`, this.canvas.width / 2, this.canvas.height / 2 + 20);
        }
        
        // Back to menu button
        this.drawButton(ctx, 'BACK TO MENU', this.canvas.width / 2, this.canvas.height / 2 + 70, 200, 50, () => {
            logger.info('Возврат в главное меню после окончания игры', {
                gameId: this.gameId,
                score: this.gameState?.score || 0
            });
            this.gameId = null;
            this.playerId = null;
            this.gameState = null;
            this.showMenu();
        });
    }

    public stop(): void {
        logger.info('Остановка игрового клиента');
        cancelAnimationFrame(this.animationFrameId);
        this.socket.disconnect();
    }

    // Добавляем метод для отправки входных данных на сервер
    private sendInputs(): void {
        const inputs = this.inputHandler.getInput();
        
        // Отправляем ввод игрока в соответствии с форматом, ожидаемым сервером
        this.socket.emit('input', {
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
            this.socket.emit('place_bomb', {
                game_id: this.gameId
            });
            
            // Сбрасываем ввод бомбы, чтобы предотвратить многократные установки от одного нажатия
            this.inputHandler.resetBombInput();
        }
    }
}
