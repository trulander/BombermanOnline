// Определения типов данных (на основе game_routes.py и team_routes.py)
import {GameClient} from "../components/GameClient";
import React from "react";
import {MapUpdate} from "./Map";
import {EntitiesInfo} from "./EntitiesParams";

export enum GameStatus {
    PENDING = 'pending',
    ACTIVE = 'active',
    PAUSED = 'paused',
    FINISHED = 'finished',
}

export enum GameModeType {
    CAMPAIGN = "campaign",                 // Прохождение с возможностью кооператива
    FREE_FOR_ALL = "free_for_all",         // Все против всех (количество игроков = количество команд)
    CAPTURE_THE_FLAG = "capture_the_flag",  // Командная игра с флагами
}

export enum UnitType {
    BOMBERMAN = 'bomberman',
    TANK = 'tank',
}

export enum WeaponType {
    BOMB = "bomb",
    BULLET = "bullet",
    MINE = "mine",
}

export enum EnemyType {
    COIN = "coin",
    BEAR = "bear",
    GHOST = "ghost",
}

export enum PowerUpType {
    BOMB_UP = "BOMB_UP",
    BULLET_UP = "BULLET_UP",
    MINE_UP = "MINE_UP",
    BOMB_POWER_UP = "BOMB_POWER_UP",
    BULLET_POWER_UP = "BULLET_POWER_UP",
    SPEED_UP = "SPEED_UP",
    LIFE_UP = "LIFE_UP"
    // MINE_POWER_UP = "MINE_POWER_UP"
}

export interface MapTemplate {
    id: string;
    name: string;
    description?: string;
    grid_data: number[][];
    width: number;
    height: number;
    difficulty: number;
    max_players: number;
    created_by: string;
    created_at: string;
    updated_at: string;
}

export interface GamePlayerInfo {
    name?: string;
    team_id?: string;
    player_id: string;
    x: number;
    y: number;
    lives: number;
    primary_weapon: WeaponType;
    primary_weapon_max_count: number;
    primary_weapon_power: number;
    secondary_weapon?: WeaponType;
    secondary_weapon_max_count?: number;
    secondary_weapon_power?: number;
    invulnerable: boolean;
    color: string;
    unit_type: UnitType;
}

export interface EnemyState {
    x: number,
    y: number,
    type: EnemyType,
    lives: number,
    invulnerable: boolean,
    destroyed: boolean,
}

export interface WeaponState {
  x: number;
  y: number;
  type: WeaponType;
  direction?: [number, number];
  activated: boolean;
  exploded: boolean;
  explosion_cells: [number, number][];
  owner_id: string;
}

export interface PowerUpState {
    x: number,
    y: number,
    type: PowerUpType,
}

export interface MapData {
  grid: number[][] | null;
  width: number;
  height: number;
}

export interface GameTeamInfo {
    id: string;
    name: string;
    score: number;
    player_ids: string[];
    player_count: number;
}

export interface GameUpdateEvent {
  status: GameStatus;
  is_active: boolean;
  error?: boolean; // по умолчанию False → необязательное с типом boolean
  message?: string | null;
  map_update?: MapUpdate[] | null;
  game_id?: string | null;
}




export interface TeamModeSettings {
  game_mode: GameModeType;

  default_team_count: number;
  max_team_count: number;
  min_players_per_team: number;
  max_players_per_team: number;

  auto_distribute_players: boolean;
  allow_uneven_teams: boolean;

  default_team_names: string[];
}

export interface GameSettings {
  // Базовые настройки
  cell_size: number;
  default_map_width: number;
  default_map_height: number;
  destroy_animation_time: number;

  // Настройки игрока
  player_default_speed: number;
  player_invulnerable_time: number;
  player_max_speed: number;
  player_max_lives: number;

  // Настройки оружия
  bomb_timer: number;
  bomb_explosion_duration: number;
  default_bomb_power: number;
  default_max_bombs: number;
  bullet_speed: number;
  mine_timer: number;

  // Настройки врагов
  enemy_count_multiplier: number;
  enemy_invulnerable_time: number;

  // Настройки очков
  block_destroy_score: number;
  enemy_destroy_score: number;
  player_destroy_score: number;
  powerup_collect_score: number;
  level_complete_score: number;

  // Вероятности появления
  powerup_drop_chance: number;
  enemy_powerup_drop_chance: number;

  // Настройки генерации карт
  enable_snake_walls: boolean;
  allow_enemies_near_players: boolean;
  min_distance_from_players: number;

  // Настраиваемые параметры во время создания игры
  game_id: string | null;

  // Режим игры
  game_mode: GameModeType;

  // Настройки игроков и команд
  max_players: number;
  player_start_lives: number;

  // Настройки врагов
  enable_enemies: boolean;

  // Настройки карт
  map_chain_id?: string | null;
  map_template_id?: string | null;

  // Игровые настройки
  respawn_enabled: boolean;
  friendly_fire: boolean;
  time_limit?: number | null;
  score_limit?: number | null;
  rounds_count?: number | null;

  team_mode_settings: TeamModeSettings
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

export interface ManageGameProps {
    gameId: string;
    isModalOpen?: boolean; // New prop
}

export interface GameCreateSettings {
    // Настройки игроков и команд
    max_players?: number;             // = 4
    player_start_lives?: number;      // = 3

    // Настройки врагов
    enable_enemies?: boolean;         // = true

    // Настройки карт
    map_chain_id?: string | null;
    map_template_id?: string | null;

    // Игровые настройки
    respawn_enabled?: boolean;        // = false
    friendly_fire?: boolean;          // = false
    time_limit?: number | null;       // = 300
    score_limit?: number | null;      // = 10
    rounds_count?: number | null;     // = 15
}

export interface GameListItem {
    game_id: string;
    status: GameStatus;
    game_mode: GameModeType;
    current_players_count: number;
    max_players: number;
    level: number;
    created_at: string;
}

export interface GameCanvasProps {
    onGameClientReady?: (gameClient: GameClient | null) => void;
    gameId?: string;
    userId?: string;
    entitiesInfo?: EntitiesInfo
}

export interface GameLayoutProps {
    children: React.ReactNode;
    onOpenSettings?: () => void;
}

export interface GameState {
    players: {
        [playerId: string]: GamePlayerInfo
    };
    enemies: EnemyState[];
    weapons: WeaponState[];
    power_ups: PowerUpState[];
    map: MapData;
    level: number;
    error?: boolean
    is_active?: boolean;
    status: GameStatus,
    teams?: GameTeamInfo
}

export interface ResponseGameState{
    success: boolean,
    game_state: GameState,
    message?: string
}