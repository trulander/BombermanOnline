import React, { useRef, useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import GameCanvas from '../components/GameCanvas';
import GameLayout from '../components/GameLayout';
import { GameClient } from '../components/GameClient';
import ManageGame from './ManageGame';
import {Box, CircularProgress, Dialog, DialogContent, DialogTitle, IconButton, Typography} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useAuth } from '../context/AuthContext';
import {EntitiesInfo} from "../types/EntitiesParams";
import {gameApi} from "../services/api";

const Game: React.FC = () => {
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const gameClientRef = useRef<GameClient | null>(null);
  const [searchParams] = useSearchParams();
  const openSettingsOnLoad = searchParams.get('openSettings') === 'true';
  const { user } = useAuth();

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [hasJoinedGame, setHasJoinedGame] = useState(false);

  const [entitiesInfo, setEntitiesInfo] = useState<EntitiesInfo>();
  const [loadingEntities, setLoadingEntities] = useState<boolean>(true);
  const [errorLoadingEntities, setErrorLoadingEntities] = useState<string | null>(null);

  useEffect(() => {
    const fetchEntitiesInfo = async () => {
      try {
        setLoadingEntities(true);
        const response = await gameApi.get<EntitiesInfo>('/entities/info');
        setEntitiesInfo(response.data);
      } catch (err) {
        console.error('Error fetching entities info:', err);
        setErrorLoadingEntities('Не удалось загрузить информацию о сущностях игры.');
      } finally {
        setLoadingEntities(false);
      }
    };

    fetchEntitiesInfo();
  }, []);

  useEffect(() => {
    if (openSettingsOnLoad) {
      setIsSettingsOpen(true);
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete('openSettings');
      navigate(`?${newSearchParams.toString()}`, { replace: true });
    }
  }, [openSettingsOnLoad, navigate, searchParams]);

  const handleAuthenticationFailed = () => {
    navigate('/account/login');
  };

  const handleGameJoined = (success: boolean) => {
    if (success) {
      setHasJoinedGame(true);
    }
  };

  const setGameClientRef = (gameClient: GameClient | null) => {
    gameClientRef.current = gameClient;
    if (gameClient) {
      gameClient.setAuthenticationFailedHandler(handleAuthenticationFailed);
      gameClient.setGameJoinedHandler(handleGameJoined);
    }
  };

  const handleOpenSettings = () => {
    setIsSettingsOpen(true);
  };

  const handleCloseSettings = () => {
    setIsSettingsOpen(false);
  };

    if (loadingEntities) {
    return (
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%'
      }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ mt: 2 }} color="text.secondary">
          Загрузка игровых данных...
        </Typography>
      </Box>
    );
  }

  if (errorLoadingEntities) {
    return (
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%'
      }}>
        <Typography variant="h6" color="error">
          Ошибка загрузки: {errorLoadingEntities}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Пожалуйста, попробуйте обновить страницу.
        </Typography>
      </Box>
    );
  }

  return (
    <GameLayout onOpenSettings={hasJoinedGame ? handleOpenSettings : undefined}>
      <GameCanvas onGameClientReady={setGameClientRef} gameId={gameId} userId={user?.id || ''} entitiesInfo={entitiesInfo} />
      
      {gameId && (
        <Dialog open={isSettingsOpen} onClose={handleCloseSettings} maxWidth="md" fullWidth>
          <DialogTitle sx={{ m: 0, p: 2 }}>
            Настройки игры: {gameId.substring(0, 8)}...
            <IconButton
              aria-label="close"
              onClick={handleCloseSettings}
              sx={{
                position: 'absolute',
                right: 8,
                top: 8,
                color: (theme) => theme.palette.grey[500],
              }}
            >
              <CloseIcon />
            </IconButton>
          </DialogTitle>
          <DialogContent dividers>
            <ManageGame gameId={gameId} isModalOpen={isSettingsOpen} />
          </DialogContent>
        </Dialog>
      )}
    </GameLayout>
  );
};

export default Game; 