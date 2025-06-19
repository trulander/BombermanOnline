// export interface MapTemplate {
//     id: string;
//     name: string;
// }

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

export interface MapGroup {
    id: string;
    name: string;
    created_at: string;
    updated_at: string;
}

export interface MapChain {
    id: string;
    name: string;
    description?: string;
    map_template_ids: string[];
    created_by: string;
    created_at: string;
    updated_at: string;
}

export enum CellType {
    EMPTY = 0,
    SOLID_WALL = 1,
    BREAKABLE_BLOCK = 2,
    PLAYER_SPAWN = 3,
    ENEMY_SPAWN = 4,
    LEVEL_EXIT = 5,
}

export const cellTypeColors: Record<CellType, string> = {
    [CellType.EMPTY]: '#eee',
    [CellType.SOLID_WALL]: '#555',
    [CellType.BREAKABLE_BLOCK]: '#aaa',
    [CellType.PLAYER_SPAWN]: '#00f',
    [CellType.ENEMY_SPAWN]: '#f00',
    [CellType.LEVEL_EXIT]: '#0f0',
};