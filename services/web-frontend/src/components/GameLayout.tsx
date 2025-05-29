import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  AppBar, 
  Box, 
  Toolbar, 
  Typography, 
  Button, 
  IconButton
} from '@mui/material';
import { ArrowBack, Home } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

interface GameLayoutProps {
  children: React.ReactNode;
}

const GameLayout: React.FC<GameLayoutProps> = ({ children }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [gameId, setGameId] = useState<string>('');
  const [level, setLevel] = useState<number>(1);
  const [score, setScore] = useState<number>(0);

  const handleBack = () => {
    navigate('/account/dashboard');
  };

  const handleHome = () => {
    navigate('/');
  };

  // Функции для обновления игровой информации (будут вызываться из GameClient)
  useEffect(() => {
    // Слушаем обновления игровой информации через DOM events
    const handleGameIdUpdate = (event: any) => {
      setGameId(event.detail);
    };

    const handleLevelUpdate = (event: any) => {
      setLevel(event.detail);
    };

    const handleScoreUpdate = (event: any) => {
      setScore(event.detail);
    };

    window.addEventListener('gameIdUpdate', handleGameIdUpdate);
    window.addEventListener('levelUpdate', handleLevelUpdate);
    window.addEventListener('scoreUpdate', handleScoreUpdate);

    return () => {
      window.removeEventListener('gameIdUpdate', handleGameIdUpdate);
      window.removeEventListener('levelUpdate', handleLevelUpdate);
      window.removeEventListener('scoreUpdate', handleScoreUpdate);
    };
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="back"
            onClick={handleBack}
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Bomberman Online
          </Typography>
          
          {gameId && (
            <Typography variant="body1" sx={{ mr: 3, fontFamily: 'monospace' }}>
              Game ID: {gameId}
            </Typography>
          )}
          
          <Typography variant="body1" sx={{ mr: 2 }}>
            Level: {level}
          </Typography>
          
          <Typography variant="body1" sx={{ mr: 2 }}>
            Score: {score}
          </Typography>
          
          <IconButton
            edge="end"
            color="inherit"
            aria-label="home"
            onClick={handleHome}
          >
            <Home />
          </IconButton>
        </Toolbar>
      </AppBar>
      
      <Box sx={{ 
        flex: 1, 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        backgroundColor: '#000',
        overflow: 'hidden'
      }}>
        {children}
      </Box>
    </Box>
  );
};

export default GameLayout; 