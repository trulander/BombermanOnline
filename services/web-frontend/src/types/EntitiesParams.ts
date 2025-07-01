import {EnemyType, PowerUpType, UnitType, WeaponType} from "./Game";

export interface EntitiesInfo {
  cell_types: CellTypes;
  game_modes: GameModes;
  game_statuses: GameStatuses;
  enemy_types: Record<EnemyType, EntityInfo>;
  power_up_types: Record<PowerUpType, EntityInfo>;
  player_units: Record<UnitType, UnitInfo>;
  weapon_types: Record<WeaponType, EntityInfo>;
}

export interface CellTypes {
  EMPTY: number;
  SOLID_WALL: number;
  BREAKABLE_BLOCK: number;
  PLAYER_SPAWN: number;
  ENEMY_SPAWN: number;
  LEVEL_EXIT: number;
}

export interface GameModes {
  CAMPAIGN: "campaign";
  FREE_FOR_ALL: "free_for_all";
  CAPTURE_THE_FLAG: "capture_the_flag";
}

export interface GameStatuses {
  PENDING: "pending";
  ACTIVE: "active";
  PAUSED: "paused";
  FINISHED: "finished";
}

export interface EntityInfo {
  value: string;
  width: number;
  height: number;
}

export interface UnitInfo {
  name: string;
  width: number;
  height: number;
}