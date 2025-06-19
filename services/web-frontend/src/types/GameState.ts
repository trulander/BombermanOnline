export interface GameState {
    players: {
        [playerId: string]: {
            x: number;
            y: number;
            width: number;
            height: number;
            lives: number;
            maxBombs: number;
            bombPower: number;
            invulnerable: boolean;
            color: string;
        }
    };
    enemies: {
        x: number;
        y: number;
        width: number;
        height: number;
        type: string;
        lives: number;
        destroyed: boolean;
        invulnerable: boolean;
    }[];
    bombs: {
        x: number;
        y: number;
        width: number;
        height: number;
        exploded: boolean;
        explosionCells: {
            x: number;
            y: number;
        }[];
        ownerId: string;
    }[];
    powerUps: {
        x: number;
        y: number;
        width: number;
        height: number;
        type: string;
    }[];
    map: {
        width: number;
        height: number;
        cellSize: number;
        grid_data?: number[][]; // Полная карта при первой загрузке
        changedCells?: { // Изменения в карте при обновлениях
            x: number;
            y: number;
            type: number;
        }[];
    };
    score: number;
    level: number;
    gameOver: boolean;
} 