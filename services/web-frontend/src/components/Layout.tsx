import React, { useEffect, useState } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  AppBar, 
  Box, 
  Toolbar, 
  Typography, 
  Button, 
  Container, 
  Paper,
  Menu,
  MenuItem,
  IconButton,
  Avatar
} from '@mui/material';
import { AccountCircle, ArrowBack, Settings } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { GameStatus } from '../types/Game';

interface LayoutProps {
  children?: React.ReactNode;
  showGameSpecificInfo?: boolean;
  onOpenGameSettings?: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, showGameSpecificInfo = false, onOpenGameSettings }) => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const [gameId, setGameId] = useState<string>('');
  const [level, setLevel] = useState<number>(1);
  const [status, setStatus] = useState<GameStatus>(GameStatus.PENDING);

  useEffect(() => {
    const handleGameIdUpdate = (event: CustomEvent<string>) => {
      setGameId(event.detail);
    };

    const handleLevelUpdate = (event: CustomEvent<number>) => {
      setLevel(event.detail);
    };

    const handleStatusUpdate = (event: CustomEvent<GameStatus>) => {
      setStatus(event.detail);
    };

    window.addEventListener('gameIdUpdate', handleGameIdUpdate as EventListener);
    window.addEventListener('levelUpdate', handleLevelUpdate as EventListener);
    window.addEventListener('statusUpdate', handleStatusUpdate as EventListener);

    return () => {
      window.removeEventListener('gameIdUpdate', handleGameIdUpdate as EventListener);
      window.removeEventListener('levelUpdate', handleLevelUpdate as EventListener);
      window.removeEventListener('statusUpdate', handleStatusUpdate as EventListener);
    };
  }, []);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleClose();
    await logout();
    navigate('/account/login');
  };

  const handleProfile = () => {
    handleClose();
    navigate('/account/profile');
  };

  const dontShowBackButton = !location.pathname.startsWith('/account/dashboard');

  const handleBack = () => {
    navigate(-1);
  };

  const getStatusLabel = (s: GameStatus) => {
    switch (s) {
      case GameStatus.PENDING: return 'Ожидание';
      case GameStatus.ACTIVE: return 'Активна';
      case GameStatus.PAUSED: return 'Пауза';
      case GameStatus.FINISHED: return 'Завершена';
      default: return 'Неизвестно';
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          {dontShowBackButton && (
            <IconButton
              edge="start"
              color="inherit"
              aria-label="back"
              onClick={handleBack}
              sx={{ mr: 2 }}
            >
              <ArrowBack />
            </IconButton>
          )}

          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link to={isAuthenticated ? '/account/dashboard' : '/'} style={{ color: 'white', textDecoration: 'none' }}>
              Bomberman Online
            </Link>
          </Typography>
          
          {isAuthenticated && showGameSpecificInfo && gameId && (
            <>
              <Typography variant="body1" sx={{ mr: 3, fontFamily: 'monospace' }}>
                Game ID: {gameId.substring(0, 8)}...
              </Typography>
              <Typography variant="body1" sx={{ mr: 2 }}>
                Уровень: {level}
              </Typography>
              <Typography variant="body1" sx={{ mr: 2 }}>
                Статус: {getStatusLabel(status)}
              </Typography>
            </>
          )}

          {isAuthenticated ? (
            <Box>
              {onOpenGameSettings && showGameSpecificInfo && gameId && (
                <IconButton
                  edge="end"
                  color="inherit"
                  aria-label="settings"
                  onClick={onOpenGameSettings}
                  sx={{ ml: 1 }}
                >
                  <Settings />
                </IconButton>
              )}
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
              >
                {user?.profile_image ? (
                  <Avatar alt={user.username} src={user.profile_image} />
                ) : (
                  <AccountCircle />
                )}
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem onClick={handleProfile}>Профиль</MenuItem>
                <MenuItem onClick={handleLogout}>Выйти</MenuItem>
              </Menu>
            </Box>
          ) : (
            <Box>
              <Button color="inherit" component={Link} to="/account/login">
                Войти
              </Button>
              <Button color="inherit" component={Link} to="/account/register">
                Регистрация
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      
      <Container component="main" 
        sx={{
          mt: showGameSpecificInfo ? 0 : 4,
          mb: showGameSpecificInfo ? 0 : 4,
          flex: '1 0 auto',
          maxWidth: showGameSpecificInfo ? 'none' : 'lg',
          p: showGameSpecificInfo ? 0 : 4,
          bgcolor: showGameSpecificInfo ? '#000' : 'background.paper',
          borderRadius: showGameSpecificInfo ? 0 : 2,
          boxShadow: showGameSpecificInfo ? 'none' : 3,
          display: showGameSpecificInfo ? 'flex' : 'block',
          justifyContent: showGameSpecificInfo ? 'center' : 'unset',
          alignItems: showGameSpecificInfo ? 'center' : 'unset',
          overflow: showGameSpecificInfo ? 'hidden' : 'visible',
        }}
      >
        {children || <Outlet />}
      </Container>
      
      <Box component="footer" sx={{ py: 3, bgcolor: 'background.paper', marginTop: 'auto' }}>
        <Container maxWidth="sm">
          <Typography variant="body2" color="text.secondary" align="center">
            {'© '}
            {new Date().getFullYear()}
            {' Bomberman Online. Все права защищены.'}
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout; 