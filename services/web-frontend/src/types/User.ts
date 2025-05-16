export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  MODERATOR = 'moderator',
  DEVELOPER = 'developer'
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  profile_image?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
} 