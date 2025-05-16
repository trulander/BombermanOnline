export interface LoginCredentials {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordReset {
  token: string;
  new_password: string;
} 