import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  Grid,
  Paper,
  Divider,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { SportsEsports, EmojiEvents, Timeline } from '@mui/icons-material';

const Stats: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/account/dashboard');
  };

  const handlePlayGame = () => {
    navigate('/account/game');
  };

  // Моковые данные статистики для демонстрации
  const mockStats = {
    gamesPlayed: 42,
    gamesWon: 28,
    gamesLost: 14,
    winRate: Math.round((28 / 42) * 100),
    totalScore: 15430,
    bestScore: 2850,
    enemiesDestroyed: 156,
    blocksDestroyed: 389,
    powerUpsCollected: 67,
    bombsPlaced: 523
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography component="h1" variant="h4">
          Игровая статистика
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            onClick={handleBack}
            sx={{ mr: 2 }}
          >
            Назад
          </Button>
          <Button 
            variant="contained" 
            onClick={handlePlayGame}
            startIcon={<SportsEsports />}
          >
            Играть
          </Button>
        </Box>
      </Box>
      
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Общая статистика для {user?.username}
        </Typography>
        
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12} md={4}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <SportsEsports sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {mockStats.gamesPlayed}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Игр сыграно
              </Typography>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <EmojiEvents sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {mockStats.winRate}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Процент побед
              </Typography>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <Timeline sx={{ fontSize: 48, color: 'secondary.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {mockStats.totalScore.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Общий счет
              </Typography>
            </Card>
          </Grid>
        </Grid>
      </Paper>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Результаты игр
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Побед:</Typography>
                <Typography variant="body1" color="success.main">
                  {mockStats.gamesWon}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Поражений:</Typography>
                <Typography variant="body1" color="error.main">
                  {mockStats.gamesLost}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body1">Лучший счет:</Typography>
                <Typography variant="body1" color="primary.main">
                  {mockStats.bestScore.toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Игровые достижения
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Врагов уничтожено:</Typography>
                <Typography variant="body1">
                  {mockStats.enemiesDestroyed}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Блоков разрушено:</Typography>
                <Typography variant="body1">
                  {mockStats.blocksDestroyed}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Усилений собрано:</Typography>
                <Typography variant="body1">
                  {mockStats.powerUpsCollected}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body1">Бомб установлено:</Typography>
                <Typography variant="body1">
                  {mockStats.bombsPlaced}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Статистика обновляется после каждой игры
        </Typography>
      </Box>
    </Box>
  );
};

export default Stats; 