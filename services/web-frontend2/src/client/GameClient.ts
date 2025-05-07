import { io } from 'socket.io-client';
import { InputHandler } from '../input/InputHandler';
import { Renderer } from './Renderer';
import { GameState } from '../types/GameState';

export class GameClient {
    private canvas: HTMLCanvasElement;
    private socket: any;
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

    constructor(canvasId: string) {
        // Загружаем canvas
        const canvasElement = document.getElementById(canvasId) as HTMLCanvasElement;
        if (!canvasElement) {
            throw new Error(`Canvas with id '${canvasId}' not found`);
        }
        this.canvas = canvasElement;
        
        // Инициализируем обработчик ввода
        this.inputHandler = new InputHandler();
        
        // Создаем рендерер
        this.renderer = new Renderer(this.canvas);
        
        // Подключаемся к Socket.IO серверу
        this.socket = io('http://localhost:5001');
        
        // Настраиваем обработчики событий Socket.IO
        this.setupSocketEvents();
        
        // Запускаем игровой цикл
        this.startGameLoop();
        
        // Показываем стартовый экран
        this.showMenu();
    }

    private setupSocketEvents(): void {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.showMenu();
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.isConnected = false;
            this.showDisconnectedMessage();
        });

        // Game events
        this.socket.on('game_state', (gameState: GameState) => {
            console.log('Получено событие game_state');
            this.processGameStateUpdate(gameState);
        });

        // Добавляем обработчик для game_update, так как сервер использует это событие в game_loop
        this.socket.on('game_update', (gameState: GameState) => {
            console.log('Получено событие game_update');
            this.processGameStateUpdate(gameState);
        });

        this.socket.on('player_disconnected', (data: { player_id: string }) => {
            console.log(`Player ${data.player_id} disconnected`);
            
            // Update UI to show player disconnect if needed
            if (this.gameState && this.gameState.players[data.player_id]) {
                // Remove player from local state until next game_update
                delete this.gameState.players[data.player_id];
            }
        });

        this.socket.on('game_over', () => {
            this.showGameOver();
        });
    }

    private showMenu(): void {
        // Очищаем canvas и показываем меню
        this.renderer.clearCanvas();
        this.renderer.drawMenu();
        
        // Add event listeners for buttons
        document.getElementById('create-game-btn')?.addEventListener('click', () => this.createGame());
        document.getElementById('join-game-btn')?.addEventListener('click', () => this.showJoinGameForm());
    }
    
    private showJoinGameForm(): void {
        // Show form to enter game ID
        this.renderer.drawJoinGameForm();
        
        document.getElementById('join-game-submit')?.addEventListener('click', () => {
            const gameIdInput = document.getElementById('game-id-input') as HTMLInputElement;
            if (gameIdInput && gameIdInput.value) {
                this.joinGame(gameIdInput.value);
        }
        });
    }

    // Запрос полного состояния игры
    private requestGameState(): void {
        if (this.gameId && this.playerId) {
            console.log('Запрашиваем состояние игры');
            this.socket.emit('get_game_state', { 
                game_id: this.gameId
            }, this.handleGetGameStateResponse.bind(this));
        } else {
            console.warn('Невозможно запросить состояние игры: gameId =', this.gameId, 'playerId =', this.playerId);
        }
    }

    private handleGetGameStateResponse(response: any): void {
        console.log('Получен ответ на запрос состояния игры', response);
        
        if (response.success && response.game_state) {
            this.processGameStateUpdate(response.game_state);
        }
    }

    private showDisconnectedMessage(): void {
        // Показываем сообщение о разрыве соединения
        this.renderer.clearCanvas();
        this.renderer.drawText('Disconnected from server', this.canvas.width / 2, this.canvas.height / 2, 'red');
        this.renderer.drawText('Trying to reconnect...', this.canvas.width / 2, this.canvas.height / 2 + 30, 'white');
    }
    
    private showGameOver(): void {
        // Показываем сообщение о завершении игры
        const ctx = this.canvas.getContext('2d');
        if (!ctx) return;
        
        const score = this.gameState?.score || 0;
        const level = this.gameState?.level || 1;
        
        this.renderer.drawGameOver(score, level);
        
        // Слушаем клавишу R для рестарта
        const restartListener = (e: KeyboardEvent) => {
            if (e.key === 'r' || e.key === 'R') {
                window.removeEventListener('keydown', restartListener);
                this.createGame();
    }
        };
        
        window.addEventListener('keydown', restartListener);
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
            console.log(`Давно не было обновлений (${Math.round(timeSinceLastUpdate)}ms), запрашиваем состояние игры`);
            // Запрашиваем новое состояние игры
            this.requestGameState();
            this.lastUpdateTime = currentTime; // Обновляем время, чтобы не спамить запросами
        }

        // Отрисовка, если есть состояние игры
        if (this.gameState) {
            // Добавляем текущего игрока в состояние
            if (this.playerId) {
                this.gameState.currentPlayerId = this.playerId;
            }
            this.renderer.render(this.gameState);
        }
    }

    private processGameStateUpdate(gameState: GameState): void {
        this.gameState = gameState;
        this.lastUpdateTime = performance.now();
        
        // Если карта была инициализирована с полным обновлением
        if (gameState.map && gameState.map.grid) {
            this.renderer.updateMap(gameState.map);
        }
    }

    private createGame(): void {
        if (!this.isConnected) {
            alert('Cannot create game: not connected to server');
            return;
        }
        
        // Отправляем запрос на создание игры
        this.socket.emit('create_game', {}, (response: any) => {
            console.log('Create game response:', response);
        
            if (response.success) {
                this.gameId = response.game_id;
                
                // Показываем ID игры для присоединения других игроков
                this.renderer.clearCanvas();
                this.renderer.drawText(`Game created!`, this.canvas.width / 2, this.canvas.height / 2 - 60, 'white');
                this.renderer.drawText(`Game ID: ${this.gameId}`, this.canvas.width / 2, this.canvas.height / 2 - 30, 'white');
                this.renderer.drawText(`Share this ID with other players to join`, this.canvas.width / 2, this.canvas.height / 2, 'white');
                this.renderer.drawText(`Joining game...`, this.canvas.width / 2, this.canvas.height / 2 + 30, 'white');
                
                // Автоматически присоединяемся к созданной игре
                setTimeout(() => {
                    if (this.gameId) {
            this.joinGame(this.gameId);
                    }
                }, 2000);
            } else {
                alert(`Failed to create game: ${response.message || 'Unknown error'}`);
        }
        });
    }

    private joinGame(gameId: string): void {
        if (!this.isConnected) {
            alert('Cannot join game: not connected to server');
            return;
        }
        
        // Отправляем запрос на присоединение к игре
        this.socket.emit('join_game', { game_id: gameId }, (response: any) => {
            console.log('Join game response:', response);
            
            if (response.success) {
                this.gameId = gameId;
                this.playerId = response.player_id;
                
                // Получаем начальное состояние игры
                if (response.game_state) {
                    this.processGameStateUpdate(response.game_state);
                } else {
                    // Если состояние не пришло с ответом, запрашиваем отдельно
                    this.requestGameState();
                }
                
                // Теперь включаем обработку ввода
                this.inputHandler.startListening();
                
                console.log(`Joined game ${this.gameId} as player ${this.playerId}`);
            } else {
                alert(`Failed to join game: ${response.message || 'Unknown error'}`);
            }
        });
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
    
    // Метод для остановки клиента
    public stop(): void {
        // Останавливаем игровой цикл
        cancelAnimationFrame(this.animationFrameId);
        
        // Отключаем обработку ввода
        this.inputHandler.stopListening();
        
        // Отсоединяемся от сервера
        this.socket.disconnect();
    }
}
