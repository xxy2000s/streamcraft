import { apiClient } from './apiClient'
import { User, LoginRequest, RegisterRequest, TokenResponse } from '@/types'

export class AuthService {
  static async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/login', credentials)
    return response.data.data!
  }

  static async register(userData: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>('/register', userData)
    return response.data.data!
  }

  static async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/users/me')
    return response.data.data!
  }

  static async logout(): Promise<void> {
    await apiClient.post('/logout')
    apiClient.clearAuth()
  }

  static isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }

  static getToken(): string | null {
    return localStorage.getItem('access_token')
  }

  static setAuth(token: string, user: User): void {
    localStorage.setItem('access_token', token)
    localStorage.setItem('user', JSON.stringify(user))
  }

  static clearAuth(): void {
    apiClient.clearAuth()
  }

  static getCurrentUserFromStorage(): User | null {
    try {
      const userStr = localStorage.getItem('user')
      if (!userStr || userStr === 'undefined') return null
      return JSON.parse(userStr)
    } catch (error) {
      console.error('Failed to parse user from storage:', error)
      localStorage.removeItem('user')
      return null
    }
  }
}