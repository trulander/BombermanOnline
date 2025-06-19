import React, { useRef, useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import GameCanvas from '../components/GameCanvas';
import GameLayout from '../components/GameLayout';
import { GameClient } from '../components/GameClient';
import ManageGame from './ManageGame';
import { Dialog, DialogContent, DialogTitle, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useAuth } from '../context/AuthContext';

const Game: React.FC = () => {
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const gameClientRef = useRef<GameClient | null>(null);
  const [searchParams] = useSearchParams();
  const openSettingsOnLoad = searchParams.get('openSettings') === 'true';
  const { user } = useAuth();

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [hasJoinedGame, setHasJoinedGame] = useState(false);

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
  
  return (
    <GameLayout onOpenSettings={hasJoinedGame ? handleOpenSettings : undefined}>
      <GameCanvas onGameClientReady={setGameClientRef} gameId={gameId} userId={user?.id || ''} />
      
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