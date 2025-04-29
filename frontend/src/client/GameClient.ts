import { io, Socket } from 'socket.io-client';
import { InputHandler } from '../input/InputHandler';
import { Renderer } from './Renderer';
import { GameState } from '../types/GameState';

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

    constructor(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        
        // Initialize socket connection to Python backend
        this.socket = io('http://localhost:5000', {
            transports: ['websocket']
        });
        
        this.inputHandler = new InputHandler();
        this.renderer = new Renderer(canvas);
        
        this.setupSocketEvents();
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
        this.socket.on('game_update', (state: GameState) => {
            this.gameState = state;
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

    public start(): void {
        this.showMenu();
        this.startGameLoop();
    }

    private startGameLoop(): void {
        const gameLoop = () => {
            // Send inputs to server if in a game
            if (this.gameId && this.playerId) {
                this.sendInputs();
            }
            
            // Render current game state
            if (this.gameState) {
                this.renderer.render(this.gameState, this.playerId);
            }
            
            this.animationFrameId = requestAnimationFrame(gameLoop);
        };
        
        gameLoop();
    }

    private sendInputs(): void {
        const inputs = this.inputHandler.getInput();
        
        // Send inputs to server
        this.socket.emit('input', {
            game_id: this.gameId,
            inputs: {
                up: inputs.up,
                down: inputs.down,
                left: inputs.left,
                right: inputs.right
            }
        });
        
        // Handle bomb placement separately (to prevent rapid bombing)
        if (inputs.bomb) {
            this.socket.emit('place_bomb', {
                game_id: this.gameId
            });
            
            // Reset bomb input to prevent multiple bombs from single press
            this.inputHandler.resetBombInput();
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
        this.socket.emit('create_game', {}, (response: { game_id: string }) => {
            this.gameId = response.game_id;
            this.joinGame(this.gameId);
        });
    }

    private promptGameId(): void {
        const gameId = prompt('Enter Game ID:');
        if (gameId) {
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
                this.gameState = response.game_state;
                
                // Show game ID on screen for others to join
                const gameIdElement = document.getElementById('gameId');
                if (gameIdElement) {
                    gameIdElement.textContent = `Game ID: ${gameId}`;
                    gameIdElement.style.display = 'block';
                }
            } else {
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
            this.gameId = null;
            this.playerId = null;
            this.gameState = null;
            this.showMenu();
        });
    }

    public stop(): void {
        cancelAnimationFrame(this.animationFrameId);
        this.socket.disconnect();
    }
}
