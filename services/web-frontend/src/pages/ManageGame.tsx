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
  Badge,
  SelectChangeEvent
} from '@mui/material';
import { 
  PlayArrow, Pause, Refresh, Delete, Add, Remove,
  GroupAdd, GroupRemove, Done, Warning,
  Edit,
  People,
  SportsEsports
} from '@mui/icons-material';
import GameLayout from '../components/GameLayout';
import { gameApi, getProxiedGameApi } from '../services/api';
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
  map_template_id?: string; // Add map_template_id to settings
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

  // Initialize proxiedGameApi here, as it depends on gameId
  const proxiedGameApi = gameId ? getProxiedGameApi(gameId) : null;

  const [game, setGame] = useState<GameInfo | null>(null);
  const [mapTemplates, setMapTemplates] = useState<MapTemplate[]>([]);
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

  const [selectedMapTemplateId, setSelectedMapTemplateId] = useState<string>('');

  const fetchGameDetails = async () => {
    if (!gameId || !proxiedGameApi) {
      setError('Идентификатор игры или прокси API не инициализирован.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const [gameResponse, mapsResponse] = await Promise.all([
        proxiedGameApi.get<GameInfo>(`/games/${gameId}`),
        proxiedGameApi.get<MapTemplate[]>('/maps/templates') // Also proxy map templates when fetched in game context
      ]);
      setGame(gameResponse.data);
      setMapTemplates(mapsResponse.data);

      if (gameResponse.data.settings.map_template_id) {
        setSelectedMapTemplateId(gameResponse.data.settings.map_template_id);
      }

      setError(null);
    } catch (err: any) {
      console.error('Error fetching game details or map templates:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить информацию об игре или шаблоны карт.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (proxiedGameApi) {
      fetchGameDetails();
      const interval = setInterval(fetchGameDetails, 5000); // Обновлять каждые 5 секунд
      return () => clearInterval(interval); // Очистка интервала при размонтировании
    }
  }, [gameId, proxiedGameApi]); // Add proxiedGameApi to dependencies

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

  const currentMapPreview = selectedMapTemplateId
    ? mapTemplates.find(map => map.id === selectedMapTemplateId)
    : null;

  if (loading || !game) {
    return (
      <GameLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>Загрузка данных игры...</Typography>
        </Box>
      </GameLayout>
    );
  }

  return (
    <GameLayout>
      <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
        <Typography component="h1" variant="h4" gutterBottom align="center">
          Управление игрой: {game.game_id.substring(0, 8)}...
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Общая информация об игре
                </Typography>
                <Chip label={`Статус: ${game.status}`} color={game.status === GameStatus.ACTIVE ? 'success' : game.status === GameStatus.PENDING ? 'info' : 'default'} sx={{ mb: 1 }} />
                <Typography variant="body1"><strong>Режим игры:</strong> {game.game_mode}</Typography>
                <Typography variant="body1"><strong>Макс. игроков:</strong> {game.max_players}</Typography>
                <Typography variant="body1"><strong>Текущие игроки:</strong> {game.current_players_count}</Typography>
                <Typography variant="body1"><strong>Команды:</strong> {game.team_count}</Typography>
                <Typography variant="body1"><strong>Уровень:</strong> {game.level}</Typography>
                <Typography variant="body1"><strong>Создана:</strong> {new Date(game.created_at).toLocaleString()}</Typography>
                <Typography variant="body1"><strong>Обновлена:</strong> {new Date(game.updated_at).toLocaleString()}</Typography>
                
                {game.settings.map_template_id && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body1"><strong>Используемый шаблон карты:</strong></Typography>
                    <FormControl fullWidth margin="normal">
                      <InputLabel id="map-template-select-label">Выберите шаблон карты</InputLabel>
                      <Select
                        labelId="map-template-select-label"
                        value={selectedMapTemplateId}
                        label="Выберите шаблон карты"
                        onChange={handleMapTemplateChange}
                        disabled={game.status !== GameStatus.PENDING} // Disable if game is not PENDING
                      >
                        <MenuItem value=""><em>Без изменений</em></MenuItem>
                        {mapTemplates.map((map) => (
                          <MenuItem key={map.id} value={map.id}>
                            {map.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>
                )}

                {currentMapPreview && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="h6" sx={{ mt: 2 }}>Предварительный просмотр выбранной карты:</Typography>
                    <Box sx={{ 
                      border: '1px solid #ccc', 
                      p: 1, 
                      mt: 1, 
                      overflow: 'auto', 
                      maxHeight: '200px',
                      fontFamily: 'monospace',
                      fontSize: '12px'
                    }}>
                      {currentMapPreview.grid.map((row, rowIndex) => (
                        <div key={rowIndex} style={{ whiteSpace: 'pre' }}>
                          {row.map((cell, colIndex) => (
                            <span 
                              key={colIndex} 
                              style={{
                                backgroundColor: cell === 'wall' ? '#888' : 
                                                 cell === 'empty' ? '#eee' : 
                                                 cell === 'start' ? '#afa' : 
                                                 '#fff',
                                width: '10px',
                                height: '10px',
                                display: 'inline-block',
                                border: '1px solid #ddd'
                              }}
                            ></span>
                          ))}
                        </div>
                      ))}
                    </Box>
                  </Box>
                )}


                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  {game.status === GameStatus.PENDING && (
                    <Button 
                      variant="contained" 
                      color="primary" 
                      startIcon={<PlayArrow />} 
                      onClick={handleStartGame}
                    >
                      Начать игру
                    </Button>
                  )}
                  {game.status === GameStatus.ACTIVE && (
                    <Button 
                      variant="outlined" 
                      color="warning" 
                      startIcon={<Pause />} 
                      onClick={handlePauseGame}
                    >
                      Пауза
                    </Button>
                  )}
                  {game.status === GameStatus.PAUSED && (
                    <Button 
                      variant="contained" 
                      color="primary" 
                      startIcon={<PlayArrow />} 
                      onClick={handleResumeGame}
                    >
                      Возобновить
                    </Button>
                  )}
                  <Button 
                    variant="outlined" 
                    color="error" 
                    startIcon={<Delete />} 
                    onClick={handleDeleteGame}
                  >
                    Удалить игру
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Игроки ({game.players.length}/{game.max_players})
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={() => setOpenAddPlayerDialog(true)}
                  sx={{ mb: 2 }}
                  disabled={game.current_players_count >= game.max_players}
                >
                  Добавить игрока
                </Button>
                <List>
                  {game.players.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">В этой игре пока нет игроков.</Typography>
                  ) : (
                    game.players.map(player => (
                      <ListItem 
                        key={player.id}
                        secondaryAction={
                          <Box>
                            {game.game_mode === GameModeType.TEAM_BATTLE && (
                              <FormControl sx={{ minWidth: 120, mr: 1 }} size="small">
                                <InputLabel id={`team-select-label-${player.id}`}>Команда</InputLabel>
                                <Select
                                  labelId={`team-select-label-${player.id}`}
                                  value={player.team_id || ''}
                                  label="Команда"
                                  onChange={(e) => handleAddPlayerToTeam(e.target.value as string, player.id)}
                                  disabled={game.status !== GameStatus.PENDING}
                                >
                                  <MenuItem value=""><em>Без команды</em></MenuItem>
                                  {game.teams.map((team) => (
                                    <MenuItem key={team.id} value={team.id}>
                                      {team.name}
                                    </MenuItem>
                                  ))}
                                </Select>
                              </FormControl>
                            )}
                            <IconButton edge="end" aria-label="remove player" onClick={() => handleRemovePlayer(player.id)}>
                              <Remove />
                            </IconButton>
                          </Box>
                        }
                      >
                        <ListItemText 
                          primary={<>
                            <Typography component="span" variant="body1" sx={{ fontWeight: 'bold' }}>{player.name}</Typography>
                            {player.team_id && (
                              <Chip 
                                label={game.teams.find(t => t.id === player.team_id)?.name || 'Неизвестная команда'}
                                size="small" 
                                sx={{ ml: 1, backgroundColor: player.color || '#ccc', color: '#fff' }}
                              />
                            )}
                          </>}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.secondary">
                                ID: {player.id.substring(0, 8)}...
                              </Typography>
                              <br/>
                              <Typography component="span" variant="body2" color="text.secondary">
                                Тип юнита: {player.unit_type}
                              </Typography>
                              <br/>
                              <Typography component="span" variant="body2" color="text.secondary">
                                Жизни: {player.lives}
                              </Typography>
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

          {game.game_mode === GameModeType.TEAM_BATTLE && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Команды ({game.teams.length})
                  </Typography>
                  <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      startIcon={<Add />}
                      onClick={() => setOpenCreateTeamDialog(true)}
                    >
                      Создать команду
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<People />}
                      onClick={() => handleDistributePlayers(false)}
                      disabled={game.status !== GameStatus.PENDING || game.players.length === 0 || game.teams.length === 0}
                    >
                      Распределить игроков
                    </Button>
                     <Button
                      variant="outlined"
                      startIcon={<Refresh />}
                      onClick={() => handleDistributePlayers(true)}
                      disabled={game.status !== GameStatus.PENDING || game.players.length === 0 || game.teams.length === 0}
                    >
                      Перераспределить игроков
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Done />}
                      onClick={handleValidateTeams}
                      disabled={game.status !== GameStatus.PENDING}
                    >
                      Проверить команды
                    </Button>
                  </Box>
                  <List>
                    {game.teams.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">В этой игре пока нет команд.</Typography>
                    ) : (
                      game.teams.map(team => (
                        <ListItem
                          key={team.id}
                          secondaryAction={
                            <Box>
                              <IconButton edge="end" aria-label="edit team" onClick={() => handleEditTeamClick(team)}>
                                <Edit />
                              </IconButton>
                              <IconButton edge="end" aria-label="delete team" onClick={() => handleDeleteTeam(team.id)}>
                                <Delete />
                              </IconButton>
                            </Box>
                          }
                        >
                          <ListItemText 
                            primary={<>
                              <Typography component="span" variant="body1" sx={{ fontWeight: 'bold' }}>{team.name}</Typography>
                              <Chip label={`Счет: ${team.score}`} size="small" sx={{ ml: 1 }} />
                              {team.player_count > 0 && (
                                <Badge badgeContent={team.player_count} color="primary" sx={{ ml: 1 }}>
                                  <SportsEsports />
                                </Badge>
                              )}
                            </>}
                            secondary={
                              <>
                                <Typography component="span" variant="body2" color="text.secondary">
                                  ID: {team.id.substring(0, 8)}...
                                </Typography>
                                <br/>
                                <Typography component="span" variant="body2" color="text.secondary">
                                  Игроки: {team.player_ids.length > 0 ? team.player_ids.map(id => id.substring(0, 8)).join(', ') : 'Нет'}
                                </Typography>
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
          )}
        </Grid>
      </Box>

      {/* Add Player Dialog */}
      <Dialog open={openAddPlayerDialog} onClose={() => setOpenAddPlayerDialog(false)}>
        <DialogTitle>Добавить игрока</DialogTitle>
        <DialogContent>
          {addPlayerError && <Alert severity="error" sx={{ mb: 2 }}>{addPlayerError}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="ID Игрока (или username)"
            type="text"
            fullWidth
            variant="outlined"
            value={addPlayerId}
            onChange={(e) => setAddPlayerId(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel id="unit-type-label">Тип юнита</InputLabel>
            <Select
              labelId="unit-type-label"
              value={addPlayerUnitType}
              label="Тип юнита"
              onChange={(e) => setAddPlayerUnitType(e.target.value as UnitType)}
            >
              {Object.values(UnitType).map((type) => (
                <MenuItem key={type} value={type}>{type}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddPlayerDialog(false)}>Отмена</Button>
          <Button onClick={handleAddPlayer} variant="contained" color="primary">
            Добавить
          </Button>
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
          <Button onClick={handleCreateTeam} variant="contained" color="primary">
            Создать
          </Button>
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
            variant="outlined"
            value={editTeamName}
            onChange={(e) => setEditTeamName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditTeamDialog(false)}>Отмена</Button>
          <Button onClick={handleUpdateTeam} variant="contained" color="primary">
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>
    </GameLayout>
  );
};

export default ManageGame; 