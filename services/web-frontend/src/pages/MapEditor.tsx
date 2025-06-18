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
  IconButton,
  Autocomplete
} from '@mui/material';
import { Add, Edit, Delete, Visibility } from '@mui/icons-material';
import GameLayout from '../components/GameLayout';
import { gameApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

interface MapTemplate {
  id: string;
  name: string;
  description?: string;
  grid_data: number[][];
  width: number;
  height: number;
  difficulty: number;
  max_players: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface MapGroup {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

interface MapChain {
  id: string;
  name: string;
  description?: string;
  map_template_ids: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
}

enum CellType {
  EMPTY = 0,
  SOLID_WALL = 1,
  BREAKABLE_BLOCK = 2,
  PLAYER_SPAWN = 3,
  ENEMY_SPAWN = 4,
  LEVEL_EXIT = 5,
}

const cellTypeColors: Record<CellType, string> = {
  [CellType.EMPTY]: '#eee',
  [CellType.SOLID_WALL]: '#555',
  [CellType.BREAKABLE_BLOCK]: '#aaa',
  [CellType.PLAYER_SPAWN]: '#00f',
  [CellType.ENEMY_SPAWN]: '#f00',
  [CellType.LEVEL_EXIT]: '#0f0',
};

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
  const [openEditDialog, setOpenEditDialog] = useState<boolean>(false);
  const [editingMap, setEditingMap] = useState<MapTemplate | null>(null);
  const [editMapError, setEditMapError] = useState<string | null>(null);

  // State for editing form fields, initialized from selectedMap when opening dialog
  const [editMapName, setEditMapName] = useState<string>('');
  const [editMapDescription, setEditMapDescription] = useState<string>('');
  const [editMapWidth, setEditMapWidth] = useState<number>(15);
  const [editMapHeight, setEditMapHeight] = useState<number>(11);
  const [editMapDifficulty, setEditMapDifficulty] = useState<number>(1);
  const [editMapMaxPlayers, setEditMapMaxPlayers] = useState<number>(4);

  // State for Map Groups
  const [mapGroups, setMapGroups] = useState<MapGroup[]>([]);
  const [openCreateGroupDialog, setOpenCreateGroupDialog] = useState<boolean>(false);
  const [newGroupName, setNewGroupName] = useState<string>('');
  const [createGroupError, setCreateGroupError] = useState<string | null>(null);
  const [openEditGroupDialog, setOpenEditGroupDialog] = useState<boolean>(false);
  const [editingGroup, setEditingGroup] = useState<MapGroup | null>(null);
  const [editGroupName, setEditGroupName] = useState<string>('');
  const [editGroupError, setEditGroupError] = useState<string | null>(null);

  // State for Map Chains
  const [mapChains, setMapChains] = useState<MapChain[]>([]);
  const [openCreateChainDialog, setOpenCreateChainDialog] = useState<boolean>(false);
  const [newChainName, setNewChainName] = useState<string>('');
  const [newChainDescription, setNewChainDescription] = useState<string>('');
  const [newChainMapTemplates, setNewChainMapTemplates] = useState<string[]>([]); // Array of selected map IDs
  const [createChainError, setCreateChainError] = useState<string | null>(null);
  const [openEditChainDialog, setOpenEditChainDialog] = useState<boolean>(false);
  const [editingChain, setEditingChain] = useState<MapChain | null>(null);
  const [editChainName, setEditChainName] = useState<string>('');
  const [editChainDescription, setEditChainDescription] = useState<string>('');
  const [editChainMapTemplates, setEditChainMapTemplates] = useState<string[]>([]);
  const [editChainError, setEditChainError] = useState<string | null>(null);

  // State for interactive map editor
  const [currentGrid, setCurrentGrid] = useState<number[][]>(
    Array.from({ length: newMapHeight }, () => Array(newMapWidth).fill(CellType.EMPTY))
  );
  const [selectedCellType, setSelectedCellType] = useState<CellType>(CellType.SOLID_WALL);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);

  useEffect(() => {
    // Initialize currentGrid when newMapWidth or newMapHeight changes for create dialog
    setCurrentGrid(Array.from({ length: newMapHeight }, () => Array(newMapWidth).fill(CellType.EMPTY)));
  }, [newMapWidth, newMapHeight]);

  const handleMouseDown = (rowIndex: number, colIndex: number) => {
    setIsDrawing(true);
    updateGridCell(rowIndex, colIndex);
  };

  const handleMouseEnter = (rowIndex: number, colIndex: number) => {
    if (isDrawing) {
      updateGridCell(rowIndex, colIndex);
    }
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const updateGridCell = (rowIndex: number, colIndex: number) => {
    setCurrentGrid(prevGrid => {
      const newGrid = prevGrid.map(row => [...row]); // Create a deep copy
      newGrid[rowIndex][colIndex] = selectedCellType;
      return newGrid;
    });
  };

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

  const fetchMapGroups = async () => {
    try {
      const response = await gameApi.get<MapGroup[]>('/maps/groups');
      setMapGroups(response.data);
    } catch (err: any) {
      console.error('Error fetching map groups:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить группы карт.');
    }
  };

  const fetchMapChains = async () => {
    try {
      const response = await gameApi.get<MapChain[]>('/maps/chains');
      setMapChains(response.data);
    } catch (err: any) {
      console.error('Error fetching map chains:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить цепочки карт.');
    }
  };

  useEffect(() => {
    fetchMapTemplates();
    fetchMapGroups();
    fetchMapChains();
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
      const response = await gameApi.post('/maps/templates', {
        name: newMapName,
        description: newMapDescription,
        width: newMapWidth,
        height: newMapHeight,
        difficulty: newMapDifficulty,
        max_players: newMapMaxPlayers,
        grid_data: currentGrid // Use the interactive grid data
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
        setCurrentGrid(Array.from({ length: 11 }, () => Array(15).fill(CellType.EMPTY))); // Reset grid
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

  const handleEditMap = (map: MapTemplate) => {
    setEditingMap(map);
    setEditMapName(map.name);
    setEditMapDescription(map.description || '');
    setEditMapWidth(map.width);
    setEditMapHeight(map.height);
    setEditMapDifficulty(map.difficulty);
    setEditMapMaxPlayers(map.max_players);
    setCurrentGrid(map.grid_data); // Load existing grid for editing
    setOpenEditDialog(true);
  };

  const handleSaveEditedMap = async () => {
    setEditMapError(null);
    if (!editMapName.trim()) {
      setEditMapError('Название карты не может быть пустым.');
      return;
    }

    try {
      const response = await gameApi.put(`/maps/templates/${editingMap?.id}`, {
        name: editMapName,
        description: editMapDescription,
        width: editMapWidth,
        height: editMapHeight,
        difficulty: editMapDifficulty,
        max_players: editMapMaxPlayers,
        grid_data: currentGrid // Save the edited grid data
      });
      if (response.data) {
        fetchMapTemplates();
        setOpenEditDialog(false);
        setEditingMap(null);
        setCurrentGrid(Array.from({ length: 11 }, () => Array(15).fill(CellType.EMPTY))); // Reset grid
      } else {
        setEditMapError(response.data.message || 'Не удалось сохранить изменения.');
      }
    } catch (err: any) {
      console.error('Error saving edited map:', err);
      setEditMapError(err.response?.data?.detail || 'Ошибка сервера при сохранении изменений.');
    }
  };

  // Map Group Handlers
  const handleCreateGroup = async () => {
    setCreateGroupError(null);
    if (!newGroupName.trim()) {
      setCreateGroupError('Название группы не может быть пустым.');
      return;
    }
    try {
      const response = await gameApi.post('/maps/groups', { name: newGroupName });
      if (response.data) {
        fetchMapGroups();
        setOpenCreateGroupDialog(false);
        setNewGroupName('');
      } else {
        setCreateGroupError(response.data.message || 'Не удалось создать группу.');
      }
    } catch (err: any) {
      console.error('Error creating group:', err);
      setCreateGroupError(err.response?.data?.detail || 'Ошибка сервера при создании группы.');
    }
  };

  const handleEditGroup = (group: MapGroup) => {
    setEditingGroup(group);
    setEditGroupName(group.name);
    setOpenEditGroupDialog(true);
  };

  const handleSaveEditedGroup = async () => {
    setEditGroupError(null);
    if (!editGroupName.trim()) {
      setEditGroupError('Название группы не может быть пустым.');
      return;
    }
    try {
      const response = await gameApi.put(`/maps/groups/${editingGroup?.id}`, { name: editGroupName });
      if (response.data) {
        fetchMapGroups();
        setOpenEditGroupDialog(false);
        setEditingGroup(null);
      } else {
        setEditGroupError(response.data.message || 'Не удалось сохранить изменения группы.');
      }
    } catch (err: any) {
      console.error('Error saving edited group:', err);
      setEditGroupError(err.response?.data?.detail || 'Ошибка сервера при сохранении изменений группы.');
    }
  };

  const handleDeleteGroup = async (groupId: string) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту группу карт?')) {
      return;
    }
    try {
      const response = await gameApi.delete(`/maps/groups/${groupId}`);
      if (response.status === 204) {
        fetchMapGroups();
      } else {
        setError(response.data?.message || 'Не удалось удалить группу.');
      }
    } catch (err: any) {
      console.error('Error deleting group:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении группы.');
    }
  };

  // Map Chain Handlers
  const handleCreateChain = async () => {
    setCreateChainError(null);
    if (!newChainName.trim()) {
      setCreateChainError('Название цепочки не может быть пустым.');
      return;
    }
    if (newChainMapTemplates.length === 0) {
      setCreateChainError('Выберите хотя бы один шаблон карты для цепочки.');
      return;
    }
    try {
      const response = await gameApi.post('/maps/chains', {
        name: newChainName,
        description: newChainDescription,
        map_ids: newChainMapTemplates,
        difficulty_progression: 1.0, // Default value, can be made editable later
      });
      if (response.data) {
        fetchMapChains();
        setOpenCreateChainDialog(false);
        setNewChainName('');
        setNewChainDescription('');
        setNewChainMapTemplates([]);
      } else {
        setCreateChainError(response.data.message || 'Не удалось создать цепочку.');
      }
    } catch (err: any) {
      console.error('Error creating chain:', err);
      setCreateChainError(err.response?.data?.detail || 'Ошибка сервера при создании цепочки.');
    }
  };

  const handleEditChain = (chain: MapChain) => {
    setEditingChain(chain);
    setEditChainName(chain.name);
    setEditChainDescription(chain.description || '');
    setEditChainMapTemplates(chain.map_template_ids);
    setOpenEditChainDialog(true);
  };

  const handleSaveEditedChain = async () => {
    setEditChainError(null);
    if (!editChainName.trim()) {
      setEditChainError('Название цепочки не может быть пустым.');
      return;
    }
    if (editChainMapTemplates.length === 0) {
      setEditChainError('Выберите хотя бы один шаблон карты для цепочки.');
      return;
    }
    try {
      const response = await gameApi.put(`/maps/chains/${editingChain?.id}`, {
        name: editChainName,
        description: editChainDescription,
        map_ids: editChainMapTemplates,
        difficulty_progression: 1.0, // Default value
      });
      if (response.data) {
        fetchMapChains();
        setOpenEditChainDialog(false);
        setEditingChain(null);
      } else {
        setEditChainError(response.data.message || 'Не удалось сохранить изменения цепочки.');
      }
    } catch (err: any) {
      console.error('Error saving edited chain:', err);
      setEditChainError(err.response?.data?.detail || 'Ошибка сервера при сохранении изменений цепочки.');
    }
  };

  const handleDeleteChain = async (chainId: string) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту цепочку карт?')) {
      return;
    }
    try {
      const response = await gameApi.delete(`/maps/chains/${chainId}`);
      if (response.status === 204) {
        fetchMapChains();
      } else {
        setError(response.data?.message || 'Не удалось удалить цепочку.');
      }
    } catch (err: any) {
      console.error('Error deleting chain:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении цепочки.');
    }
  };

  return (
    <GameLayout>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>Редактор карт</Typography>

        {loading && <CircularProgress />}
        {error && <Alert severity="error">{error}</Alert>}

        <Box sx={{ mb: 4 }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setOpenCreateDialog(true)}
            sx={{ mr: 2 }}
          >
            Создать новый шаблон карты
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setOpenCreateGroupDialog(true)}
            sx={{ mr: 2 }}
          >
            Создать новую группу карт
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setOpenCreateChainDialog(true)}
          >
            Создать новую цепочку карт
          </Button>
        </Box>

        <Typography variant="h5" gutterBottom>Существующие шаблоны карт</Typography>
        {mapTemplates.length === 0 && !loading && !error && (
          <Typography>Шаблоны карт не найдены.</Typography>
        )}
        <List>
          {mapTemplates.map((map) => (
            <Card key={map.id} sx={{ mb: 2, p: 2 }}>
              <CardContent>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={8}>
                    <Typography variant="h6">{map.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Описание: {map.description || 'Нет описания'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Размеры: {map.width}x{map.height}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Сложность: {map.difficulty}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Макс. игроков: {map.max_players}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Создан: {new Date(map.created_at).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={4} sx={{ textAlign: 'right' }}>
                    <IconButton onClick={() => handleViewDetails(map)} color="primary">
                      <Visibility />
                    </IconButton>
                    <IconButton onClick={() => handleEditMap(map)} color="secondary">
                      <Edit />
                    </IconButton>
                    <IconButton onClick={() => handleDeleteMap(map.id)} color="error">
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </List>

        {/* Map Groups Section */}
        <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>Существующие группы карт</Typography>
        {mapGroups.length === 0 && !loading && !error && (
          <Typography>Группы карт не найдены.</Typography>
        )}
        <List>
          {mapGroups.map((group) => (
            <Card key={group.id} sx={{ mb: 2, p: 2 }}>
              <CardContent>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={8}>
                    <Typography variant="h6">{group.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Создан: {new Date(group.created_at).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={4} sx={{ textAlign: 'right' }}>
                    <IconButton onClick={() => handleEditGroup(group)} color="secondary">
                      <Edit />
                    </IconButton>
                    <IconButton onClick={() => handleDeleteGroup(group.id)} color="error">
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </List>

        {/* Map Chains Section */}
        <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>Существующие цепочки карт</Typography>
        {mapChains.length === 0 && !loading && !error && (
          <Typography>Цепочки карт не найдены.</Typography>
        )}
        <List>
          {mapChains.map((chain) => (
            <Card key={chain.id} sx={{ mb: 2, p: 2 }}>
              <CardContent>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={8}>
                    <Typography variant="h6">{chain.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Описание: {chain.description || 'Нет описания'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Шаблоны карт: 
                      {chain.map_template_ids.length > 0 ? (
                        chain.map_template_ids.map(mapId => {
                          const template = mapTemplates.find(t => t.id === mapId);
                          return (
                            <Chip 
                              key={mapId} 
                              label={template ? template.name : mapId} 
                              size="small" 
                              sx={{ mr: 0.5, mb: 0.5 }}
                            />
                          );
                        })
                      ) : (
                        <Chip label="Нет шаблонов" size="small" sx={{ mr: 0.5, mb: 0.5 }}/>
                      )}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Создан: {new Date(chain.created_at).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={4} sx={{ textAlign: 'right' }}>
                    <IconButton onClick={() => handleEditChain(chain)} color="secondary">
                      <Edit />
                    </IconButton>
                    <IconButton onClick={() => handleDeleteChain(chain.id)} color="error">
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </List>

        {/* Create Map Template Dialog */}
        <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="md" fullWidth>
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
              label="Описание карты"
              type="text"
              fullWidth
              multiline
              rows={3}
              variant="outlined"
              value={newMapDescription}
              onChange={(e) => setNewMapDescription(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6}>
                <TextField
                  margin="dense"
                  label="Ширина"
                  type="number"
                  fullWidth
                  variant="outlined"
                  value={newMapWidth}
                  onChange={(e) => setNewMapWidth(Number(e.target.value))}
                  inputProps={{ min: 5, max: 50 }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  margin="dense"
                  label="Высота"
                  type="number"
                  fullWidth
                  variant="outlined"
                  value={newMapHeight}
                  onChange={(e) => setNewMapHeight(Number(e.target.value))}
                  inputProps={{ min: 5, max: 50 }}
                />
              </Grid>
            </Grid>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6}>
                <TextField
                  margin="dense"
                  label="Сложность (1-10)"
                  type="number"
                  fullWidth
                  variant="outlined"
                  value={newMapDifficulty}
                  onChange={(e) => setNewMapDifficulty(Number(e.target.value))}
                  inputProps={{ min: 1, max: 10 }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  margin="dense"
                  label="Макс. игроков (1-8)"
                  type="number"
                  fullWidth
                  variant="outlined"
                  value={newMapMaxPlayers}
                  onChange={(e) => setNewMapMaxPlayers(Number(e.target.value))}
                  inputProps={{ min: 1, max: 8 }}
                />
              </Grid>
            </Grid>
            
            {/* Cell Type Selector */}
            <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Выберите тип ячейки для рисования:</Typography>
            <Box sx={{ mb: 2 }}>
              {Object.entries(CellType)
                .filter(([key, value]) => typeof value === 'number')
                .map(([key, value]) => (
                  <Button
                    key={key}
                    variant={selectedCellType === value ? "contained" : "outlined"}
                    onClick={() => setSelectedCellType(value as CellType)}
                    sx={{ mr: 1, mb: 1 }}
                  >
                    {key.replace(/_/g, ' ').toLowerCase()}
                  </Button>
                ))}
            </Box>

            {/* Interactive Grid Editor */}
            <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Редактирование сетки карты:</Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: `repeat(${newMapWidth}, 20px)`,
                gap: '1px',
                border: '1px solid #ccc',
                width: newMapWidth * 20 + newMapWidth - 1,
                height: newMapHeight * 20 + newMapHeight - 1,
                margin: '0 auto',
                cursor: isDrawing ? 'grabbing' : 'grab',
              }}
              onMouseLeave={handleMouseUp} // Stop drawing if mouse leaves grid
            >
              {currentGrid.map((row, rowIndex) => (
                row.map((cell, colIndex) => (
                  <Box
                    key={`${rowIndex}-${colIndex}`}
                    sx={{
                      width: '20px',
                      height: '20px',
                      backgroundColor: cellTypeColors[cell as CellType],
                      border: '0.5px solid #ccc',
                    }}
                    onMouseDown={() => handleMouseDown(rowIndex, colIndex)}
                    onMouseEnter={() => handleMouseEnter(rowIndex, colIndex)}
                    onMouseUp={handleMouseUp}
                  />
                ))
              ))}
            </Box>

          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenCreateDialog(false)}>Отмена</Button>
            <Button onClick={handleCreateMap} variant="contained">Создать</Button>
          </DialogActions>
        </Dialog>

        {/* Edit Map Template Dialog */}
        <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Редактировать шаблон карты</DialogTitle>
          <DialogContent>
            {editMapError && <Alert severity="error" sx={{ mb: 2 }}>{editMapError}</Alert>}
            {editingMap && (
              <>
                <TextField
                  autoFocus
                  margin="dense"
                  label="Название карты"
                  type="text"
                  fullWidth
                  variant="outlined"
                  value={editMapName}
                  onChange={(e) => setEditMapName(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <TextField
                  margin="dense"
                  label="Описание карты"
                  type="text"
                  fullWidth
                  multiline
                  rows={3}
                  variant="outlined"
                  value={editMapDescription}
                  onChange={(e) => setEditMapDescription(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <TextField
                      margin="dense"
                      label="Ширина"
                      type="number"
                      fullWidth
                      variant="outlined"
                      value={editMapWidth}
                      onChange={(e) => setEditMapWidth(Number(e.target.value))}
                      inputProps={{ min: 5, max: 50 }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      margin="dense"
                      label="Высота"
                      type="number"
                      fullWidth
                      variant="outlined"
                      value={editMapHeight}
                      onChange={(e) => setEditMapHeight(Number(e.target.value))}
                      inputProps={{ min: 5, max: 50 }}
                    />
                  </Grid>
                </Grid>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <TextField
                      margin="dense"
                      label="Сложность (1-10)"
                      type="number"
                      fullWidth
                      variant="outlined"
                      value={editMapDifficulty}
                      onChange={(e) => setEditMapDifficulty(Number(e.target.value))}
                      inputProps={{ min: 1, max: 10 }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      margin="dense"
                      label="Макс. игроков (1-8)"
                      type="number"
                      fullWidth
                      variant="outlined"
                      value={editMapMaxPlayers}
                      onChange={(e) => setEditMapMaxPlayers(Number(e.target.value))}
                      inputProps={{ min: 1, max: 8 }}
                    />
                  </Grid>
                </Grid>

                {/* Cell Type Selector for Edit Dialog */}
                <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Выберите тип ячейки для рисования:</Typography>
                <Box sx={{ mb: 2 }}>
                  {Object.entries(CellType)
                    .filter(([key, value]) => typeof value === 'number')
                    .map(([key, value]) => (
                      <Button
                        key={key}
                        variant={selectedCellType === value ? "contained" : "outlined"}
                        onClick={() => setSelectedCellType(value as CellType)}
                        sx={{ mr: 1, mb: 1 }}
                      >
                        {key.replace(/_/g, ' ').toLowerCase()}
                      </Button>
                    ))}
                </Box>

                {/* Interactive Grid Editor for Edit Dialog */}
                <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Редактирование сетки карты:</Typography>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: `repeat(${editMapWidth}, 20px)`,
                    gap: '1px',
                    border: '1px solid #ccc',
                    width: editMapWidth * 20 + editMapWidth - 1,
                    height: editMapHeight * 20 + editMapHeight - 1,
                    margin: '0 auto',
                    cursor: isDrawing ? 'grabbing' : 'grab',
                  }}
                  onMouseLeave={handleMouseUp} // Stop drawing if mouse leaves grid
                >
                  {currentGrid.map((row, rowIndex) => (
                    row.map((cell, colIndex) => (
                      <Box
                        key={`${rowIndex}-${colIndex}`}
                        sx={{
                          width: '20px',
                          height: '20px',
                          backgroundColor: cellTypeColors[cell as CellType],
                          border: '0.5px solid #ccc',
                        }}
                        onMouseDown={() => handleMouseDown(rowIndex, colIndex)}
                        onMouseEnter={() => handleMouseEnter(rowIndex, colIndex)}
                        onMouseUp={handleMouseUp}
                      />
                    ))
                  ))}
                </Box>
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenEditDialog(false)}>Отмена</Button>
            <Button onClick={handleSaveEditedMap} variant="contained">Сохранить</Button>
          </DialogActions>
        </Dialog>

        {/* View Map Template Dialog */}
        <Dialog open={openViewDialog} onClose={handleCloseViewDialog} maxWidth="md" fullWidth>
          <DialogTitle>Просмотр шаблона карты: {selectedMap?.name}</DialogTitle>
          <DialogContent>
            {selectedMap && (
              <>
                <Typography variant="body1">Описание: {selectedMap.description || 'Нет описания'}</Typography>
                <Typography variant="body1">Размеры: {selectedMap.width}x{selectedMap.height}</Typography>
                <Typography variant="body1">Сложность: {selectedMap.difficulty}</Typography>
                <Typography variant="body1">Макс. игроков: {selectedMap.max_players}</Typography>
                <Typography variant="body1">Создан: {new Date(selectedMap.created_at).toLocaleString()}</Typography>
                
                <Typography variant="h6" sx={{ mt: 2 }}>Предварительный просмотр сетки карты:</Typography>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: `repeat(${selectedMap.width}, 20px)`,
                    gap: '1px',
                    border: '1px solid #ccc',
                    width: selectedMap.width * 20 + selectedMap.width - 1,
                    height: selectedMap.height * 20 + selectedMap.height - 1,
                    margin: '0 auto',
                  }}
                >
                  {selectedMap.grid_data.map((row: number[], rowIndex: number) => (
                    row.map((cell: number, colIndex: number) => {
                      return (
                        <Box
                          key={`${rowIndex}-${colIndex}`}
                          sx={{
                            width: '20px',
                            height: '20px',
                            backgroundColor: cellTypeColors[cell as CellType],
                            border: '0.5px solid #ccc',
                          }}
                        />
                      );
                    })
                  ))}
                </Box>
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseViewDialog}>Закрыть</Button>
          </DialogActions>
        </Dialog>

        {/* Create Map Group Dialog */}
        <Dialog open={openCreateGroupDialog} onClose={() => setOpenCreateGroupDialog(false)}>
          <DialogTitle>Создать новую группу карт</DialogTitle>
          <DialogContent>
            {createGroupError && <Alert severity="error" sx={{ mb: 2 }}>{createGroupError}</Alert>}
            <TextField
              autoFocus
              margin="dense"
              label="Название группы"
              type="text"
              fullWidth
              variant="outlined"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenCreateGroupDialog(false)}>Отмена</Button>
            <Button onClick={handleCreateGroup} variant="contained">Создать</Button>
          </DialogActions>
        </Dialog>

        {/* Edit Map Group Dialog */}
        <Dialog open={openEditGroupDialog} onClose={() => setOpenEditGroupDialog(false)}>
          <DialogTitle>Редактировать группу карт: {editingGroup?.name}</DialogTitle>
          <DialogContent>
            {editGroupError && <Alert severity="error" sx={{ mb: 2 }}>{editGroupError}</Alert>}
            {editingGroup && (
              <TextField
                autoFocus
                margin="dense"
                label="Название группы"
                type="text"
                fullWidth
                variant="outlined"
                value={editGroupName}
                onChange={(e) => setEditGroupName(e.target.value)}
              />
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenEditGroupDialog(false)}>Отмена</Button>
            <Button onClick={handleSaveEditedGroup} variant="contained">Сохранить</Button>
          </DialogActions>
        </Dialog>

        {/* Create Map Chain Dialog */}
        <Dialog open={openCreateChainDialog} onClose={() => setOpenCreateChainDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Создать новую цепочку карт</DialogTitle>
          <DialogContent>
            {createChainError && <Alert severity="error" sx={{ mb: 2 }}>{createChainError}</Alert>}
            <TextField
              autoFocus
              margin="dense"
              label="Название цепочки"
              type="text"
              fullWidth
              variant="outlined"
              value={newChainName}
              onChange={(e) => setNewChainName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Описание цепочки"
              type="text"
              fullWidth
              multiline
              rows={3}
              variant="outlined"
              value={newChainDescription}
              onChange={(e) => setNewChainDescription(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Autocomplete
              multiple
              id="map-templates-for-chain"
              options={mapTemplates}
              getOptionLabel={(option) => option.name}
              value={mapTemplates.filter(template => newChainMapTemplates.includes(template.id))}
              onChange={(event, newValue) => {
                setNewChainMapTemplates(newValue.map(template => template.id));
              }}
              renderInput={(params) => (
                <TextField {...params} variant="outlined" label="Выберите шаблоны карт" placeholder="Шаблоны карт" />
              )}
              sx={{ mb: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenCreateChainDialog(false)}>Отмена</Button>
            <Button onClick={handleCreateChain} variant="contained">Создать</Button>
          </DialogActions>
        </Dialog>

        {/* Edit Map Chain Dialog */}
        <Dialog open={openEditChainDialog} onClose={() => setOpenEditChainDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Редактировать цепочку карт: {editingChain?.name}</DialogTitle>
          <DialogContent>
            {editChainError && <Alert severity="error" sx={{ mb: 2 }}>{editChainError}</Alert>}
            {editingChain && (
              <>
                <TextField
                  autoFocus
                  margin="dense"
                  label="Название цепочки"
                  type="text"
                  fullWidth
                  variant="outlined"
                  value={editChainName}
                  onChange={(e) => setEditChainName(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <TextField
                  margin="dense"
                  label="Описание цепочки"
                  type="text"
                  fullWidth
                  multiline
                  rows={3}
                  variant="outlined"
                  value={editChainDescription}
                  onChange={(e) => setEditChainDescription(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <Autocomplete
                  multiple
                  id="edit-map-templates-for-chain"
                  options={mapTemplates}
                  getOptionLabel={(option) => option.name}
                  value={mapTemplates.filter(template => editChainMapTemplates.includes(template.id))}
                  onChange={(event, newValue) => {
                    setEditChainMapTemplates(newValue.map(template => template.id));
                  }}
                  renderInput={(params) => (
                    <TextField {...params} variant="outlined" label="Выберите шаблоны карт" placeholder="Шаблоны карт" />
                  )}
                  sx={{ mb: 2 }}
                />
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenEditChainDialog(false)}>Отмена</Button>
            <Button onClick={handleSaveEditedChain} variant="contained">Сохранить</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </GameLayout>
  );
};

export default MapEditor; 