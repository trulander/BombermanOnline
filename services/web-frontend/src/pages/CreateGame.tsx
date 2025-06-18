import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  CircularProgress,
  Alert,
  MenuItem,
  Select,
  InputLabel,
  FormControl
} from '@mui/material';
import GameLayout from '../components/GameLayout';
import { gameApi, webApi } from '../services/api';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';

interface EntitiesInfo {
  game_modes: { [key: string]: string };
  // Add other entity types if needed for future features
}

interface MapTemplate {
  id: string;
  name: string;
}

interface GameCreateSettings {
  game_mode: string;
  max_players: number;
  name?: string;
  map_template_id?: string;
}

const validationSchema = Yup.object().shape({
  game_mode: Yup.string().required('Режим игры обязателен'),
  max_players: Yup.number()
    .min(2, 'Минимум 2 игрока')
    .max(8, 'Максимум 8 игроков')
    .required('Максимум игроков обязателен'),
  name: Yup.string().max(50, 'Название не может быть длиннее 50 символов'),
  map_template_id: Yup.string().optional()
});

const CreateGame: React.FC = () => {
  const navigate = useNavigate();
  const [entitiesInfo, setEntitiesInfo] = useState<EntitiesInfo | null>(null);
  const [mapTemplates, setMapTemplates] = useState<MapTemplate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [entitiesResponse, mapsResponse] = await Promise.all([
          gameApi.get<EntitiesInfo>('/entities/info'),
          gameApi.get<MapTemplate[]>('/maps/templates')
        ]);
        setEntitiesInfo(entitiesResponse.data);
        setMapTemplates(mapsResponse.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching initial data:', err);
        setError('Не удалось загрузить необходимые данные (режимы игры, карты). Пожалуйста, попробуйте позже.');
        setLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  const handleSubmit = async (values: GameCreateSettings) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    console.log('Attempting to create game with values:', values);

    try {
      const response = await webApi.post('/games', values);
      if (response.data && response.data.game_id) {
        setSuccess('Игра успешно создана!');
        // Redirect to the actual game page to join it
        navigate(`/account/game/${response.data.game_id}`);
      } else {
        setError(response.data?.message || 'Не удалось создать игру.');
      }
    } catch (err: any) {
      console.error('Error creating game:', err);
      setError(err.response?.data?.detail || 'Произошла ошибка при создании игры.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && (!entitiesInfo || mapTemplates.length === 0)) {
    return (
      <GameLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>Загрузка данных...</Typography>
        </Box>
      </GameLayout>
    );
  }

  return (
    <GameLayout>
      <Box sx={{ maxWidth: 600, mx: 'auto', p: 3, bgcolor: 'background.paper', borderRadius: 2, boxShadow: 3 }}>
        <Typography component="h1" variant="h4" align="center" gutterBottom>
          Создать новую игру
        </Typography>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <Formik
          initialValues={{
            game_mode: '',
            max_players: 4,
            name: '',
            map_template_id: '',
          }}
          validationSchema={validationSchema}
          onSubmit={handleSubmit}
        >
          {({ errors, touched, values, handleChange }) => (
            <Form>
              <FormControl fullWidth margin="normal" error={touched.game_mode && Boolean(errors.game_mode)}>
                <InputLabel id="game-mode-label">Режим игры</InputLabel>
                <Field
                  as={Select}
                  labelId="game-mode-label"
                  id="game_mode"
                  name="game_mode"
                  label="Режим игры"
                  value={values.game_mode}
                  onChange={handleChange}
                >
                  {entitiesInfo?.game_modes && Object.keys(entitiesInfo.game_modes).map((mode) => (
                    <MenuItem key={mode} value={entitiesInfo.game_modes[mode]}>
                      {entitiesInfo.game_modes[mode]}
                    </MenuItem>
                  ))}
                </Field>
                {touched.game_mode && errors.game_mode && (
                  <Typography variant="caption" color="error">{errors.game_mode}</Typography>
                )}
              </FormControl>

              <Field
                as={TextField}
                name="max_players"
                label="Максимум игроков"
                type="number"
                variant="outlined"
                fullWidth
                margin="normal"
                error={touched.max_players && Boolean(errors.max_players)}
                helperText={touched.max_players && errors.max_players}
              />

              <Field
                as={TextField}
                name="name"
                label="Название игры (опционально)"
                variant="outlined"
                fullWidth
                margin="normal"
                error={touched.name && Boolean(errors.name)}
                helperText={touched.name && errors.name}
              />
              
              <FormControl fullWidth margin="normal" error={touched.map_template_id && Boolean(errors.map_template_id)}>
                <InputLabel id="map-template-label">Шаблон карты (опционально)</InputLabel>
                <Field
                  as={Select}
                  labelId="map-template-label"
                  id="map_template_id"
                  name="map_template_id"
                  label="Шаблон карты (опционально)"
                  value={values.map_template_id}
                  onChange={handleChange}
                >
                  <MenuItem value=""><em>Без выбора</em></MenuItem>
                  {mapTemplates.map((map) => (
                    <MenuItem key={map.id} value={map.id}>
                      {map.name}
                    </MenuItem>
                  ))}
                </Field>
                {touched.map_template_id && errors.map_template_id && (
                  <Typography variant="caption" color="error">{errors.map_template_id}</Typography>
                )}
              </FormControl>

              <Button
                type="submit"
                fullWidth
                variant="contained"
                color="primary"
                disabled={loading}
                sx={{ mt: 3, mb: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Создать игру'}
              </Button>
            </Form>
          )}
        </Formik>
      </Box>
    </GameLayout>
  );
};

export default CreateGame; 