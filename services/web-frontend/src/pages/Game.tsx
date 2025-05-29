import React, { useRef, useEffect } from 'react';
import { Box, Paper, Container, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import GameCanvas from '../components/GameCanvas';
import { GameClient } from '../components/GameClient';

const Game: React.FC = () => {
  const navigate = useNavigate();
  const gameClientRef = useRef<GameClient | null>(null);
  
  const handleBack = () => {
    navigate('/account/dashboard');
  };

  const handleAuthenticationFailed = () => {
    // Перенаправляем на страницу авторизации при ошибке авторизации
    navigate('/account/login');
  };

  const setGameClientRef = (gameClient: GameClient | null) => {
    gameClientRef.current = gameClient;
    if (gameClient) {
      gameClient.setAuthenticationFailedHandler(handleAuthenticationFailed);
    }
  };
  
  return (
    <Container maxWidth="lg">
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button 
            variant="outlined" 
            onClick={handleBack}
            sx={{ mb: 2 }}
          >
            Вернуться на главную
          </Button>
        </Box>
        
        <GameCanvas onGameClientReady={setGameClientRef} />
      </Paper>
    </Container>
  );
};

export default Game; 