import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Alert,
  CircularProgress,
  Button
} from '@mui/material';
import { api } from '../services/api';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setError('Отсутствует токен подтверждения email');
        setLoading(false);
        return;
      }
      
      try {
        const response = await api.get(`/auth/verify-email?token=${token}`);
        
        if (response.data && response.data.success) {
          setSuccess('Email успешно подтвержден! Теперь вы можете войти в систему.');
        } else {
          setError('Не удалось подтвердить email. Возможно, ссылка устарела или недействительна.');
        }
      } catch (error) {
        setError('Произошла ошибка при подтверждении email.');
        console.error('Verify email error:', error);
      } finally {
        setLoading(false);
      }
    };
    
    verifyEmail();
  }, [token]);

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto', textAlign: 'center' }}>
      <Typography component="h1" variant="h5" gutterBottom>
        Подтверждение email
      </Typography>
      
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}
      
      <Box sx={{ mt: 4 }}>
        <Button 
          component={Link} 
          to="/account/login" 
          variant="contained" 
          color="primary"
          sx={{ mx: 1 }}
        >
          Перейти на страницу входа
        </Button>
      </Box>
    </Box>
  );
};

export default VerifyEmail; 