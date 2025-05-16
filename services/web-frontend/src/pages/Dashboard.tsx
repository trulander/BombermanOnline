import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  Grid,
  Avatar,
  Divider,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { SportsEsports, Person, Settings } from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handlePlayGame = () => {
    navigate('/game');
  };

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        Личный кабинет
      </Typography>
      
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar 
              src={user?.profile_image} 
              alt={user?.username}
              sx={{ width: 64, height: 64, mr: 2 }}
            />
            <Box>
              <Typography variant="h6">
                {user?.full_name || user?.username}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {user?.email}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Роль: {user?.role}
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ mt: 2 }}>
            <Button 
              component={Link} 
              to="/auth/profile" 
              variant="outlined" 
              startIcon={<Person />}
              sx={{ mr: 1 }}
            >
              Редактировать профиль
            </Button>
          </Box>
        </CardContent>
      </Card>
      
      <Typography variant="h5" gutterBottom>
        Игровые возможности
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Начать игру
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Присоединяйтесь к существующим играм или создайте свою!
              </Typography>
              <Button 
                onClick={handlePlayGame}
                variant="contained" 
                color="primary"
                startIcon={<SportsEsports />}
                fullWidth
              >
                Играть
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Статистика
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Просмотрите свою игровую статистику, достижения и историю игр.
              </Typography>
              <Button 
                component="a" 
                href="/stats" 
                variant="outlined"
                startIcon={<Settings />}
                fullWidth
              >
                Статистика
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Divider sx={{ my: 4 }} />
      
      <Typography variant="h5" gutterBottom>
        Последние новости
      </Typography>
      
      <Card>
        <CardContent>
          <Typography variant="body1">
            Добро пожаловать в Bomberman Online! Пригласите друзей и начните игру вместе.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard; 