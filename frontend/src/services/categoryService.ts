import { apiClient } from './apiClient'
import { Category } from '@/types'

export interface CategoryCreate {
  name: string
  description?: string
  color?: string
}

export interface CategoryUpdate {
  name?: string
  description?: string
  color?: string
}

export class CategoryService {
  static async getCategories(): Promise<Category[]> {
    const response = await apiClient.get<Category[]>('/categories')
    return response.data.data || []
  }

  static async getCategory(id: number): Promise<Category> {
    const response = await apiClient.get<Category>(`/categories/${id}`)
    return response.data.data!
  }

  static async createCategory(category: CategoryCreate): Promise<Category> {
    const response = await apiClient.post<Category>('/categories', category)
    return response.data.data!
  }

  static async updateCategory(id: number, updates: CategoryUpdate): Promise<Category> {
    const response = await apiClient.put<Category>(`/categories/${id}`, updates)
    return response.data.data!
  }

  static async deleteCategory(id: number): Promise<void> {
    await apiClient.delete(`/categories/${id}`)
  }
}