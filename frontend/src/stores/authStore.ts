import { create } from 'zustand'
import { User } from '@/types'
import { AuthService } from '@/services/authService'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => void
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: AuthService.getCurrentUserFromStorage(),
  isAuthenticated: AuthService.isAuthenticated(),
  isLoading: false,

  login: async (username, password) => {
    set({ isLoading: true })
    try {
      const response = await AuthService.login({ username, password })
      // 先保存 token，这样后续请求才能通过认证
      localStorage.setItem('access_token', response.access_token)
      const user = await AuthService.getCurrentUser()
      AuthService.setAuth(response.access_token, user)
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  register: async (username, email, password) => {
    set({ isLoading: true })
    try {
      await AuthService.register({ username, email, password })
      set({ isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  logout: () => {
    AuthService.logout()
    set({ user: null, isAuthenticated: false })
  },

  checkAuth: () => {
    const isAuthenticated = AuthService.isAuthenticated()
    const user = AuthService.getCurrentUserFromStorage()
    set({ isAuthenticated, user })
  },

  setUser: (user) => {
    set({ user, isAuthenticated: !!user })
    if (user) {
      localStorage.setItem('user', JSON.stringify(user))
    } else {
      localStorage.removeItem('user')
    }
  }
}))