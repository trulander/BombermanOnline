import React, { useState } from 'react';
import { Link } from 'react-router-dom';
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
  email: Yup.string()
    .email('Некорректный email')
    .required('Email обязателен')
});

const ResetPassword: React.FC = () => {
  const { resetPassword } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (values: { email: string }) => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    try {
      const success = await resetPassword(values.email);
      
      if (success) {
        setSuccess('Инструкции по сбросу пароля отправлены на указанный email.');
      } else {
        setError('Не удалось отправить инструкции по сбросу пароля.');
      }
    } catch (error) {
      setError('Произошла ошибка при отправке инструкций по сбросу пароля.');
      console.error('Reset password error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto' }}>
      <Typography component="h1" variant="h5" align="center" gutterBottom>
        Сброс пароля
      </Typography>
      
      <Typography variant="body2" align="center" sx={{ mb: 2 }}>
        Введите ваш email для получения инструкций по сбросу пароля
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
        initialValues={{ email: '' }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ errors, touched }) => (
          <Form>
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
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={loading}
              sx={{ mt: 3, mb: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Отправить инструкции'}
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

export default ResetPassword;