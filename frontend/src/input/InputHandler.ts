export interface Input {
    up: boolean;
    down: boolean;
    left: boolean;
    right: boolean;
    bomb: boolean;
    restart: boolean;
}

export class InputHandler {
    private input: Input;
    
    constructor() {
        this.input = {
            up: false,
            down: false,
            left: false,
            right: false,
            bomb: false,
            restart: false
        };
        
        this.setupEventListeners();
    }
    
    private setupEventListeners(): void {
        window.addEventListener('keydown', (e) => {
            this.handleKeyDown(e.key);
        });
        
        window.addEventListener('keyup', (e) => {
            this.handleKeyUp(e.key);
        });
    }
    
    private handleKeyDown(key: string): void {
        switch (key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                this.input.up = true;
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                this.input.down = true;
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                this.input.left = true;
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                this.input.right = true;
                break;
            case ' ':
                this.input.bomb = true;
                break;
            case 'r':
            case 'R':
                this.input.restart = true;
                break;
        }
    }
    
    private handleKeyUp(key: string): void {
        switch (key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                this.input.up = false;
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                this.input.down = false;
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                this.input.left = false;
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                this.input.right = false;
                break;
            case ' ':
                this.input.bomb = false;
                break;
            case 'r':
            case 'R':
                this.input.restart = false;
                break;
        }
    }
    
    public getInput(): Input {
        return this.input;
    }
    
    public resetBombInput(): void {
        this.input.bomb = false;
    }
}
