import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  FormControlLabel, 
  Checkbox,
  Alert,
  CircularProgress
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';

const validationSchema = Yup.object().shape({
  username: Yup.string()
    .required('Имя пользователя обязательно'),
  password: Yup.string()
    .required('Пароль обязателен'),
  remember_me: Yup.boolean()
});

const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (values: { username: string; password: string; remember_me: boolean }) => {
    setError(null);
    setLoading(true);
    
    try {
      const success = await login(values);
      
      if (success) {
        // Перенаправляем на сохраненный путь или dashboard по умолчанию
        const from = location.state?.from?.pathname || '/account/dashboard';
        navigate(from, { replace: true });
      } else {
        setError('Не удалось авторизоваться. Пожалуйста, проверьте введенные данные.');
      }
    } catch (error) {
      setError('Произошла ошибка при авторизации. Пожалуйста, попробуйте еще раз.');
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto' }}>
      <Typography component="h1" variant="h5" align="center" gutterBottom>
        Вход в систему
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Formik
        initialValues={{ username: '', password: '', remember_me: false }}
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
              name="password"
              label="Пароль"
              type="password"
              variant="outlined"
              fullWidth
              margin="normal"
              error={touched.password && Boolean(errors.password)}
              helperText={touched.password && errors.password}
            />
            
            <FormControlLabel
              control={<Field as={Checkbox} name="remember_me" color="primary" />}
              label="Запомнить меня"
              sx={{ mt: 1, mb: 2 }}
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={loading}
              sx={{ mt: 1, mb: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Войти'}
            </Button>
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
              <Link to="/account/reset-password" style={{ textDecoration: 'none' }}>
                <Typography variant="body2" color="primary">
                  Забыли пароль?
                </Typography>
              </Link>
              
              <Link to="/account/register" style={{ textDecoration: 'none' }}>
                <Typography variant="body2" color="primary">
                  Регистрация
                </Typography>
              </Link>
            </Box>
          </Form>
        )}
      </Formik>
    </Box>
  );
};

export default Login; 