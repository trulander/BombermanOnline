import React, { useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import GameCanvas from '../components/GameCanvas';
import GameLayout from '../components/GameLayout';
import { GameClient } from '../components/GameClient';

const Game: React.FC = () => {
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const gameClientRef = useRef<GameClient | null>(null);
  
  const handleAuthenticationFailed = () => {
    // Перенаправляем на страницу авторизации при ошибке авторизации
    navigate('/account/login');
  };

  const setGameClientRef = (gameClient: GameClient | null) => {
    gameClientRef.current = gameClient;
    if (gameClient) {
      gameClient.setAuthenticationFailedHandler(handleAuthenticationFailed);
    }
  };
  
  return (
    <GameLayout>
      <GameCanvas onGameClientReady={setGameClientRef} gameId={gameId} />
    </GameLayout>
  );
};

export default Game; 