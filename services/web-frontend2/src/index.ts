import { GameClient } from './client/GameClient';

window.addEventListener('load', () => {
    const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
    const gameClient = new GameClient(canvas);
    gameClient.start();
});
