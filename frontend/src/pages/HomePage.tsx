import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, Plus, Heart, MessageCircle, TrendingUp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { CollectionService } from '@/services/collectionService'
import { Collection, Platform } from '@/types'

const HomePage = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const [collections, setCollections] = useState<Collection[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  // 图片代理URL
  const getProxyImageUrl = (url: string) => {
    if (!url) return ''
    return `/proxy-image/?url=${url}`
  }

  useEffect(() => {
    loadCollections()
  }, [])

  const loadCollections = async () => {
    try {
      setLoading(true)
      const data = await CollectionService.getCollections({ limit: 12 })
      setCollections(data || [])
    } catch (error) {
      console.error('Failed to load collections:', error)
      setCollections([])
    } finally {
      setLoading(false)
    }
  }

  const getPlatformColor = (platform: Platform) => {
    switch (platform) {
      case Platform.XIAOHONGSHU:
        return 'bg-red-500'
      case Platform.WECHAT:
        return 'bg-green-500'
      case Platform.BILIBILI:
        return 'bg-blue-500'
      default:
        return 'bg-gray-500'
    }
  }

  const filteredCollections = (collections || []).filter(collection =>
    collection.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (collection.author && collection.author.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              发现精彩内容，
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                {' '}一站式收藏
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto">
              聚合小红书、微信、B站等多个平台的优质内容，通过AI智能分类，让您的收藏井井有条
            </p>
            
            {!isAuthenticated && (
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => navigate('/register')}
                  className="px-8 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors shadow-lg hover:shadow-xl"
                >
                  立即注册
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="px-8 py-3 bg-white text-indigo-600 font-medium rounded-lg border-2 border-indigo-600 hover:bg-indigo-50 transition-colors"
                >
                  登录账户
                </button>
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-shadow"
          >
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <Plus className="w-6 h-6 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">一键收藏</h3>
            <p className="text-gray-600">通过机器人助手，只需发送链接即可自动收藏到您的个人空间</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-shadow"
          >
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Heart className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">AI智能分类</h3>
            <p className="text-gray-600">利用AI技术自动为您收藏的内容进行智能分类和标签化管理</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-shadow"
          >
            <div className="w-12 h-12 bg-cyan-100 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="w-6 h-6 text-cyan-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">热门追踪</h3>
            <p className="text-gray-600">实时抓取各大平台热门内容，让您不错过任何精彩资讯</p>
          </motion.div>
        </div>

        {/* Recent Collections */}
        {isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900">最近收藏</h2>
              <button
                onClick={() => navigate('/collections')}
                className="text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-2"
              >
                查看全部
                <MessageCircle className="w-4 h-4" />
              </button>
            </div>

            {/* Search Bar */}
            <div className="mb-8 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="搜索收藏内容..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-white rounded-xl shadow-md p-6 animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                    <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredCollections.map((collection) => (
                  <motion.div
                    key={collection.id}
                    whileHover={{ y: -5 }}
                    className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer"
                    onClick={() => navigate(`/collections/${collection.id}`)}
                  >
                    {collection.cover_image && (
                      <div className="relative h-48 overflow-hidden">
                        <img
                          src={getProxyImageUrl(collection.cover_image)}
                          alt={collection.title}
                          className="w-full h-full object-cover"
                        />
                        <div className={`absolute top-3 left-3 ${getPlatformColor(collection.platform)} text-white text-xs px-2 py-1 rounded-full`}>
                          {collection.platform}
                        </div>
                      </div>
                    )}
                    <div className="p-6">
                      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{collection.title}</h3>
                      {collection.author && (
                        <p className="text-sm text-gray-600 mb-3">作者: {collection.author}</p>
                      )}
                      {collection.content && (
                        <p className="text-gray-700 text-sm mb-4 line-clamp-3">{collection.content}</p>
                      )}
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>{new Date(collection.collected_at).toLocaleDateString()}</span>
                          <span className="flex items-center gap-1">
                            <Heart className="w-4 h-4" />
                            {collection.like_count}
                          </span>
                        </div>
                        {collection.category && (
                          <span className="bg-indigo-100 text-indigo-800 text-xs px-2 py-1 rounded-full">
                            {collection.category}
                          </span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default HomePage