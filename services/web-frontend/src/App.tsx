import React from 'react';
import { Routes, Route, Navigate, useParams } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import ResetPassword from './pages/ResetPassword';
import ConfirmResetPassword from './pages/ConfirmResetPassword';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Stats from './pages/Stats';
import NotFound from './pages/NotFound';
import Game from './pages/Game';
import CreateGame from './pages/CreateGame';
import ManageGame from './pages/ManageGame';
import MapEditor from './pages/MapEditor';
import GameList from './pages/GameList';

// Layout components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        {/* Главная страница - доступна всем */}
        <Route path="/" element={<Home />} />

        <Route path="/account" element={<Layout />}>
          {/* Публичные маршруты - доступны только НЕ авторизованным */}
          <Route path="login" element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } />
          <Route path="register" element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } />
          <Route path="reset-password" element={
            <PublicRoute>
              <ResetPassword />
            </PublicRoute>
          } />
          <Route path="confirm-reset-password" element={
            <PublicRoute>
              <ConfirmResetPassword />
            </PublicRoute>
          } />
          
          {/* Верификация email - доступна всем */}
          <Route path="verify-email" element={<VerifyEmail />} />
          
          {/* Защищенные маршруты - только для авторизованных */}
          <Route path="dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="profile" element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />
          <Route path="stats" element={
            <ProtectedRoute>
              <Stats />
            </ProtectedRoute>
          } />

          <Route path="games/create" element={
            <ProtectedRoute>
              <CreateGame />
            </ProtectedRoute>
          } />

          {/* Игровая страница - отдельно от основного Layout */}
          <Route path="game/:gameId" element={
            <ProtectedRoute>
              <Game />
            </ProtectedRoute>
          } />

          <Route path="games/:gameId/manage" element={
            <ProtectedRoute>
              <GameManagementWrapper />
            </ProtectedRoute>
          } />

          <Route path="games" element={
            <ProtectedRoute>
              <GameList />
            </ProtectedRoute>
          } />

          <Route path="maps/editor" element={
            <ProtectedRoute>
              <MapEditor />
            </ProtectedRoute>
          } />

          
          {/* Редирект с корневого маршрута на login для неавторизованных */}
          <Route index element={<Navigate to="/account/login" replace />} />
        </Route>
        
        {/* 404 страница */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ThemeProvider>
  );
};

const GameManagementWrapper: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  return gameId ? <ManageGame gameId={gameId} /> : null;
};

export default App; 