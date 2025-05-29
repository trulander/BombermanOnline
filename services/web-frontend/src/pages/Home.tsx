import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Button, 
  Container, 
  Grid,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import { SportsEsports, AccountBox, Person } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

const Home: React.FC = () => {
  const { isAuthenticated } = useAuth();
  
  return (
    <Container maxWidth="lg">
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Bomberman Online
        </Typography>
        
        <Typography variant="h5" component="h2" gutterBottom color="text.secondary">
          Играйте в классический Bomberman онлайн с друзьями!
        </Typography>
        
        <Typography variant="body1" paragraph sx={{ mt: 4, mb: 6 }}>
          Присоединяйтесь к захватывающим онлайн-баталиям, создавайте свои игры 
          или присоединяйтесь к существующим. Соревнуйтесь с игроками со всего мира!
        </Typography>
        
        <Grid container spacing={4} sx={{ mt: 4 }}>
          <Grid item xs={12} md={4}>
            <Card elevation={3}>
              <CardContent>
                <SportsEsports sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Играть онлайн
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Создавайте или присоединяйтесь к играм с друзьями и другими игроками
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center' }}>
                <Button 
                  component={Link} 
                  to={isAuthenticated ? "/account/game" : "/account/login"}
                  variant="contained" 
                  color="primary"
                >
                  {isAuthenticated ? "Начать игру" : "Войти для игры"}
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card elevation={3}>
              <CardContent>
                <AccountBox sx={{ fontSize: 60, color: 'secondary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Личный кабинет
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Управляйте своим профилем, просматривайте статистику и достижения
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center' }}>
                <Button 
                  component={Link} 
                  to={isAuthenticated ? "/account/dashboard" : "/account/register"}
                  variant="outlined"
                >
                  {isAuthenticated ? "Мой профиль" : "Регистрация"}
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card elevation={3}>
              <CardContent>
                <Person sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Статистика
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Следите за своими достижениями, рейтингом и игровой историей
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center' }}>
                <Button 
                  component={Link} 
                  to={isAuthenticated ? "/account/stats" : "/account/login"}
                  variant="outlined"
                >
                  {isAuthenticated ? "Просмотреть" : "Войти"}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        </Grid>
        
        {!isAuthenticated && (
          <Box sx={{ mt: 6 }}>
            <Typography variant="h6" gutterBottom>
              Готовы начать?
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 2 }}>
              <Button 
                component={Link} 
                to="/account/register" 
                variant="contained" 
                color="primary" 
                size="large"
              >
                Зарегистрироваться
              </Button>
              <Button 
                component={Link} 
                to="/account/login" 
                variant="outlined" 
                size="large"
              >
                Войти
              </Button>
            </Box>
          </Box>
        )}
        
        {isAuthenticated && (
          <Box sx={{ mt: 6 }}>
            <Button 
              component={Link} 
              to="/account/game" 
              variant="contained" 
              color="primary" 
              size="large"
              startIcon={<SportsEsports />}
            >
              Начать играть сейчас!
            </Button>
          </Box>
        )}
      </Box>
    </Container>
  );
};

export default Home; 