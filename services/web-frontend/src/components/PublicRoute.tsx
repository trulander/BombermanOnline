import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../context/AuthContext';

interface PublicRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

const PublicRoute: React.FC<PublicRouteProps> = ({ children, redirectTo = '/account/dashboard' }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  
  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '50vh',
        gap: 2
      }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Загрузка...
        </Typography>
      </Box>
    );
  }
  
  if (isAuthenticated) {
    // Если пользователь пришел с защищенного маршрута, отправляем его туда
    const from = location.state?.from?.pathname || redirectTo;
    return <Navigate to={from} replace />;
  }
  
  return <>{children}</>;
};

export default PublicRoute; 