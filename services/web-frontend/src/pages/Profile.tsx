import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Alert,
  CircularProgress,
  Avatar,
  Grid,
  Paper
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';

const validationSchema = Yup.object().shape({
  username: Yup.string()
    .min(3, 'Имя пользователя должно быть не менее 3 символов')
    .max(30, 'Имя пользователя должно быть не более 30 символов'),
  full_name: Yup.string()
    .max(100, 'Полное имя должно быть не более 100 символов'),
  profile_image: Yup.string()
    .url('Должен быть действительный URL-адрес')
});

const Profile: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  if (!user) {
    return (
      <Box sx={{ textAlign: 'center', p: 4 }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Загрузка данных пользователя...
        </Typography>
      </Box>
    );
  }

  const handleSubmit = async (values: any) => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    try {
      // Проверяем, что данные были изменены
      const changedValues: any = {};
      
      Object.keys(values).forEach(key => {
        if (values[key] !== user[key as keyof typeof user] && values[key] !== '') {
          changedValues[key] = values[key];
        }
      });
      
      if (Object.keys(changedValues).length === 0) {
        setSuccess('Данные не были изменены.');
        setLoading(false);
        return;
      }
      
      const success = await updateProfile(changedValues);
      
      if (success) {
        setSuccess('Профиль успешно обновлен!');
      } else {
        setError('Не удалось обновить профиль. Пожалуйста, проверьте введенные данные.');
      }
    } catch (error) {
      setError('Произошла ошибка при обновлении профиля.');
      console.error('Update profile error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        Настройки профиля
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
      
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Avatar 
              src={user.profile_image} 
              alt={user.username}
              sx={{ width: 128, height: 128, mb: 2 }}
            />
            <Typography variant="h6" gutterBottom>
              {user.username}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Зарегистрирован: {new Date(user.created_at).toLocaleDateString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Email: {user.email}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Статус: {user.is_verified ? 'Подтвержден' : 'Не подтвержден'}
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={8}>
            <Formik
              initialValues={{
                username: user.username || '',
                full_name: user.full_name || '',
                profile_image: user.profile_image || ''
              }}
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
                    name="full_name"
                    label="Полное имя"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    error={touched.full_name && Boolean(errors.full_name)}
                    helperText={touched.full_name && errors.full_name}
                  />
                  
                  <Field
                    as={TextField}
                    name="profile_image"
                    label="URL аватара"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    error={touched.profile_image && Boolean(errors.profile_image)}
                    helperText={touched.profile_image && errors.profile_image}
                  />
                  
                  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                    <Button
                      variant="outlined"
                      onClick={() => navigate('/account/dashboard')}
                    >
                      Назад
                    </Button>
                    
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      disabled={loading}
                    >
                      {loading ? <CircularProgress size={24} /> : 'Сохранить'}
                    </Button>
                  </Box>
                </Form>
              )}
            </Formik>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default Profile; 