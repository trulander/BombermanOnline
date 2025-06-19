import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  SelectChangeEvent,
  TextField,
  Typography
} from '@mui/material';
import {
  Add,
  Delete,
  Done,
  Edit,
  GroupAdd,
  Pause,
  People,
  PlayArrow,
  Refresh,
  Remove,
  SportsEsports
} from '@mui/icons-material';
import {getProxiedGameApi} from '../services/api';
import {useAuth} from '../context/AuthContext';
import {GameInfo, GameModeType, GameStatus, GameTeamInfo, ManageGameProps, MapTemplate, UnitType} from "../types/Game"; // Corrected: CellType is a named export

const ManageGame: React.FC<ManageGameProps> = ({ gameId, isModalOpen }) => {
  console.log('ManageGame: Component Rendered'); // Log on every render

  const navigate = useNavigate();
  const { user } = useAuth();

  // Initialize proxiedGameApi here, as it depends on gameId
  const proxiedGameApi = useMemo(() => {
    console.log('ManageGame: Recalculating proxiedGameApi. gameId:', gameId); // Log when useMemo re-calculates
    return gameId ? getProxiedGameApi(gameId) : null;
  }, [gameId]);

  const [game, setGame] = useState<GameInfo | null>(null);
  const [mapTemplates, setMapTemplates] = useState<MapTemplate[]>([]);
  const [initialLoading, setInitialLoading] = useState<boolean>(!isModalOpen); // If modal is open, assume initial loading is handled by parent or not needed
  const [isUpdating, setIsUpdating] = useState<boolean>(false); // For background updates
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [openAddPlayerDialog, setOpenAddPlayerDialog] = useState(false);
  const [addPlayerId, setAddPlayerId] = useState<string>('');
  const [addPlayerUnitType, setAddPlayerUnitType] = useState<UnitType>(UnitType.BOMBERMAN);
  const [addPlayerError, setAddPlayerError] = useState<string | null>(null);
  
  const [playerUnitType, setPlayerUnitType] = useState<UnitType>(UnitType.BOMBERMAN); // Current player's unit type
  const [isPlayerInThisGame, setIsPlayerInThisGame] = useState<boolean>(false); // Is current user in THIS game

  const [openCreateTeamDialog, setOpenCreateTeamDialog] = useState(false);
  const [newTeamName, setNewTeamName] = useState<string>('');
  const [createTeamError, setCreateTeamError] = useState<string | null>(null);

  const [openEditTeamDialog, setOpenEditTeamDialog] = useState<boolean>(false);
  const [editTeamId, setEditTeamId] = useState<string | null>(null);
  const [editTeamName, setEditTeamName] = useState<string>('');
  const [editTeamError, setEditTeamError] = useState<string | null>(null);

  const [selectedMapTemplateId, setSelectedMapTemplateId] = useState<string>('');
  const [displayedMapGrid, setDisplayedMapGrid] = useState<number[][] | null>(null); // New state for map preview

  const fetchGameDetails = useCallback(async () => {
    console.log('ManageGame: fetchGameDetails called'); // Log every time fetchGameDetails is called
    if (!gameId || !proxiedGameApi) {
      console.warn('ManageGame: fetchGameDetails skipped - gameId or proxiedGameApi not initialized.', { gameId, proxiedGameApi });
      setError('Идентификатор игры или прокси API не инициализирован.');
      // No setInitialLoading(false) here, as it's an error, not a successful load
      return;
    }

    // Set isUpdating true for all fetches (including initial one, but initialLoading takes precedence)
    setIsUpdating(true);
    try {
      const [gameResponse, mapsResponse] = await Promise.all([
        proxiedGameApi.get<GameInfo>(`/games/${gameId}`),
        proxiedGameApi.get<MapTemplate[]>('/maps/templates') // Also proxy map templates when fetched in game context
      ]);
      setGame(gameResponse.data);
      setMapTemplates(mapsResponse.data);

      if (gameResponse.data.settings.map_template_id) {
        setSelectedMapTemplateId(gameResponse.data.settings.map_template_id);
        const map = mapsResponse.data.find(m => m.id === gameResponse.data.settings.map_template_id);
        if (map) {
          setDisplayedMapGrid(map.grid_data);
        }
      } else {
        setSelectedMapTemplateId(''); // Clear selection if no template is set
        setDisplayedMapGrid(null); // Clear map preview
      }

      setError(null);
    } catch (err: any) {
      console.error('ManageGame: Error fetching game details or map templates:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить информацию об игре или шаблоны карт.');
    } finally {
      // Only set initialLoading to false if we weren't already in a modal context
      if (!isModalOpen) {
          setInitialLoading(false);
      }
      setIsUpdating(false); // Always set false after fetch attempt
    }
  }, [gameId, proxiedGameApi, setGame, setMapTemplates, setSelectedMapTemplateId, setError, isModalOpen]);

  // Effect to determine if the current user is in the game and their unit type
  useEffect(() => {
    if (user && game && game.players) {
      const currentPlayer = game.players.find(p => p.id === user.id);
      if (currentPlayer) {
        setIsPlayerInThisGame(true);
        setPlayerUnitType(currentPlayer.unit_type);
      } else {
        setIsPlayerInThisGame(false);
        setPlayerUnitType(UnitType.BOMBERMAN); // Reset to default if not in game
      }
    }
  }, [user, game]);

  useEffect(() => {
    console.log('ManageGame: useEffect ran. proxiedGameApi:', !!proxiedGameApi, 'fetchGameDetails:', !!fetchGameDetails); // Log when useEffect runs
    if (proxiedGameApi) {
      fetchGameDetails();
      const interval = setInterval(() => {
        console.log('ManageGame: setInterval triggered fetchGameDetails'); // Log when setInterval triggers
        fetchGameDetails();
      }, 5000); // Обновлять каждые 5 секунд
      return () => {
        console.log('ManageGame: useEffect cleanup. Clearing interval.'); // Log when cleanup runs
        clearInterval(interval);
      };
    }
  }, [proxiedGameApi, fetchGameDetails]); // Updated dependencies

  const updateMapTemplate = async (newMapId: string) => {
    if (!gameId || !proxiedGameApi) return;

    try {
      setSuccess(null);
      setError(null);
      await proxiedGameApi.put(`/games/${gameId}/settings`, { map_template_id: newMapId });
      setSuccess('Шаблон карты успешно обновлен!');
      fetchGameDetails(); // Refresh to show updated map details
    } catch (err: any) {
      console.error('Error updating map template:', err);
      setError(err.response?.data?.detail || 'Не удалось обновить шаблон карты.');
    }
  };

  const handleMapTemplateChange = (event: SelectChangeEvent<string>) => {
    const newMapId = event.target.value;
    setSelectedMapTemplateId(newMapId);
    updateMapTemplate(newMapId); // Call the async function
  };

  const handleGameAction = async (action: 'start' | 'pause' | 'resume') => {
    if (!proxiedGameApi) return;
    try {
      const response = await proxiedGameApi.put(`/games/${gameId}/status`, { action });
      if (response.data.success) {
        fetchGameDetails(); // Refresh game state
      } else {
        setError(response.data.message || `Не удалось выполнить действие: ${action}`);
      }
    } catch (err: any) {
      console.error(`Error performing game action ${action}:`, err);
      setError(err.response?.data?.detail || 'Ошибка сервера при изменении статуса игры.');
    }
  };

  const handleDeleteGame = async () => {
    if (!gameId || !proxiedGameApi) return;
    if (!window.confirm('Вы уверены, что хотите удалить эту игру? Это действие необратимо.')) {
      return;
    }
    try {
      const response = await proxiedGameApi.delete(`/games/${gameId}`);
      if (response.data.success) {
        navigate('/account/dashboard'); // Redirect after deletion
      } else {
        setError(response.data.message || 'Не удалось удалить игру.');
      }
    } catch (err: any) {
      console.error('Error deleting game:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении игры.');
    }
  };

  const handleAddPlayer = async () => {
    setAddPlayerError(null);
    if (!proxiedGameApi) return;
    try {
      const response = await proxiedGameApi.post(`/games/${gameId}/players`, {
        player_id: addPlayerId,
        unit_type: addPlayerUnitType
      });
      if (response.data) {
        setAddPlayerId('');
        setAddPlayerUnitType(UnitType.BOMBERMAN);
        setOpenAddPlayerDialog(false);
        setSuccess('Игрок успешно добавлен!');
        fetchGameDetails(); // Refresh players list
      } else {
        setAddPlayerError(response.data.message || 'Не удалось добавить игрока.');
      }
    } catch (err: any) {
      console.error('Error adding player:', err);
      setAddPlayerError(err.response?.data?.detail || 'Ошибка сервера при добавлении игрока.');
    }
  };

  const handleRemovePlayer = async (playerId: string) => {
    if (!gameId || !proxiedGameApi) return;
    if (!window.confirm('Вы уверены, что хотите удалить этого игрока из игры?')) {
      return;
    }
    try {
      const response = await proxiedGameApi.delete(`/games/${gameId}/players/${playerId}`);
      if (response.data.success) {
        setSuccess('Игрок успешно удален!');
        fetchGameDetails(); // Refresh players list
      } else {
        setError(response.data.message || 'Не удалось удалить игрока.');
      }
    } catch (err: any) {
      console.error('Error removing player:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении игрока.');
    }
  };

  // Handle adding current authenticated user to game
  const handleAddSelfToGame = async () => {
    if (!proxiedGameApi || !user?.id) return;
    setSuccess(null);
    setError(null);
    try {
      const response = await proxiedGameApi.post(`/games/${gameId}/players`, {
        player_id: user.id,
        unit_type: playerUnitType
      });
      if (response.data.success) {
        setSuccess('Вы успешно присоединились к игре!');
        fetchGameDetails();
      } else {
        setError(response.data.message || 'Не удалось присоединиться к игре.');
      }
    } catch (err: any) {
      console.error('Error adding self to game:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при присоединении к игре.');
    }
  };

  // Handle removing current authenticated user from game
  const handleRemoveSelfFromGame = async () => {
    if (!gameId || !proxiedGameApi || !user?.id) return;
    if (!window.confirm('Вы уверены, что хотите покинуть игру?')) {
      return;
    }
    setSuccess(null);
    setError(null);
    try {
      const response = await proxiedGameApi.delete(`/games/${gameId}/players/${user.id}`);
      if (response.data.success) {
        setSuccess('Вы успешно покинули игру!');
        fetchGameDetails();
      } else {
        setError(response.data.message || 'Не удалось покинуть игру.');
      }
    } catch (err: any) {
      console.error('Error removing self from game:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при выходе из игры.');
    }
  };

  // Handle changing current user's unit type
  const handleChangeUnitType = async () => {
    if (!gameId || !proxiedGameApi || !user?.id) return;
    setSuccess(null);
    setError(null);
    try {
      // 1. Remove player
      const removeResponse = await proxiedGameApi.delete(`/games/${gameId}/players/${user.id}`);
      if (!removeResponse.data.success) {
        throw new Error(removeResponse.data.message || 'Не удалось удалить игрока для смены типа.');
      }

      // 2. Add player with new unit type
      const addResponse = await proxiedGameApi.post(`/games/${gameId}/players`, {
        player_id: user.id,
        unit_type: playerUnitType
      });

      if (addResponse.data.success) {
        setSuccess('Тип юнита успешно изменен!');
        fetchGameDetails();
      } else {
        setError(addResponse.data.message || 'Не удалось добавить игрока с новым типом.');
      }
    } catch (err: any) {
      console.error('Error changing unit type:', err);
      setError(err.message || err.response?.data?.detail || 'Ошибка сервера при смене типа юнита.');
    }
  };

  const handleCreateTeam = async () => {
    setCreateTeamError(null);
    if (!proxiedGameApi) return;
    try {
      const response = await proxiedGameApi.post(`/games/${gameId}/teams`, { name: newTeamName });
      if (response.data) {
        setNewTeamName('');
        setOpenCreateTeamDialog(false);
        setSuccess('Команда успешно создана!');
        fetchGameDetails(); // Refresh teams list
      } else {
        setCreateTeamError(response.data.message || 'Не удалось создать команду.');
      }
    } catch (err: any) {
      console.error('Error creating team:', err);
      setCreateTeamError(err.response?.data?.detail || 'Ошибка сервера при создании команды.');
    }
  };

  const handleEditTeamClick = (team: GameTeamInfo) => {
    setEditTeamId(team.id);
    setEditTeamName(team.name);
    setOpenEditTeamDialog(true);
  };

  const handleUpdateTeam = async () => {
    setEditTeamError(null);
    if (!editTeamId || !proxiedGameApi) return;
    if (!editTeamName.trim()) {
      setEditTeamError('Название команды не может быть пустым.');
      return;
    }
    try {
      const response = await proxiedGameApi.put(`/games/${gameId}/teams/${editTeamId}`, { name: editTeamName });
      if (response.data) {
        setOpenEditTeamDialog(false);
        setEditTeamId(null);
        setEditTeamName('');
        setSuccess('Команда успешно обновлена!');
        fetchGameDetails(); // Refresh teams list
      } else {
        setEditTeamError(response.data.message || 'Не удалось обновить команду.');
      }
    } catch (err: any) {
      console.error('Error updating team:', err);
      setEditTeamError(err.response?.data?.detail || 'Ошибка сервера при обновлении команды.');
    }
  };

  const handleDeleteTeam = async (teamId: string) => {
    if (!gameId || !proxiedGameApi) return;
    if (!window.confirm('Вы уверены, что хотите удалить эту команду?')) {
      return;
    }
    try {
      const response = await proxiedGameApi.delete(`/games/${gameId}/teams/${teamId}`);
      if (response.data.success) {
        setSuccess('Команда успешно удалена!');
        fetchGameDetails(); // Refresh teams list
      } else {
        setError(response.data.message || 'Не удалось удалить команду.');
      }
    } catch (err: any) {
      console.error('Error deleting team:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении команды.');
    }
  };

  const handleAddPlayerToTeam = async (teamId: string, playerId: string) => {
    if (!gameId || !proxiedGameApi) return;
    try {
      const response = await proxiedGameApi.post(`/games/${gameId}/teams/${teamId}/players`, { player_id: playerId });
      if (response.data) {
        setSuccess(`Игрок ${playerId} добавлен в команду ${teamId} успешно!`);
        fetchGameDetails();
      } else {
        setError(response.data.message || 'Не удалось добавить игрока в команду.');
      }
    } catch (err: any) {
      console.error('Error adding player to team:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при добавлении игрока в команду.');
    }
  };

  const handleRemovePlayerFromTeam = async (teamId: string, playerId: string) => {
    if (!gameId || !proxiedGameApi) return;
    try {
      const response = await proxiedGameApi.delete(`/games/${gameId}/teams/${teamId}/players/${playerId}`);
      if (response.data.success) {
        setSuccess(`Игрок ${playerId} удален из команды ${teamId} успешно!`);
        fetchGameDetails();
      } else {
        setError(response.data.message || 'Не удалось удалить игрока из команды.');
      }
    } catch (err: any) {
      console.error('Error removing player from team:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении игрока из команды.');
    }
  };

  const handleDistributePlayers = async (redistributeExisting: boolean) => {
    if (!gameId || !proxiedGameApi) return;
    try {
      const response = await proxiedGameApi.post(`/games/${gameId}/teams/distribute`, { redistribute_existing: redistributeExisting });
      if (response.data.success) {
        setSuccess('Игроки успешно распределены по командам!');
        fetchGameDetails();
      } else {
        setError(response.data.message || 'Не удалось распределить игроков.');
      }
    } catch (err: any) {
      console.error('Error distributing players:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при распределении игроков.');
    }
  };

  const handleValidateTeams = async () => {
    if (!gameId || !proxiedGameApi) return;
    try {
      const response = await proxiedGameApi.post(`/games/${gameId}/teams/validate`);
      if (response.data.is_valid) {
        setSuccess('Распределение команд валидно!');
      } else {
        setError(response.data.message || 'Распределение команд не валидно.');
      }
    } catch (err: any) {
      console.error('Error validating teams:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при валидации команд.');
    }
  };

  const handleStartGame = () => {
    handleGameAction('start');
  };

  const handlePauseGame = () => {
    handleGameAction('pause');
  };

  const handleResumeGame = () => {
    handleGameAction('resume');
  };

  if (initialLoading && !isModalOpen) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '500px',
        p: 3,
        maxWidth: 1200,
        mx: 'auto'
      }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>Загрузка данных игры...</Typography>
      </Box>
    );
  }

  // Render nothing if game is null after initial loading, or show error
  if (!game) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '500px',
        p: 3,
        maxWidth: 1200,
        mx: 'auto'
      }}>
        <Alert severity="info">Данные игры недоступны или игра была удалена.</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{
      p: 3,
      maxWidth: 1200,
      mx: 'auto',
      minHeight: isModalOpen ? 'auto' : '500px', // Maintain min-height only if not in modal
      position: 'relative',
      opacity: isUpdating ? 0.7 : 1, // Add semi-transparent overlay when updating
      pointerEvents: isUpdating ? 'none' : 'auto', // Disable interactions when updating
    }}>
      {isUpdating && (
        <Box sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.7)',
          zIndex: 10, // Ensure it's on top
        }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>Обновление данных игры...</Typography>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Grid container spacing={3}>

        {/* Блок: Ваше участие в игре */}
        <Grid item xs={12}>
          <Card raised>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <People sx={{ verticalAlign: 'middle', mr: 1 }} /> Ваше участие в игре
              </Typography>
              {!user ? (
                <Typography variant="body1" color="text.secondary">
                  Пожалуйста, <a href="/account/login">войдите</a>, чтобы присоединиться к игре.
                </Typography>
              ) : (
                <Box>
                  {isPlayerInThisGame ? (
                    <Box>
                      <Typography variant="body1">Вы в игре как <Chip label={playerUnitType.toUpperCase()} color="primary" size="small" />
                      </Typography>
                      <FormControl fullWidth margin="normal">
                        <InputLabel id="change-unit-type-label">Сменить тип юнита</InputLabel>
                        <Select
                          labelId="change-unit-type-label"
                          value={playerUnitType}
                          label="Сменить тип юнита"
                          onChange={(e: SelectChangeEvent<UnitType>) => setPlayerUnitType(e.target.value as UnitType)}
                          disabled={game?.status !== GameStatus.PENDING}
                        >
                          {Object.values(UnitType).map((type) => (
                            <MenuItem key={type} value={type}>
                              {type.charAt(0).toUpperCase() + type.slice(1)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleChangeUnitType}
                        startIcon={<SportsEsports />}
                        sx={{ mr: 1 }}
                        disabled={game?.status !== GameStatus.PENDING}
                      >
                        Сменить тип юнита
                      </Button>
                      <Button
                        variant="outlined"
                        color="secondary"
                        onClick={handleRemoveSelfFromGame}
                        startIcon={<Remove />}
                        disabled={game?.status !== GameStatus.PENDING}
                      >
                        Покинуть игру
                      </Button>
                    </Box>
                  ) : (
                    <Box>
                      <Typography variant="body1" color="text.secondary">Вы не участвуете в этой игре.</Typography>
                      <FormControl fullWidth margin="normal">
                        <InputLabel id="join-unit-type-label">Выбрать тип юнита</InputLabel>
                        <Select
                          labelId="join-unit-type-label"
                          value={playerUnitType}
                          label="Выбрать тип юнита"
                          onChange={(e: SelectChangeEvent<UnitType>) => setPlayerUnitType(e.target.value as UnitType)}
                          disabled={game?.status !== GameStatus.PENDING}
                        >
                          {Object.values(UnitType).map((type) => (
                            <MenuItem key={type} value={type}>
                              {type.charAt(0).toUpperCase() + type.slice(1)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleAddSelfToGame}
                        startIcon={<Add />}
                        disabled={game?.status !== GameStatus.PENDING}
                      >
                        Присоединиться к игре
                      </Button>
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Блок: Информация об игре */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SportsEsports sx={{ verticalAlign: 'middle', mr: 1 }} /> Общая информация об игре
              </Typography>
              <Chip label={`Статус: ${game?.status}`} color={game?.status === GameStatus.ACTIVE ? 'success' : game?.status === GameStatus.PENDING ? 'info' : 'default'} sx={{ mb: 1 }} />
              <Typography variant="body1"><strong>Режим игры:</strong> {game?.game_mode}</Typography>
              <Typography variant="body1"><strong>Макс. игроков:</strong> {game?.max_players}</Typography>
              <Typography variant="body1"><strong>Текущие игроки:</strong> {game?.current_players_count}</Typography>
              <Typography variant="body1"><strong>Команды:</strong> {game?.team_count}</Typography>
              <Typography variant="body1"><strong>Уровень:</strong> {game?.level}</Typography>
              <Typography variant="body1"><strong>Создана:</strong> {game?.created_at ? new Date(game.created_at).toLocaleString() : 'N/A'}</Typography>
              <Typography variant="body1"><strong>Обновлена:</strong> {game?.updated_at ? new Date(game.updated_at).toLocaleString() : 'N/A'}</Typography>

              {game?.settings.map_template_id && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1"><strong>Используемый шаблон карты:</strong></Typography>
                  <FormControl fullWidth margin="normal">
                    <InputLabel id="map-template-select-label">Выберите шаблон карты</InputLabel>
                    <Select
                      labelId="map-template-select-label"
                      value={selectedMapTemplateId}
                      label="Выберите шаблон карты"
                      onChange={handleMapTemplateChange}
                      disabled={game?.status !== GameStatus.PENDING}
                    >
                      <MenuItem value=""><em>Без изменений</em></MenuItem>
                      {mapTemplates.map((template) => (
                        <MenuItem key={template.id} value={template.id}>
                          {template.name} ({template.width}x{template.height}, {template.difficulty}★)
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
              )}

              {displayedMapGrid && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1" sx={{ mb: 1 }}><strong>Предпросмотр карты:</strong></Typography>
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: `repeat(${game?.settings.default_map_width || 15}, 20px)`,
                      gap: '1px',
                      border: '1px solid #ccc',
                      width: (game?.settings.default_map_width || 15) * 20 + (game?.settings.default_map_width || 15) - 1,
                      height: (game?.settings.default_map_height || 11) * 20 + (game?.settings.default_map_height || 11) - 1,
                      margin: '0 auto',
                    }}
                  >
                    {displayedMapGrid.map((row: number[], rowIndex: number) => (
                      row.map((cell: number, colIndex: number) => {
                        const cellTypeColors: { [key: number]: string } = {
                          0: "#8CBF26", // Empty (Green grass)
                          1: "#6B6B6B", // Solid wall (Dark gray)
                          2: "#B97A57", // Breakable block (Brown)
                          3: "#FFCC00", // Player Spawn (Yellow)
                          4: "#FF0000", // Enemy Spawn (Red)
                          5: "#00FF00", // Level Exit (Bright Green)
                        };
                        return (
                          <Box
                            key={`${rowIndex}-${colIndex}`}
                            sx={{
                              width: '20px',
                              height: '20px',
                              backgroundColor: cellTypeColors[cell] || '#FF00FF', // Magenta for unknown
                              border: '0.5px solid #ccc',
                            }}
                          />
                        );
                      })
                    ))}
                  </Box>
                </Box>
              )}

              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                {game?.status === GameStatus.PENDING && (
                  <Button
                    variant="contained"
                    color="success"
                    onClick={handleStartGame}
                    startIcon={<PlayArrow />}
                    disabled={game?.current_players_count === 0 || game?.game_mode === GameModeType.CAPTURE_THE_FLAG && game?.teams.length === 0}
                  >
                    Начать игру
                  </Button>
                )}
                {game?.status === GameStatus.ACTIVE && (
                  <Button
                    variant="outlined"
                    color="warning"
                    onClick={handlePauseGame}
                    startIcon={<Pause />}
                  >
                    Приостановить игру
                  </Button>
                )}
                {game?.status === GameStatus.PAUSED && (
                  <Button
                    variant="contained"
                    color="success"
                    onClick={handleResumeGame}
                    startIcon={<PlayArrow />}
                  >
                    Возобновить игру
                  </Button>
                )}
                {(game?.status === GameStatus.PENDING || game?.status === GameStatus.FINISHED) && (
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={handleDeleteGame}
                    startIcon={<Delete />}
                  >
                    Удалить игру
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Блок: Игроки */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <People sx={{ verticalAlign: 'middle', mr: 1 }} /> Игроки ({game?.players.length}/{game?.max_players})
              </Typography>
              <Button
                variant="contained"
                onClick={() => setOpenAddPlayerDialog(true)}
                sx={{ mb: 2 }}
                disabled={game?.current_players_count >= game?.max_players}
              >
                Добавить игрока
              </Button>
              <List>
                {game?.players.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">В этой игре пока нет игроков.</Typography>
                ) : (
                  game?.players.map(player => (
                    <ListItem
                      key={player.id}
                      secondaryAction={
                        <Box>
                          {game?.game_mode === GameModeType.CAPTURE_THE_FLAG && (
                            <FormControl sx={{ minWidth: 120, mr: 1 }} size="small">
                              <InputLabel id={`team-select-label-${player.id}`}>Команда</InputLabel>
                              <Select
                                labelId={`team-select-label-${player.id}`}
                                value={player.team_id || ''}
                                label="Команда"
                                onChange={(e) => handleAddPlayerToTeam(e.target.value as string, player.id)}
                                disabled={game?.status !== GameStatus.PENDING}
                              >
                                <MenuItem value=""><em>Без команды</em></MenuItem>
                                {game?.teams.map((team) => (
                                  <MenuItem key={team.id} value={team.id}>
                                    {team.name}
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>
                          )}
                          <IconButton
                            edge="end"
                            aria-label="delete"
                            onClick={() => handleRemovePlayer(player.id)}
                            disabled={game?.status !== GameStatus.PENDING}
                          >
                            <Remove />
                          </IconButton>
                        </Box>
                      }
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Badge variant="dot" color={player.invulnerable ? "info" : "success"} sx={{ mr: 1 }} />
                            {player.name} ({player.unit_type.charAt(0).toUpperCase() + player.unit_type.slice(1)})
                            {player.team_id && (
                              <Chip
                                label={game?.teams.find(t => t.id === player.team_id)?.name || 'Неизвестная команда'}
                                size="small"
                                sx={{ ml: 1, backgroundColor: player.color || '#ccc', color: '#fff' }}
                                onDelete={() => handleRemovePlayerFromTeam(player.team_id!, player.id)}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Typography variant="body2" color="text.secondary">
                            Жизни: {player.lives} | Координаты: ({player.x}, {player.y})
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Блок: Команды */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <GroupAdd sx={{ verticalAlign: 'middle', mr: 1 }} /> Команды ({game?.teams.length})
              </Typography>
              <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={() => setOpenCreateTeamDialog(true)}
                  startIcon={<Add />}
                >
                  Создать команду
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<People />}
                  onClick={() => handleDistributePlayers(false)}
                >
                  Распределить игроков
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={() => handleDistributePlayers(true)}
                >
                  Перераспределить игроков
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Done />}
                  onClick={handleValidateTeams}
                >
                  Проверить команды
                </Button>
              </Box>
              <List>
                {game?.teams.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">В этой игре пока нет команд.</Typography>
                ) : (
                  game?.teams.map(team => (
                    <ListItem
                      key={team.id}
                      secondaryAction={
                        <Box>
                          <IconButton
                            edge="end"
                            aria-label="edit"
                            onClick={() => handleEditTeamClick(team)}
                            sx={{ mr: 1 }}
                          >
                            <Edit />
                          </IconButton>
                          <IconButton
                            edge="end"
                            aria-label="delete"
                            onClick={() => handleDeleteTeam(team.id)}
                          >
                            <Delete />
                          </IconButton>
                        </Box>
                      }
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {team.name} ({team.player_count} игроков)
                          </Box>
                        }
                        secondary={
                          <Box>
                            {team.player_ids.map(playerId => {
                              const currentTeamId = team.id; // Assign to a local constant
                              return (
                                <Chip
                                  key={playerId}
                                  label={game?.players.find(p => p.id === playerId)?.name || `Неизвестный игрок (${playerId.substring(0, 4)}...)`}
                                  size="small"
                                  sx={{ mr: 0.5, mb: 0.5 }}
                                  onDelete={() => handleRemovePlayerFromTeam(team.id, playerId)}
                                  disabled={game?.status !== GameStatus.PENDING}
                                />
                              );
                            })}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add Player Dialog */}
      <Dialog open={openAddPlayerDialog} onClose={() => setOpenAddPlayerDialog(false)}>
        <DialogTitle>Добавить игрока</DialogTitle>
        <DialogContent>
          {addPlayerError && <Alert severity="error" sx={{ mb: 2 }}>{addPlayerError}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="ID Игрока"
            type="text"
            fullWidth
            value={addPlayerId}
            onChange={(e) => setAddPlayerId(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel id="add-player-unit-type-label">Тип юнита</InputLabel>
            <Select
              labelId="add-player-unit-type-label"
              value={addPlayerUnitType}
              label="Тип юнита"
              onChange={(e) => setAddPlayerUnitType(e.target.value as UnitType)}
            >
              {Object.values(UnitType).map((type) => (
                <MenuItem key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddPlayerDialog(false)}>Отмена</Button>
          <Button onClick={handleAddPlayer}>Добавить</Button>
        </DialogActions>
      </Dialog>

      {/* Create Team Dialog */}
      <Dialog open={openCreateTeamDialog} onClose={() => setOpenCreateTeamDialog(false)}>
        <DialogTitle>Создать команду</DialogTitle>
        <DialogContent>
          {createTeamError && <Alert severity="error" sx={{ mb: 2 }}>{createTeamError}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="Название команды"
            type="text"
            fullWidth
            value={newTeamName}
            onChange={(e) => setNewTeamName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateTeamDialog(false)}>Отмена</Button>
          <Button onClick={handleCreateTeam}>Создать</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Team Dialog */}
      <Dialog open={openEditTeamDialog} onClose={() => setOpenEditTeamDialog(false)}>
        <DialogTitle>Редактировать команду</DialogTitle>
        <DialogContent>
          {editTeamError && <Alert severity="error" sx={{ mb: 2 }}>{editTeamError}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="Название команды"
            type="text"
            fullWidth
            value={editTeamName}
            onChange={(e) => setEditTeamName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditTeamDialog(false)}>Отмена</Button>
          <Button onClick={handleUpdateTeam}>Сохранить</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ManageGame; 