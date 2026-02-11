import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, Plus, Heart, Grid, List } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { CollectionService } from '@/services/collectionService'
import { Collection, Platform } from '@/types'

const CollectionsPage = () => {
  const navigate = useNavigate()
  const [collections, setCollections] = useState<Collection[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  useEffect(() => {
    loadCollections()
  }, [])

  const loadCollections = async () => {
    try {
      setLoading(true)
      const data = await CollectionService.getCollections()
      setCollections(data)
    } catch (error) {
      console.error('Failed to load collections:', error)
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

  const filteredCollections = collections.filter(collection => {
    const matchesSearch = collection.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (collection.author && collection.author.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesPlatform = selectedPlatform === 'all' || collection.platform === selectedPlatform
    return matchesSearch && matchesPlatform
  })

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">我的收藏</h1>
          <p className="text-gray-600">管理和浏览您收藏的所有内容</p>
        </div>

        {/* 搜索和筛选栏 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="搜索收藏内容..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex gap-2">
              <select
                value={selectedPlatform}
                onChange={(e) => setSelectedPlatform(e.target.value)}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="all">所有平台</option>
                <option value="xiaohongshu">小红书</option>
                <option value="wechat">微信</option>
                <option value="bilibili">B站</option>
              </select>
              
              <div className="flex border border-gray-300 rounded-lg overflow-hidden">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-3 ${viewMode === 'grid' ? 'bg-indigo-100 text-indigo-600' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                >
                  <Grid className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-3 ${viewMode === 'list' ? 'bg-indigo-100 text-indigo-600' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                >
                  <List className="w-5 h-5" />
                </button>
              </div>
              
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                添加收藏
              </button>
            </div>
          </div>
        </div>

        {/* 收藏列表 */}
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
          <div className={viewMode === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            : "space-y-4"
          }>
            {filteredCollections.map((collection) => (
              <motion.div
                key={collection.id}
                whileHover={{ y: -2 }}
                className={`bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer ${
                  viewMode === 'list' ? 'flex' : ''
                }`}
                onClick={() => navigate(`/collections/${collection.id}`)}
              >
                {collection.cover_image && viewMode === 'grid' && (
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={collection.cover_image}
                      alt={collection.title}
                      className="w-full h-full object-cover"
                    />
                    <div className={`absolute top-3 left-3 ${getPlatformColor(collection.platform)} text-white text-xs px-2 py-1 rounded-full`}>
                      {collection.platform}
                    </div>
                  </div>
                )}
                
                <div className={viewMode === 'grid' ? "p-6" : "p-6 flex-1"}>
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

        {!loading && filteredCollections.length === 0 && (
          <div className="text-center py-12">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Heart className="w-12 h-12 text-gray-400" />
            </div>
            <h3 className="text-xl font-medium text-gray-900 mb-2">暂无收藏内容</h3>
            <p className="text-gray-600 mb-6">开始收藏您喜欢的内容吧！</p>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              开始收藏
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default CollectionsPage