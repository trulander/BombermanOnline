import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  CircularProgress, 
  Alert, 
  Button, 
  Grid, 
  Card, 
  CardContent, 
  Chip, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Badge
} from '@mui/material';
import { 
  PlayArrow, Pause, Refresh, Delete, Add, Remove,
  GroupAdd, GroupRemove, Done, Warning,
  Edit,
  People,
  SportsEsports
} from '@mui/icons-material';
import GameLayout from '../components/GameLayout';
import { gameApi } from '../services/api';
import { GameState } from '../types/GameState'; // Для UnitType, если потребуется
import { useAuth } from '../context/AuthContext';

// Определения типов данных (на основе game_routes.py и team_routes.py)
export enum GameStatus {
  PENDING = 'PENDING',
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  FINISHED = 'FINISHED',
  ABORTED = 'ABORTED',
}

export enum GameModeType {
  FREE_FOR_ALL = 'FREE_FOR_ALL',
  TEAM_BATTLE = 'TEAM_BATTLE',
  BATTLE_ROYALE = 'BATTLE_ROYALE',
}

export enum UnitType {
  BOMBERMAN = 'bomberman',
  TANK = 'tank',
}

export interface GamePlayerInfo {
  id: string;
  name: string;
  unit_type: UnitType;
  team_id?: string;
  lives: number;
  x: number;
  y: number;
  color: string;
  invulnerable: boolean;
}

export interface GameTeamInfo {
  id: string;
  name: string;
  score: number;
  player_ids: string[];
  player_count: number;
}

export interface GameSettings {
  game_mode: GameModeType;
  max_players: number;
  level_name: string;
  round_duration: number;
  respawn_invulnerability_time: number;
  initial_lives: number;
  max_bombs: number;
  bomb_power: number;
  max_power_ups: number;
  power_up_spawn_interval: number;
  time_to_first_spawn: number;
  time_between_spawns: number;
  min_enemies: number;
  max_enemies: number;
  enemy_spawn_interval: number;
}

export interface GameInfo {
  game_id: string;
  status: GameStatus;
  game_mode: GameModeType;
  max_players: number;
  current_players_count: number;
  team_count: number;
  level: number;
  score: number;
  game_over: boolean;
  players: GamePlayerInfo[];
  teams: GameTeamInfo[];
  settings: GameSettings; // Backend sends a dict, we can type it specifically
  created_at: string;
  updated_at: string;
}

const ManageGame: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [game, setGame] = useState<GameInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [openAddPlayerDialog, setOpenAddPlayerDialog] = useState(false);
  const [addPlayerId, setAddPlayerId] = useState<string>('');
  const [addPlayerUnitType, setAddPlayerUnitType] = useState<UnitType>(UnitType.BOMBERMAN);
  const [addPlayerError, setAddPlayerError] = useState<string | null>(null);
  
  const [openCreateTeamDialog, setOpenCreateTeamDialog] = useState(false);
  const [newTeamName, setNewTeamName] = useState<string>('');
  const [createTeamError, setCreateTeamError] = useState<string | null>(null);

  const [openEditTeamDialog, setOpenEditTeamDialog] = useState(false);
  const [editTeamId, setEditTeamId] = useState<string | null>(null);
  const [editTeamName, setEditTeamName] = useState<string>('');
  const [editTeamError, setEditTeamError] = useState<string | null>(null);

  const fetchGameDetails = async () => {
    if (!gameId) {
      setError('Идентификатор игры не указан.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await gameApi.get<GameInfo>(`/games/${gameId}`);
      setGame(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching game details:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить информацию об игре.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGameDetails();
    // Устанавливаем интервал для обновления информации об игре
    const interval = setInterval(fetchGameDetails, 5000); // Обновлять каждые 5 секунд
    return () => clearInterval(interval); // Очистка интервала при размонтировании
  }, [gameId]);

  const handleGameAction = async (action: 'start' | 'pause' | 'resume') => {
    try {
      const response = await gameApi.put(`/games/${gameId}/status`, { action });
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
    if (!window.confirm('Вы уверены, что хотите удалить эту игру? Это действие необратимо.')) {
      return;
    }
    try {
      const response = await gameApi.delete(`/games/${gameId}`);
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
    try {
      const response = await gameApi.post(`/games/${gameId}/players`, {
        player_id: addPlayerId,
        unit_type: addPlayerUnitType
      });
      if (response.data.success) {
        fetchGameDetails();
        setOpenAddPlayerDialog(false);
        setAddPlayerId('');
      } else {
        setAddPlayerError(response.data.message || 'Не удалось добавить игрока.');
      }
    } catch (err: any) {
      console.error('Error adding player:', err);
      setAddPlayerError(err.response?.data?.detail || 'Ошибка сервера при добавлении игрока.');
    }
  };

  const handleRemovePlayer = async (playerId: string) => {
    if (!window.confirm(`Вы уверены, что хотите удалить игрока ${playerId} из игры?`)) {
      return;
    }
    try {
      const response = await gameApi.delete(`/games/${gameId}/players/${playerId}`);
      if (response.data.success) {
        fetchGameDetails();
      } else {
        setError(response.data.message || `Не удалось удалить игрока ${playerId}.`);
      }
    } catch (err: any) {
      console.error('Error removing player:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении игрока.');
    }
  };

  const handleCreateTeam = async () => {
    setCreateTeamError(null);
    if (!newTeamName.trim()) {
      setCreateTeamError('Имя команды не может быть пустым.');
      return;
    }
    try {
      const response = await gameApi.post(`/teams/${gameId}`, { name: newTeamName });
      if (response.data) {
        fetchGameDetails();
        setOpenCreateTeamDialog(false);
        setNewTeamName('');
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
    if (!editTeamId || !editTeamName.trim()) {
      setEditTeamError('Имя команды не может быть пустым.');
      return;
    }
    try {
      const response = await gameApi.put(`/teams/${gameId}/${editTeamId}`, { name: editTeamName });
      if (response.data) {
        fetchGameDetails();
        setOpenEditTeamDialog(false);
        setEditTeamId(null);
        setEditTeamName('');
      } else {
        setEditTeamError(response.data.message || 'Не удалось обновить команду.');
      }
    } catch (err: any) {
      console.error('Error updating team:', err);
      setEditTeamError(err.response?.data?.detail || 'Ошибка сервера при обновлении команды.');
    }
  };

  const handleDeleteTeam = async (teamId: string) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту команду? Игроки будут откреплены.')) {
      return;
    }
    try {
      const response = await gameApi.delete(`/teams/${gameId}/${teamId}`);
      if (response.status === 204) { // 204 No Content on successful deletion
        fetchGameDetails();
      } else {
        setError(response.data?.message || 'Не удалось удалить команду.');
      }
    } catch (err: any) {
      console.error('Error deleting team:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении команды.');
    }
  };

  const handleAddPlayerToTeam = async (teamId: string, playerId: string) => {
    if (!window.confirm(`Вы уверены, что хотите добавить игрока ${playerId} в команду ${teamId}?`)) {
      return;
    }
    try {
      const response = await gameApi.post(`/teams/${gameId}/${teamId}/players/${playerId}`);
      if (response.data.success) {
        fetchGameDetails();
      } else {
        setError(response.data.message || `Не удалось добавить игрока ${playerId} в команду ${teamId}.`);
      }
    } catch (err: any) {
      console.error('Error adding player to team:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при добавлении игрока в команду.');
    }
  };

  const handleRemovePlayerFromTeam = async (teamId: string, playerId: string) => {
    if (!window.confirm(`Вы уверены, что хотите удалить игрока ${playerId} из команды ${teamId}?`)) {
      return;
    }
    try {
      const response = await gameApi.delete(`/teams/${gameId}/${teamId}/players/${playerId}`);
      if (response.data.success) {
        fetchGameDetails();
      } else {
        setError(response.data.message || `Не удалось удалить игрока ${playerId} из команды ${teamId}.`);
      }
    } catch (err: any) {
      console.error('Error removing player from team:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при удалении игрока из команды.');
    }
  };

  const handleDistributePlayers = async (redistributeExisting: boolean) => {
    try {
      const response = await gameApi.post(`/teams/${gameId}/distribute`, { redistribute_existing: redistributeExisting });
      if (response.data.success) {
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
    try {
      const response = await gameApi.post(`/teams/${gameId}/validate`);
      if (response.data.is_valid) {
        setSuccess('Конфигурация команд действительна!');
        setError(null);
      } else {
        setError(response.data.message || 'Конфигурация команд недействительна.');
        setSuccess(null);
      }
    } catch (err: any) {
      console.error('Error validating teams:', err);
      setError(err.response?.data?.detail || 'Ошибка сервера при валидации команд.');
    }
  };

  const handleStartGame = () => {
    if (game && game.status === GameStatus.PENDING) {
      // Redirect to the actual game page
      navigate(`/account/game/${game.game_id}`);
    }
  };

  const isGamePending = game?.status === GameStatus.PENDING;
  const isGameActive = game?.status === GameStatus.ACTIVE;
  const isGamePaused = game?.status === GameStatus.PAUSED;
  const isGameFinishedOrAborted = game?.status === GameStatus.FINISHED || game?.status === GameStatus.ABORTED;

  if (loading) {
    return (
      <GameLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>Загрузка информации об игре...</Typography>
        </Box>
      </GameLayout>
    );
  }

  if (error && !game) {
    return (
      <GameLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Alert severity="error">{error}</Alert>
        </Box>
      </GameLayout>
    );
  }

  if (!game) {
    return (
      <GameLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Alert severity="info">Игра не найдена или еще не загружена.</Alert>
        </Box>
      </GameLayout>
    );
  }

  return (
    <GameLayout>
      <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
        <Typography component="h1" variant="h4" gutterBottom align="center">
          Управление игрой: {game.game_id}
        </Typography>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Game Info Card */}
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h5" gutterBottom>Информация об игре</Typography>
                <Typography variant="body1"><strong>Статус:</strong> <Chip label={game.status} color={game.status === GameStatus.ACTIVE ? 'success' : game.status === GameStatus.PENDING ? 'warning' : 'info'} /></Typography>
                <Typography variant="body1"><strong>Режим игры:</strong> {game.game_mode}</Typography>
                <Typography variant="body1"><strong>Игроки:</strong> {game.current_players_count} / {game.max_players}</Typography>
                <Typography variant="body1"><strong>Команды:</strong> {game.team_count}</Typography>
                <Typography variant="body1"><strong>Уровень:</strong> {game.level}</Typography>
                <Typography variant="body1"><strong>Счет:</strong> {game.score}</Typography>
                <Typography variant="body1"><strong>Игра окончена:</strong> {game.game_over ? 'Да' : 'Нет'}</Typography>
                <Typography variant="body2" color="text.secondary">Создана: {new Date(game.created_at).toLocaleString()}</Typography>
                <Typography variant="body2" color="text.secondary">Обновлена: {new Date(game.updated_at).toLocaleString()}</Typography>
              
                <Box sx={{ mt: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    startIcon={<PlayArrow />} 
                    onClick={() => handleGameAction('start')}
                    disabled={!isGamePending}
                  >
                    Начать
                  </Button>
                  <Button 
                    variant="outlined" 
                    color="warning" 
                    startIcon={<Pause />} 
                    onClick={() => handleGameAction('pause')}
                    disabled={!isGameActive}
                  >
                    Пауза
                  </Button>
                  <Button 
                    variant="outlined" 
                    color="success" 
                    startIcon={<Refresh />} 
                    onClick={() => handleGameAction('resume')}
                    disabled={!isGamePaused}
                  >
                    Возобновить
                  </Button>
                  <Button 
                    variant="outlined" 
                    color="error" 
                    startIcon={<Delete />} 
                    onClick={handleDeleteGame}
                    disabled={!(isGamePending || isGameFinishedOrAborted)}
                  >
                    Удалить игру
                  </Button>
                  <Button
                    variant="contained"
                    color="secondary"
                    startIcon={<SportsEsports />}
                    onClick={handleStartGame}
                    disabled={!isGameActive}
                  >
                    Играть
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Players Card */}
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h5">Игроки ({game.players.length}/{game.max_players})</Typography>
                  <Button 
                    variant="contained" 
                    size="small" 
                    startIcon={<Add />} 
                    onClick={() => setOpenAddPlayerDialog(true)}
                    disabled={!isGamePending || game.players.length >= game.max_players}
                  >
                    Добавить
                  </Button>
                </Box>
                <List>
                  {game.players.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">В игре пока нет игроков.</Typography>
                  ) : (
                    game.players.map(player => (
                      <ListItem 
                        key={player.id} 
                        secondaryAction={
                          <IconButton edge="end" aria-label="delete" onClick={() => handleRemovePlayer(player.id)} disabled={!isGamePending}>
                            <Remove />
                          </IconButton>
                        }
                      >
                        <ListItemText 
                          primary={player.name || `Игрок ${player.id}`}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.secondary">
                                Юнит: {player.unit_type}, Жизни: {player.lives}
                              </Typography>
                              {player.team_id && (
                                <Typography component="span" variant="body2" color="text.secondary" sx={{ display: 'block' }}>
                                  Команда: {game.teams.find(t => t.id === player.team_id)?.name || player.team_id}
                                </Typography>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                    ))
                  )}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Teams Card */}
          <Grid item xs={12}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h5">Команды ({game.teams.length})</Typography>
                  <Box>
                    <Button 
                      variant="outlined" 
                      size="small" 
                      startIcon={<GroupAdd />} 
                      onClick={() => setOpenCreateTeamDialog(true)}
                      disabled={!isGamePending}
                      sx={{ mr: 1 }}
                    >
                      Создать команду
                    </Button>
                    <Button 
                      variant="contained" 
                      size="small" 
                      startIcon={<People />} 
                      onClick={() => handleDistributePlayers(false)}
                      disabled={!isGamePending || game.players.length === 0}
                      sx={{ mr: 1 }}
                    >
                      Распределить игроков
                    </Button>
                     <Button 
                      variant="outlined" 
                      size="small" 
                      startIcon={<Refresh />} 
                      onClick={() => handleDistributePlayers(true)}
                      disabled={!isGamePending || game.players.length === 0}
                      sx={{ mr: 1 }}
                    >
                      Перераспределить
                    </Button>
                     <Button 
                      variant="contained" 
                      size="small" 
                      color="info"
                      startIcon={<Done />} 
                      onClick={handleValidateTeams}
                      disabled={!isGamePending}
                    >
                      Проверить команды
                    </Button>
                  </Box>
                </Box>
                <List>
                  {game.teams.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">В игре пока нет команд.</Typography>
                  ) : (
                    game.teams.map(team => (
                      <ListItem 
                        key={team.id} 
                        secondaryAction={
                          <Box>
                            <IconButton edge="end" aria-label="edit" sx={{ mr: 1 }} disabled={!isGamePending}>
                                <Edit />
                            </IconButton>
                            <IconButton edge="end" aria-label="delete" disabled={!isGamePending}>
                                <Delete />
                            </IconButton>
                          </Box>
                        }
                      >
                        <ListItemText 
                          primary={`${team.name} (Игроков: ${team.player_count}, Счет: ${team.score})`}
                          secondary={
                            team.player_ids.length > 0 ? 
                              `Игроки: ${team.player_ids.map(pId => game.players.find(p => p.id === pId)?.name || pId).join(', ')}` : 
                              'Нет игроков'
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
      </Box>

      {/* Add Player Dialog */}
      <Dialog open={openAddPlayerDialog} onClose={() => setOpenAddPlayerDialog(false)}>
        <DialogTitle>Добавить игрока в игру</DialogTitle>
        <DialogContent>
          {addPlayerError && <Alert severity="error" sx={{ mb: 2 }}>{addPlayerError}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="ID Игрока"
            type="text"
            fullWidth
            variant="outlined"
            value={addPlayerId}
            onChange={(e) => setAddPlayerId(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth variant="outlined">
            <InputLabel id="unit-type-label">Тип юнита</InputLabel>
            <Select
              labelId="unit-type-label"
              value={addPlayerUnitType}
              onChange={(e) => setAddPlayerUnitType(e.target.value as UnitType)}
              label="Тип юнита"
            >
              {Object.keys(UnitType).map((type) => (
                <MenuItem key={type} value={type.toLowerCase()}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddPlayerDialog(false)}>Отмена</Button>
          <Button onClick={handleAddPlayer} variant="contained">Добавить</Button>
        </DialogActions>
      </Dialog>

      {/* Create Team Dialog */}
      <Dialog open={openCreateTeamDialog} onClose={() => setOpenCreateTeamDialog(false)}>
        <DialogTitle>Создать новую команду</DialogTitle>
        <DialogContent>
          {createTeamError && <Alert severity="error" sx={{ mb: 2 }}>{createTeamError}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="Название команды"
            type="text"
            fullWidth
            variant="outlined"
            value={newTeamName}
            onChange={(e) => setNewTeamName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateTeamDialog(false)}>Отмена</Button>
          <Button onClick={handleCreateTeam} variant="contained">Создать</Button>
        </DialogActions>
      </Dialog>

    </GameLayout>
  );
};

export default ManageGame; 