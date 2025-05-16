import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Alert,
  CircularProgress
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';

const validationSchema = Yup.object().shape({
  password: Yup.string()
    .min(8, 'Пароль должен быть не менее 8 символов')
    .required('Пароль обязателен'),
  confirmPassword: Yup.string()
    .oneOf([Yup.ref('password')], 'Пароли должны совпадать')
    .required('Подтверждение пароля обязательно')
});

const ConfirmResetPassword: React.FC = () => {
  const { confirmResetPassword } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  if (!token) {
    return (
      <Box sx={{ maxWidth: 400, mx: 'auto', textAlign: 'center' }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Отсутствует токен сброса пароля
        </Alert>
        <Link to="/auth/reset-password" style={{ textDecoration: 'none' }}>
          <Typography variant="body2" color="primary">
            Вернуться на страницу сброса пароля
          </Typography>
        </Link>
      </Box>
    );
  }

  const handleSubmit = async (values: { password: string; confirmPassword: string }) => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    try {
      const success = await confirmResetPassword(token, values.password);
      
      if (success) {
        setSuccess('Пароль успешно изменен!');
        setTimeout(() => {
          navigate('/auth/login');
        }, 3000);
      } else {
        setError('Не удалось изменить пароль. Возможно, ссылка устарела или недействительна.');
      }
    } catch (error) {
      setError('Произошла ошибка при изменении пароля.');
      console.error('Confirm reset password error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto' }}>
      <Typography component="h1" variant="h5" align="center" gutterBottom>
        Создание нового пароля
      </Typography>
      
      <Typography variant="body2" align="center" sx={{ mb: 2 }}>
        Введите новый пароль
      </Typography>
      
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
      
      <Formik
        initialValues={{ password: '', confirmPassword: '' }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ errors, touched }) => (
          <Form>
            <Field
              as={TextField}
              name="password"
              label="Новый пароль"
              type="password"
              variant="outlined"
              fullWidth
              margin="normal"
              error={touched.password && Boolean(errors.password)}
              helperText={touched.password && errors.password}
            />
            
            <Field
              as={TextField}
              name="confirmPassword"
              label="Подтвердите новый пароль"
              type="password"
              variant="outlined"
              fullWidth
              margin="normal"
              error={touched.confirmPassword && Boolean(errors.confirmPassword)}
              helperText={touched.confirmPassword && errors.confirmPassword}
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={loading}
              sx={{ mt: 3, mb: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Сохранить новый пароль'}
            </Button>
            
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Link to="/auth/login" style={{ textDecoration: 'none' }}>
                <Typography variant="body2" color="primary">
                  Вернуться на страницу входа
                </Typography>
              </Link>
            </Box>
          </Form>
        )}
      </Formik>
    </Box>
  );
};

export default ConfirmResetPassword; 