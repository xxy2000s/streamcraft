import { apiClient } from './apiClient'
import { Collection } from '@/types'

export interface CollectionQueryParams {
  skip?: number
  limit?: number
  platform?: string
  category?: string
}

export class CollectionService {
  static async getCollections(params?: CollectionQueryParams): Promise<Collection[]> {
    const response = await apiClient.get<Collection[]>('/collections', { params })
    return response.data.data || []
  }

  static async getCollection(id: number): Promise<Collection> {
    const response = await apiClient.get<Collection>(`/collections/${id}`)
    return response.data.data!
  }

  static async createCollection(collection: Partial<Collection>): Promise<Collection> {
    const response = await apiClient.post<Collection>('/collections', collection)
    return response.data.data!
  }

  static async updateCollection(id: number, updates: Partial<Collection>): Promise<Collection> {
    const response = await apiClient.put<Collection>(`/collections/${id}`, updates)
    return response.data.data!
  }

  static async deleteCollection(id: number): Promise<void> {
    await apiClient.delete(`/collections/${id}`)
  }

  static async likeCollection(id: number): Promise<void> {
    await apiClient.post(`/collections/${id}/like`)
  }

  static async unlikeCollection(id: number): Promise<void> {
    await apiClient.delete(`/collections/${id}/like`)
  }
}