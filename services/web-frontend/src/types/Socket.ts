// Определение интерфейса Socket для использования в проекте
export interface Socket {
    emit(event: string, data?: any, callback?: (response: any) => void): void;
    on(event: string, callback: (data: any) => void): void;
    disconnect(): void;
    once(event: string, callback: (data: any) => void): void;
    off(event: string, callback?: (data: any) => void): void;
} 