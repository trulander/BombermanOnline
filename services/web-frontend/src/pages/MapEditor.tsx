import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton
} from '@mui/material';
import { Add, Edit, Delete, Visibility } from '@mui/icons-material';
import GameLayout from '../components/GameLayout';
import { gameApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

interface MapTemplate {
  id: string;
  name: string;
  description?: string;
  grid: string[][];
  width: number;
  height: number;
  difficulty: number;
  max_players: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

const MapEditor: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [mapTemplates, setMapTemplates] = useState<MapTemplate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMap, setSelectedMap] = useState<MapTemplate | null>(null);
  const [openViewDialog, setOpenViewDialog] = useState<boolean>(false);
  const [openCreateDialog, setOpenCreateDialog] = useState<boolean>(false);
  const [newMapName, setNewMapName] = useState<string>('');
  const [newMapDescription, setNewMapDescription] = useState<string>('');
  const [newMapWidth, setNewMapWidth] = useState<number>(15);
  const [newMapHeight, setNewMapHeight] = useState<number>(11);
  const [newMapDifficulty, setNewMapDifficulty] = useState<number>(1);
  const [newMapMaxPlayers, setNewMapMaxPlayers] = useState<number>(4);
  const [createMapError, setCreateMapError] = useState<string | null>(null);

  const fetchMapTemplates = async () => {
    try {
      setLoading(true);
      const response = await gameApi.get<MapTemplate[]>('/maps/templates');
      setMapTemplates(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching map templates:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить шаблоны карт.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMapTemplates();
  }, []);

  const handleViewDetails = (map: MapTemplate) => {
    setSelectedMap(map);
    setOpenViewDialog(true);
  };

  const handleCloseViewDialog = () => {
    setOpenViewDialog(false);
    setSelectedMap(null);
  };

  const handleCreateMap = async () => {
    setCreateMapError(null);
    if (!newMapName.trim()) {
      setCreateMapError('Название карты не может быть пустым.');
      return;
    }

    try {
      const initialGrid: string[][] = Array.from({ length: newMapHeight }, () => 
        Array.from({ length: newMapWidth }, () => 'wall')
      );
      const response = await gameApi.post('/maps/templates', {
        name: newMapName,
        description: newMapDescription,
        width: newMapWidth,
        height: newMapHeight,
        difficulty: newMapDifficulty,
        max_players: newMapMaxPlayers,
        grid: initialGrid
      });
      if (response.data) {
        fetchMapTemplates();
        setOpenCreateDialog(false);
        setNewMapName('');
        setNewMapDescription('');
        setNewMapWidth(15);
        setNewMapHeight(11);
        setNewMapDifficulty(1);
        setNewMapMaxPlayers(4);
      } else {
        setCreateMapError(response.data.message || 'Не удалось создать карту.');
      }
    } catch (err: any) {
      console.error('Error creating map:', err);
      setCreateMapError(err.response?.data?.detail || 'Ошибка сервера при создании карты.');
    }
  };

  const handleDeleteMap = async (mapId: string) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот шаблон карты?')) {
      return;
    }
    try {
      const response = await gameApi.delete(`/maps/templates/${mapId}`);
      if (response.status === 204) {
        fetchMapTemplates();
      } else {
        setError(response.data?.message || 'Не удалось удалить карту.');
      }
    } catch (err: any) {
      console.error('Error deleting map:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении карты.');
    }
  };

  if (loading) {
    return (
      <GameLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>Загрузка шаблонов карт...</Typography>
        </Box>
      </GameLayout>
    );
  }

  return (
    <GameLayout>
      <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
        <Typography component="h1" variant="h4" gutterBottom align="center">
          Редактор карт
        </Typography>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Button 
          variant="contained" 
          startIcon={<Add />} 
          onClick={() => setOpenCreateDialog(true)}
          sx={{ mb: 3 }}
        >
          Создать новый шаблон карты
        </Button>

        {mapTemplates.length === 0 ? (
          <Typography variant="body1" color="text.secondary">Нет доступных шаблонов карт.</Typography>
        ) : (
          <Grid container spacing={2}>
            {mapTemplates.map((map) => (
              <Grid item xs={12} sm={6} md={4} key={map.id}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6">{map.name}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{map.description}</Typography>
                    <Chip label={`Ширина: ${map.width}`} size="small" sx={{ mr: 1 }} />
                    <Chip label={`Высота: ${map.height}`} size="small" sx={{ mr: 1 }} />
                    <Chip label={`Сложность: ${map.difficulty}`} size="small" sx={{ mr: 1 }} />
                    <Chip label={`Игроков: ${map.max_players}`} size="small" />
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Button variant="outlined" size="small" startIcon={<Visibility />} onClick={() => handleViewDetails(map)}>
                        Просмотр
                      </Button>
                      <IconButton size="small" onClick={() => alert('Функция редактирования пока не реализована')}><Edit /></IconButton>
                      <IconButton size="small" onClick={() => handleDeleteMap(map.id)}><Delete /></IconButton>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

      </Box>

      {/* View Map Details Dialog */}
      <Dialog open={openViewDialog} onClose={handleCloseViewDialog} maxWidth="md" fullWidth>
        <DialogTitle>{selectedMap?.name} (ID: {selectedMap?.id})</DialogTitle>
        <DialogContent>
          {selectedMap && (
            <Box>
              <Typography variant="body1"><strong>Описание:</strong> {selectedMap.description || 'Нет описания'}</Typography>
              <Typography variant="body1"><strong>Размеры:</strong> {selectedMap.width}x{selectedMap.height}</Typography>
              <Typography variant="body1"><strong>Сложность:</strong> {selectedMap.difficulty}</Typography>
              <Typography variant="body1"><strong>Макс. игроков:</strong> {selectedMap.max_players}</Typography>
              <Typography variant="body2" color="text.secondary">Создана: {new Date(selectedMap.created_at).toLocaleString()}</Typography>
              <Typography variant="body2" color="text.secondary">Создана пользователем: {selectedMap.created_by}</Typography>
              
              <Typography variant="h6" sx={{ mt: 2 }}>Предварительный просмотр сетки карты:</Typography>
              <Box sx={{ 
                border: '1px solid #ccc', 
                p: 1, 
                mt: 1, 
                overflow: 'auto', 
                maxHeight: '400px',
                fontFamily: 'monospace',
                fontSize: '12px'
              }}>
                {selectedMap.grid.map((row, rowIndex) => (
                  <div key={rowIndex} style={{ whiteSpace: 'pre' }}>
                    {row.map((cell, colIndex) => (
                      <span 
                        key={colIndex} 
                        style={{
                          backgroundColor: cell === 'wall' ? '#888' : 
                                           cell === 'empty' ? '#eee' : 
                                           cell === 'start' ? '#afa' : 
                                           '#fff',
                          color: '#000',
                          width: '12px',
                          height: '12px',
                          display: 'inline-block',
                          textAlign: 'center',
                          lineHeight: '12px',
                          border: '1px solid #ddd'
                        }}
                      >{cell === 'wall' ? '#' : cell === 'empty' ? '.' : 'S'}</span>
                    ))}
                  </div>
                ))}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseViewDialog}>Закрыть</Button>
        </DialogActions>
      </Dialog>

      {/* Create New Map Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)}>
        <DialogTitle>Создать новый шаблон карты</DialogTitle>
        <DialogContent>
          {createMapError && <Alert severity="error" sx={{ mb: 2 }}>{createMapError}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="Название карты"
            type="text"
            fullWidth
            variant="outlined"
            value={newMapName}
            onChange={(e) => setNewMapName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Описание карты (опционально)"
            type="text"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newMapDescription}
            onChange={(e) => setNewMapDescription(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Ширина (1-50)"
            type="number"
            fullWidth
            variant="outlined"
            value={newMapWidth}
            onChange={(e) => setNewMapWidth(parseInt(e.target.value))}
            inputProps={{ min: 1, max: 50 }}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Высота (1-50)"
            type="number"
            fullWidth
            variant="outlined"
            value={newMapHeight}
            onChange={(e) => setNewMapHeight(parseInt(e.target.value))}
            inputProps={{ min: 1, max: 50 }}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Сложность (1-10)"
            type="number"
            fullWidth
            variant="outlined"
            value={newMapDifficulty}
            onChange={(e) => setNewMapDifficulty(parseInt(e.target.value))}
            inputProps={{ min: 1, max: 10 }}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Макс. игроков (1-8)"
            type="number"
            fullWidth
            variant="outlined"
            value={newMapMaxPlayers}
            onChange={(e) => setNewMapMaxPlayers(parseInt(e.target.value))}
            inputProps={{ min: 1, max: 8 }}
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Отмена</Button>
          <Button onClick={handleCreateMap} variant="contained" color="primary">Создать</Button>
        </DialogActions>
      </Dialog>
    </GameLayout>
  );
};

export default MapEditor; 