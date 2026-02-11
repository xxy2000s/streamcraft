export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface Collection {
  id: number
  user_id: number
  platform: Platform
  content_id: string
  title: string
  content?: string
  url?: string
  author?: string
  cover_image?: string
  content_type: ContentType
  category?: string
  tags?: string[]
  collected_at: string
  created_at: string
  updated_at: string
  like_count: number
}

export interface Category {
  id: number
  name: string
  description?: string
  color?: string
  created_at: string
}

export interface Tag {
  id: number
  name: string
  created_at: string
}

export interface HotContent {
  id: number
  platform: Platform
  title: string
  url: string
  hot_score: number
  crawled_at: string
  created_at: string
}

export enum Platform {
  XIAOHONGSHU = 'xiaohongshu',
  WECHAT = 'wechat',
  BILIBILI = 'bilibili',
  OTHER = 'other'
}

export enum ContentType {
  POST = 'post',
  VIDEO = 'video',
  ARTICLE = 'article',
  IMAGE = 'image'
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}