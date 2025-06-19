import React, {useEffect, useRef} from 'react';
import {GameClient} from './GameClient';
import {Box, Typography} from '@mui/material';
import {GameCanvasProps} from "../types/Game";

const GameCanvas: React.FC<GameCanvasProps> = ({
  socketUrl = 'http://localhost', 
  socketPath = '/socket.io',
  onGameClientReady,
  gameId,
  userId
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const gameClientRef = useRef<GameClient | null>(null);
  
  useEffect(() => {
    if (canvasRef.current) {
      // Инициализация игрового клиента
      gameClientRef.current = new GameClient(
        canvasRef.current,
        userId
      );
      
      // Уведомляем родительский компонент
      onGameClientReady?.(gameClientRef.current);
      
      // Если есть gameId, пытаемся присоединиться к игре
      if (gameId) {
        gameClientRef.current.joinGame(gameId, userId || '');
      } else {
        // Запускаем игровое меню, если нет gameId
        gameClientRef.current.start();
      }
      
      // Очистка при размонтировании компонента
      return () => {
        if (gameClientRef.current) {
          gameClientRef.current.stop();
          onGameClientReady?.(null);
        }
      };
    }
  }, [gameId, onGameClientReady, userId]);
  
  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center'
    }}>
      <canvas 
        ref={canvasRef} 
        width={800} 
        height={600} 
        style={{ 
          display: 'block', 
          backgroundColor: '#000',
          border: '1px solid #333'
        }}
      />
      
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Используйте клавиши WASD или стрелки для перемещения, пробел для установки бомбы
        </Typography>
      </Box>
    </Box>
  );
};

export default GameCanvas; 