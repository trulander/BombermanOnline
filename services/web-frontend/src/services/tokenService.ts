export interface TokenData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

class TokenService {
  private static instance: TokenService;

  public static getInstance(): TokenService {
    if (!TokenService.instance) {
      TokenService.instance = new TokenService();
    }
    return TokenService.instance;
  }

  // Получение access токена
  public getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // Получение refresh токена
  public getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  // Сохранение токенов
  public saveTokens(tokenData: TokenData): void {
    localStorage.setItem('access_token', tokenData.access_token);
    localStorage.setItem('refresh_token', tokenData.refresh_token);
    localStorage.setItem('token_type', tokenData.token_type || 'bearer');
    localStorage.setItem('expires_in', tokenData.expires_in?.toString() || '1800');
    localStorage.setItem('token_time', Date.now().toString());
    
    // Создаем cookie для WebSocket авторизации
    this.setWebSocketAuthCookie(tokenData.access_token, tokenData.expires_in);
  }

  // Создание cookie для WebSocket авторизации
  private setWebSocketAuthCookie(token: string, expiresIn: number): void {
    const expiresInMs = expiresIn * 1000;
    const expires = new Date(Date.now() + expiresInMs);
    
    // Определяем нужен ли Secure флаг (только для HTTPS)
    const isSecure = window.location.protocol === 'https:';
    const secureFlag = isSecure ? '; Secure' : '';
    
    // Создаем две cookie:
    // 1. Для WebSocket endpoint (будет отправляться только на /socket.io/)
    const wsPathCookieValue = `ws_auth_token=${token}; path=/socket.io/; expires=${expires.toUTCString()}; SameSite=Lax${secureFlag}`;
    document.cookie = wsPathCookieValue;
    
    // 2. Для чтения из JavaScript на других страницах (корневой path)
    const rootPathCookieValue = `ws_auth_token=${token}; path=/; expires=${expires.toUTCString()}; SameSite=Lax${secureFlag}`;
    document.cookie = rootPathCookieValue;
    
    console.log('WebSocket auth cookie set', {
      wsPath: '/socket.io/',
      rootPath: '/',
      expires: expires.toISOString(),
      hasToken: !!token,
      isSecure,
      protocol: window.location.protocol,
      currentPath: window.location.pathname
    });
  }

  // Очистка токенов
  public clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('expires_in');
    localStorage.removeItem('token_time');
    
    // Удаляем WebSocket cookie
    this.clearWebSocketAuthCookie();
  }

  // Удаление WebSocket cookie
  private clearWebSocketAuthCookie(): void {
    // Определяем нужен ли Secure флаг (только для HTTPS)
    const isSecure = window.location.protocol === 'https:';
    const secureFlag = isSecure ? '; Secure' : '';
    
    // Удаляем обе cookie (с разными path)
    document.cookie = `ws_auth_token=; path=/socket.io/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax${secureFlag}`;
    document.cookie = `ws_auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax${secureFlag}`;
    console.log('WebSocket auth cookie cleared from both paths');
  }

  // Проверка наличия токенов
  public hasTokens(): boolean {
    return !!(this.getAccessToken() && this.getRefreshToken());
  }

  // Обновление токена через API
  public async refreshToken(): Promise<TokenData | null> {
    const refreshToken = this.getRefreshToken();
    
    if (!refreshToken) {
      return null;
    }
    
    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      });
      
      if (response.ok) {
        const tokenData: TokenData = await response.json();
        this.saveTokens(tokenData);
        return tokenData;
      } else {
        // Если refresh не удался, очищаем токены
        this.clearTokens();
        return null;
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
      this.clearTokens();
      return null;
    }
  }

  // Проверка на истечение токена (приблизительная)
  public isTokenExpired(): boolean {
    const tokenTime = localStorage.getItem('token_time');
    const expiresIn = localStorage.getItem('expires_in');
    
    if (!tokenTime || !expiresIn) {
      return true;
    }
    
    const tokenTimestamp = parseInt(tokenTime);
    const expiresInSeconds = parseInt(expiresIn);
    const now = Date.now();
    
    // Добавляем 5 минут буфера
    const bufferTime = 5 * 60 * 1000;
    return now > (tokenTimestamp + (expiresInSeconds * 1000) - bufferTime);
  }

  // Получение WebSocket cookie (для отладки)
  public getWebSocketAuthCookie(): string | null {
    const allCookies = document.cookie;
    console.log('All cookies:', allCookies);
    
    const cookies = allCookies.split(';');
    console.log('Parsed cookies:', cookies);
    
    for (const cookie of cookies) {
      const trimmedCookie = cookie.trim();
      const equalsIndex = trimmedCookie.indexOf('=');
      
      if (equalsIndex === -1) continue;
      
      const name = trimmedCookie.substring(0, equalsIndex);
      const value = trimmedCookie.substring(equalsIndex + 1);
      
      console.log(`Cookie: name="${name}", value="${value}"`);
      
      if (name === 'ws_auth_token') {
        console.log('Found ws_auth_token:', value);
        return value;
      }
    }
    
    console.log('ws_auth_token cookie not found');
    return null;
  }
}

export const tokenService = TokenService.getInstance(); 