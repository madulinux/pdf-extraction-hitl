/**
 * API Client
 * Axios client with auth interceptors
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { APIResponse } from '../types/common.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<APIResponse>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Try to refresh token
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/v1/auth/refresh`, {
                refresh_token: refreshToken,
              });

              const { access_token, refresh_token: newRefreshToken } = response.data.data.tokens;

              // Save new tokens
              this.saveToken(access_token);
              this.saveRefreshToken(newRefreshToken);

              // Retry original request
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${access_token}`;
              }
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, logout user
            this.clearTokens();
            if (typeof window !== 'undefined') {
              window.location.href = '/login';
            }
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  public saveToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  public saveRefreshToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('refresh_token', token);
    }
  }

  public clearTokens(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  }

  // HTTP methods
  public get<T>(url: string, config?: InternalAxiosRequestConfig) {
    return this.client.get<APIResponse<T>>(url, config);
  }

  public post<T>(url: string, data?: unknown, config?: InternalAxiosRequestConfig) {
    return this.client.post<APIResponse<T>>(url, data, config);
  }

  public put<T>(url: string, data?: unknown, config?: InternalAxiosRequestConfig) {
    return this.client.put<APIResponse<T>>(url, data, config);
  }

  public delete<T>(url: string, config?: InternalAxiosRequestConfig) {
    return this.client.delete<APIResponse<T>>(url, config);
  }

  public getBlob(url: string, config?: InternalAxiosRequestConfig) {
    return this.client.get<Blob>(url, {
      ...config,
      responseType: 'blob',
    });
  }

  public getClient(): AxiosInstance {
    return this.client;
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
