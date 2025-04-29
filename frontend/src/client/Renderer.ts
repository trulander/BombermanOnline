import { GameState } from '../types/GameState';

export class Renderer {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private cellSize: number = 40;

    constructor(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d')!;
    }

    public render(gameState: GameState, currentPlayerId: string | null): void {
        // Resize canvas if needed based on map size
        if (gameState.map) {
            this.cellSize = gameState.map.cellSize;
            this.canvas.width = gameState.map.width * this.cellSize;
            this.canvas.height = gameState.map.height * this.cellSize;
        }

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Render map
        this.renderMap(gameState);

        // Render power-ups
        this.renderPowerUps(gameState);

        // Render bombs
        this.renderBombs(gameState);

        // Render enemies
        this.renderEnemies(gameState);

        // Render players
        this.renderPlayers(gameState, currentPlayerId);

        // Update UI
        this.updateUI(gameState);
    }

    private renderMap(gameState: GameState): void {
        const map = gameState.map;
        if (!map || !map.grid) return;

        for (let y = 0; y < map.height; y++) {
            for (let x = 0; x < map.width; x++) {
                const cellType = map.grid[y][x];

                switch (cellType) {
                    case 0: // Empty
                        this.ctx.fillStyle = "#8CBF26"; // Green grass
                        break;
                    case 1: // Solid wall
                        this.ctx.fillStyle = "#6B6B6B"; // Dark gray
                        break;
                    case 2: // Breakable block
                        this.ctx.fillStyle = "#B97A57"; // Brown
                        break;
                }

                this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);

                // Add visual details
                if (cellType === 1) { // Solid wall
                    this.ctx.strokeStyle = "#555555";
                    this.ctx.lineWidth = 2;
                    this.ctx.strokeRect(
                        x * this.cellSize + 2,
                        y * this.cellSize + 2,
                        this.cellSize - 4,
                        this.cellSize - 4
                    );
                } else if (cellType === 2) { // Breakable block
                    this.ctx.fillStyle = "#8E5E42";
                    this.ctx.fillRect(
                        x * this.cellSize + this.cellSize / 4,
                        y * this.cellSize + this.cellSize / 4,
                        this.cellSize / 2,
                        this.cellSize / 2
                    );
                }
            }
        }
    }

    private renderPowerUps(gameState: GameState): void {
        if (!gameState.powerUps) return;

        for (const powerUp of gameState.powerUps) {
            // Floating animation
            const time = performance.now() / 1000;
            const floatOffset = Math.sin(time * 3) * 3;

            // Get color based on type
            let color = "#9B59B6"; // Default purple
            let shadowColor = "rgba(155, 89, 182, 0.7)";
            let symbol = "?";

            switch (powerUp.type) {
                case "BOMB_UP":
                    color = "#F39C12"; // Orange
                    shadowColor = "rgba(243, 156, 18, 0.7)";
                    symbol = "B";
                    break;
                case "POWER_UP":
                    color = "#E74C3C"; // Red
                    shadowColor = "rgba(231, 76, 60, 0.7)";
                    symbol = "P";
                    break;
                case "LIFE_UP":
                    color = "#3498DB"; // Blue
                    shadowColor = "rgba(52, 152, 219, 0.7)";
                    symbol = "♥";
                    break;
                case "SPEED_UP":
                    color = "#2ECC71"; // Green
                    shadowColor = "rgba(46, 204, 113, 0.7)";
                    symbol = "S";
                    break;
            }

            // Draw power-up with glow
            this.ctx.shadowColor = shadowColor;
            this.ctx.shadowBlur = 10;

            // Draw base
            this.ctx.fillStyle = color;
            const x = powerUp.x;
            const y = powerUp.y + floatOffset;

            this.ctx.beginPath();
            this.ctx.arc(
                x + powerUp.width / 2,
                y + powerUp.height / 2,
                powerUp.width / 2,
                0,
                Math.PI * 2
            );
            this.ctx.fill();

            // Draw icon
            this.ctx.fillStyle = "white";
            this.ctx.font = `bold ${powerUp.width / 2}px Arial`;
            this.ctx.textAlign = "center";
            this.ctx.textBaseline = "middle";
            this.ctx.fillText(symbol, x + powerUp.width / 2, y + powerUp.height / 2);

            // Reset shadow
            this.ctx.shadowBlur = 0;
        }
    }

    private renderBombs(gameState: GameState): void {
        if (!gameState.bombs) return;

        for (const bomb of gameState.bombs) {
            if (!bomb.exploded) {
                // Bomb pulsating effect
                const time = performance.now() / 1000;
                const scale = 0.8 + Math.sin(time * 5) * 0.1;
                const size = bomb.width * scale;
                const offset = (bomb.width - size) / 2;

                // Draw bomb
                this.ctx.fillStyle = "#333";
                this.ctx.beginPath();
                this.ctx.arc(
                    bomb.x + bomb.width / 2,
                    bomb.y + bomb.height / 2,
                    size / 2,
                    0,
                    Math.PI * 2
                );
                this.ctx.fill();

                // Draw fuse
                this.ctx.strokeStyle = "#999";
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.moveTo(bomb.x + bomb.width / 2, bomb.y + offset);
                this.ctx.lineTo(bomb.x + bomb.width / 2, bomb.y - 5);
                this.ctx.stroke();
            } else {
                // Draw explosion
                for (const cell of bomb.explosionCells) {
                    // Explosion gradient
                    const gradient = this.ctx.createRadialGradient(
                        cell.x + this.cellSize / 2,
                        cell.y + this.cellSize / 2,
                        0,
                        cell.x + this.cellSize / 2,
                        cell.y + this.cellSize / 2,
                        this.cellSize / 2
                    );

                    gradient.addColorStop(0, "rgba(255, 255, 0, 0.8)");
                    gradient.addColorStop(0.7, "rgba(255, 80, 0, 0.8)");
                    gradient.addColorStop(1, "rgba(255, 0, 0, 0.4)");

                    this.ctx.fillStyle = gradient;
                    this.ctx.fillRect(cell.x, cell.y, this.cellSize, this.cellSize);
                }
            }
        }
    }

    private renderEnemies(gameState: GameState): void {
        if (!gameState.enemies) return;

        for (const enemy of gameState.enemies) {
            if (enemy.destroyed) {
                continue; // Skip rendering destroyed enemies
            }

            // Draw enemy
            this.ctx.fillStyle = "#E74C3C"; // Red
            this.ctx.fillRect(enemy.x, enemy.y, enemy.width, enemy.height);

            // Draw enemy details (eyes)
            this.ctx.fillStyle = "white";
            const eyeSize = enemy.width / 6;
            this.ctx.fillRect(
                enemy.x + enemy.width / 3 - eyeSize / 2,
                enemy.y + enemy.height / 3,
                eyeSize,
                eyeSize
            );
            this.ctx.fillRect(
                enemy.x + enemy.width * 2 / 3 - eyeSize / 2,
                enemy.y + enemy.height / 3,
                eyeSize,
                eyeSize
            );
        }
    }

    private renderPlayers(gameState: GameState, currentPlayerId: string | null): void {
        if (!gameState.players) return;

        for (const [playerId, player] of Object.entries(gameState.players)) {
            // Skip rendering dead players
            if (player.lives <= 0) continue;

            // Skip rendering if invulnerable and in blinking phase
            if (player.invulnerable && Math.floor(performance.now() / 100) % 2 === 0) {
                continue;
            }

            // Get player color
            const color = player.color || "#3498db"; // Default blue
            const darkColor = this.darkenColor(color, 0.8);

            // Highlight current player
            if (playerId === currentPlayerId) {
                // Draw highlight around current player
                this.ctx.strokeStyle = "#FFFF00";
                this.ctx.lineWidth = 3;
                this.ctx.strokeRect(
                    player.x - 2,
                    player.y - 2,
                    player.width + 4,
                    player.height + 4
                );
            }

            // Draw player
            this.ctx.fillStyle = color;
            this.ctx.fillRect(player.x, player.y, player.width, player.height);

            // Draw player details
            this.ctx.fillStyle = darkColor;

            // Head
            const headSize = player.width / 2;
            this.ctx.fillRect(
                player.x + (player.width - headSize) / 2,
                player.y,
                headSize,
                headSize
            );

            // Eyes
            this.ctx.fillStyle = "white";
            const eyeSize = headSize / 4;
            this.ctx.fillRect(
                player.x + player.width / 2 - eyeSize - eyeSize / 2,
                player.y + headSize / 3,
                eyeSize,
                eyeSize
            );
            this.ctx.fillRect(
                player.x + player.width / 2 + eyeSize / 2,
                player.y + headSize / 3,
                eyeSize,
                eyeSize
            );
        }
    }

    private updateUI(gameState: GameState): void {
        // Update score element
        const scoreElement = document.getElementById('score');
        if (scoreElement) {
            scoreElement.textContent = `Level: ${gameState.level} | Score: ${gameState.score}`;
        }
    }

    private darkenColor(color: string, factor: number): string {
        // Convert hex to RGB
        let r = 0, g = 0, b = 0;
        if (color.startsWith('#')) {
            r = parseInt(color.substr(1, 2), 16);
            g = parseInt(color.substr(3, 2), 16);
            b = parseInt(color.substr(5, 2), 16);
        }

        // Darken
        r = Math.floor(r * factor);
        g = Math.floor(g * factor);
        b = Math.floor(b * factor);

        // Convert back to hex
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
}
