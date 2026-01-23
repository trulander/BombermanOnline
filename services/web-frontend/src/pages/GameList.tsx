import React, {useEffect, useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Grid, Typography} from '@mui/material';
import {PlayArrow} from '@mui/icons-material';
// import Layout from '../components/Layout'; // Using the general layout
import {webApi} from '../services/api';

import {GameListItem, GameStatus} from "../types/Game"; // Reusing types from ManageGame

const GameList: React.FC = () => {
  const navigate = useNavigate();
  const [games, setGames] = useState<GameListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGames = async () => {
    try {
      setLoading(true);
      const response = await webApi.get<GameListItem[]>('/games');
      setGames(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching game list:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить список игр.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
    const interval = setInterval(fetchGames, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleJoinGame = (gameId: string) => {
    navigate(`/account/game/${gameId}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>Загрузка списка игр...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography component="h1" variant="h4" gutterBottom align="center">
        Список игр
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {games.length === 0 ? (
        <Typography variant="body1" color="text.secondary" align="center">
          Нет доступных игр. Почему бы не создать новую?
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {games.map((game) => (
            <Grid item xs={12} sm={6} md={4} key={game.game_id}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>{`Игра ID: ${game.game_id.substring(0, 8)}...`}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Статус:</strong> <Chip label={game.status} color={game.status === GameStatus.ACTIVE ? 'success' : game.status === GameStatus.PENDING ? 'warning' : 'info'} size="small" />
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Режим:</strong> {game.game_mode}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Игроки:</strong> {game.current_players_count}/{game.max_players}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Уровень:</strong> {game.level}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Создана:</strong> {new Date(game.created_at).toLocaleString()}
                  </Typography>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<PlayArrow />}
                    onClick={() => handleJoinGame(game.game_id)}
                    disabled={game.status !== GameStatus.PENDING && game.status !== GameStatus.ACTIVE}
                    sx={{ mt: 2 }}
                    fullWidth
                  >
                    Присоединиться
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default GameList; 