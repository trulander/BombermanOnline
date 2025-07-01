import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Typography, Button, Container } from '@mui/material';
import { useAuth } from '../context/AuthContext';

const NotFound: React.FC = () => {
  const { isAuthenticated } = useAuth();
  
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '80vh',
          textAlign: 'center'
        }}
      >
        <Typography variant="h1" component="h1" gutterBottom>
          404
        </Typography>
        
        <Typography variant="h5" component="h2" gutterBottom>
          Страница не найдена
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          Запрошенная страница не существует или была перемещена.
        </Typography>
        
        <Button
          component={Link}
          to={isAuthenticated ? "/account/dashboard" : "/"}
          variant="contained"
          color="primary"
          sx={{ mt: 3 }}
        >
          {isAuthenticated ? "Вернуться в личный кабинет" : "На главную"}
        </Button>
      </Box>
    </Container>
  );
};

export default NotFound;
