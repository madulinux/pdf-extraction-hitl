/**
 * Auth API
 * Authentication endpoints
 */
import { apiClient } from './client';
import { User, TokenPair, LoginRequest, RegisterRequest } from '../types/auth.types';

export const authAPI = {
  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<{ user: User }> {
    const response = await apiClient.post<{ user: User }>('/v1/auth/register', data);
    return response.data.data!;
  },

  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<{ tokens: TokenPair }> {
    const response = await apiClient.post<{ tokens: TokenPair }>('/v1/auth/login', data);
    
    // Save tokens
    const tokens = response.data.data!.tokens;
    apiClient.saveToken(tokens.access_token);
    apiClient.saveRefreshToken(tokens.refresh_token);
    
    return response.data.data!;
  },

  /**
   * Logout user
   */
  async logout(refreshToken: string): Promise<void> {
    try {
      const response = await apiClient.post('/v1/auth/logout', { refresh_token: refreshToken });
    } finally {
      apiClient.clearTokens();
    }
  },

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<{ user: User }> {
    const response = await apiClient.get<{ user: User }>('/v1/auth/me');
    return response.data.data!;
  },

  /**
   * Verify token
   */
  async verifyToken(): Promise<{ user_id: number; username: string; role: string }> {
    const response = await apiClient.post('/v1/auth/verify');
    return response.data.data! as { user_id: number; username: string; role: string };
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<{ tokens: TokenPair }> {
    const response = await apiClient.post<{ tokens: TokenPair }>('/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    
    // Save new tokens
    const tokens = response.data.data!.tokens;
    apiClient.saveToken(tokens.access_token);
    apiClient.saveRefreshToken(tokens.refresh_token);
    
    return response.data.data!;
  },
};
