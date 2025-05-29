import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
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
import { AccountCircle } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

const Layout: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

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

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link to={isAuthenticated ? '/account/dashboard' : '/'} style={{ color: 'white', textDecoration: 'none' }}>
              Bomberman Online
            </Link>
          </Typography>
          
          {isAuthenticated ? (
            <div>
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
            </div>
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
      
      <Container component="main" sx={{ mt: 4, mb: 4, flex: '1 0 auto' }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Outlet />
        </Paper>
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