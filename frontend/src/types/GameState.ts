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
        destroyed: boolean;
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
        grid: number[][];
    };
    score: number;
    level: number;
    gameOver: boolean;
}
