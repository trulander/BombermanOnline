import React from 'react';
import { Box, Paper, Container, Button, Link } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import GameCanvas from '../components/GameCanvas';

const Game: React.FC = () => {
  const navigate = useNavigate();
  
  const handleBack = () => {
    navigate('/auth/dashboard');
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
        
        <GameCanvas/>
      </Paper>
    </Container>
  );
};

export default Game; 