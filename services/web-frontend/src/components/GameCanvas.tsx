import React, { useEffect, useRef } from 'react';
import { GameClient } from './GameClient';
import { Box, Typography } from '@mui/material';

interface GameCanvasProps {
  socketUrl?: string;
  socketPath?: string;
}

const GameCanvas: React.FC<GameCanvasProps> = ({ 
  socketUrl = 'http://localhost', 
  socketPath = '/socket.io' 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const gameClientRef = useRef<GameClient | null>(null);
  
  useEffect(() => {
    if (canvasRef.current) {
      // Инициализация игрового клиента
      gameClientRef.current = new GameClient(
        canvasRef.current
      );
      
      // Запуск игры
      gameClientRef.current.start();
      
      // Очистка при размонтировании компонента
      return () => {
        if (gameClientRef.current) {
          gameClientRef.current.stop();
        }
      };
    }
  });
  
  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      mt: 2
    }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1" align="center" gutterBottom>
          Bomberman Online
        </Typography>
        <Typography id="gameId" sx={{ 
          display: 'block',
          // backgroundColor: '#555',
          padding: '5px 10px',
          borderRadius: '5px',
          fontFamily: 'monospace'
        }}>
          Game ID:
        </Typography>
      </Box>
      
      <Box sx={{ position: 'relative' }}>
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
        <Box sx={{ 
          position: 'absolute',
          bottom: -30,
          left: 0,
          width: '100%',
          color: 'black',
          textAlign: 'center',
          display: 'block ruby'
        }}>
          <Typography id="level" variant="body1">
            Level: 1
          </Typography> |
          <Typography id="score" variant="body1">
            Score: 0
          </Typography>
        </Box>
      </Box>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Используйте клавиши WASD или стрелки для перемещения, пробел для установки бомбы
        </Typography>
      </Box>
    </Box>
  );
};

export default GameCanvas; 