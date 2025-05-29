import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  username: Yup.string()
    .required('Имя пользователя обязательно')
    .min(3, 'Имя пользователя должно быть не менее 3 символов')
    .max(30, 'Имя пользователя должно быть не более 30 символов'),
  email: Yup.string()
    .email('Некорректный email')
    .required('Email обязателен'),
  password: Yup.string()
    .min(8, 'Пароль должен быть не менее 8 символов')
    .required('Пароль обязателен'),
  confirmPassword: Yup.string()
    .oneOf([Yup.ref('password')], 'Пароли должны совпадать')
    .required('Подтверждение пароля обязательно'),
  full_name: Yup.string()
});

const Register: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (values: { username: string; email: string; password: string; full_name?: string }) => {
    // Удаляем поле confirmPassword, т.к. его нет в API
    const { confirmPassword, ...registerData } = values as any;
    
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    try {
      const success = await register(registerData);
      
      if (success) {
        setSuccess('Регистрация успешна! Проверьте вашу почту для подтверждения аккаунта.');
        setTimeout(() => {
          navigate('/account/login');
        }, 3000);
      } else {
        setError('Не удалось зарегистрироваться. Пожалуйста, проверьте введенные данные.');
      }
    } catch (error) {
      setError('Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.');
      console.error('Register error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto' }}>
      <Typography component="h1" variant="h5" align="center" gutterBottom>
        Регистрация
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
        initialValues={{ username: '', email: '', password: '', confirmPassword: '', full_name: '' }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ errors, touched }) => (
          <Form>
            <Field
              as={TextField}
              name="username"
              label="Имя пользователя"
              variant="outlined"
              fullWidth
              margin="normal"
              error={touched.username && Boolean(errors.username)}
              helperText={touched.username && errors.username}
            />
            
            <Field
              as={TextField}
              name="email"
              label="Email"
              type="email"
              variant="outlined"
              fullWidth
              margin="normal"
              error={touched.email && Boolean(errors.email)}
              helperText={touched.email && errors.email}
            />
            
            <Field
              as={TextField}
              name="full_name"
              label="Полное имя (опционально)"
              variant="outlined"
              fullWidth
              margin="normal"
              error={touched.full_name && Boolean(errors.full_name)}
              helperText={touched.full_name && errors.full_name}
            />
            
            <Field
              as={TextField}
              name="password"
              label="Пароль"
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
              label="Подтвердите пароль"
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
              {loading ? <CircularProgress size={24} /> : 'Зарегистрироваться'}
            </Button>
            
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Link to="/account/login" style={{ textDecoration: 'none' }}>
                <Typography variant="body2" color="primary">
                  Уже есть аккаунт? Войти
                </Typography>
              </Link>
            </Box>
          </Form>
        )}
      </Formik>
    </Box>
  );
};

export default Register; 