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
    private keyDownHandler: (e: KeyboardEvent) => void;
    private keyUpHandler: (e: KeyboardEvent) => void;
    private isListening: boolean = false;
    
    constructor() {
        this.input = {
            up: false,
            down: false,
            left: false,
            right: false,
            bomb: false,
            restart: false
        };
        
        // Создаем привязанные обработчики, чтобы можно было удалить их позже
        this.keyDownHandler = this.handleKeyDown.bind(this);
        this.keyUpHandler = this.handleKeyUp.bind(this);
    }
    
    public startListening(): void {
        if (!this.isListening) {
            window.addEventListener('keydown', this.keyDownHandler);
            window.addEventListener('keyup', this.keyUpHandler);
            this.isListening = true;
            console.log('Input handler started listening');
        }
    }
    
    public stopListening(): void {
        if (this.isListening) {
            window.removeEventListener('keydown', this.keyDownHandler);
            window.removeEventListener('keyup', this.keyUpHandler);
            this.isListening = false;
            
            // Сбрасываем все входные данные при остановке
            this.resetInput();
            console.log('Input handler stopped listening');
        }
    }
    
    private resetInput(): void {
        this.input = {
            up: false,
            down: false,
            left: false,
            right: false,
            bomb: false,
            restart: false
        };
    }
    
    private handleKeyDown(e: KeyboardEvent): void {
        switch (e.key) {
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
    
    private handleKeyUp(e: KeyboardEvent): void {
        switch (e.key) {
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
