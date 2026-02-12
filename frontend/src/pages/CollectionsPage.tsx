import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, Heart, Grid, List, FolderPlus, MoreHorizontal, Plus, X, Link as LinkIcon, RefreshCw, ArrowLeft, Trash2 } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { CollectionService } from '@/services/collectionService'
import { CategoryService } from '@/services/categoryService'
import { Collection, Platform, Category, ContentType } from '@/types'

const CollectionsPage = () => {
  const navigate = useNavigate()
  const { id } = useParams()
  const isDetailView = !!id
  const [collections, setCollections] = useState<Collection[]>([])
  const [currentCollection, setCurrentCollection] = useState<Collection | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all')
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [activeDropdown, setActiveDropdown] = useState<number | null>(null)
  const [showCategoryModal, setShowCategoryModal] = useState(false)
  const [collectionToCategorize, setCollectionToCategorize] = useState<Collection | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [parsingUrl, setParsingUrl] = useState(false)
  const [isBatchMode, setIsBatchMode] = useState(false)
  const [selectedCollectionIds, setSelectedCollectionIds] = useState<Set<number>>(new Set())
  const [formData, setFormData] = useState({
    platform: Platform.OTHER,
    content_id: '',
    title: '',
    content: '',
    url: '',
    author: '',
    cover_image: '',
    content_type: ContentType.POST,
    category_id: undefined as number | undefined,
    tags: [] as string[]
  })

  useEffect(() => {
    if (isDetailView && id) {
      loadCollectionDetail(Number(id))
    } else {
      loadCollections()
    }
    loadCategories()
  }, [id, isDetailView])

  useEffect(() => {
    loadCollections()
  }, [selectedCategoryId])

  const loadCollections = async () => {
    try {
      setLoading(true)
      const params: any = { limit: 100 }
      if (selectedCategoryId) {
        params.category_id = selectedCategoryId
      }
      const data = await CollectionService.getCollections(params)
      setCollections(data)
    } catch (error) {
      toast.error('加载收藏失败')
    } finally {
      setLoading(false)
    }
  }

  const loadCollectionDetail = async (collectionId: number) => {
    try {
      setLoading(true)
      const data = await CollectionService.getCollection(collectionId)
      setCurrentCollection(data)
    } catch (error) {
      toast.error('加载收藏详情失败')
      navigate('/collections')
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const data = await CategoryService.getCategories()
      setCategories(data)
    } catch (error) {
      console.error('Failed to load categories:', error)
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
      case Platform.ZHIHU:
        return 'bg-blue-600'
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

  const handleLike = async (e: React.MouseEvent, collection: Collection) => {
    e.stopPropagation()
    try {
      await CollectionService.likeCollection(collection.id)
      setCollections(prev =>
        prev.map(c =>
          c.id === collection.id
            ? { ...c, like_count: c.like_count + 1 }
            : c
        )
      )
      toast.success('点赞成功')
    } catch (error) {
      toast.error('点赞失败')
    }
  }

  const handleSetCategory = (collection: Collection) => {
    setCollectionToCategorize(collection)
    setShowCategoryModal(true)
  }

  const handleSelectCategory = async (categoryId: number | null) => {
    if (!collectionToCategorize) return
    try {
      await CollectionService.updateCollection(collectionToCategorize.id, { category_id: categoryId || undefined })
      toast.success('分类设置成功')
      setShowCategoryModal(false)
      loadCollections()
    } catch (error) {
      toast.error('设置分类失败')
    }
  }

  const handleDeleteCollection = async (collectionId: number) => {
    if (!confirm('确定要删除这个收藏吗？')) return
    try {
      await CollectionService.deleteCollection(collectionId)
      toast.success('删除成功')
      loadCollections()
    } catch (error) {
      toast.error('删除失败')
    }
  }

  const toggleCollectionSelection = (collectionId: number) => {
    const newSelection = new Set(selectedCollectionIds)
    if (newSelection.has(collectionId)) {
      newSelection.delete(collectionId)
    } else {
      newSelection.add(collectionId)
    }
    setSelectedCollectionIds(newSelection)
  }

  const handleBatchDelete = async () => {
    if (selectedCollectionIds.size === 0) {
      toast.error('请先选择要删除的收藏')
      return
    }
    if (!confirm(`确定要删除选中的 ${selectedCollectionIds.size} 个收藏吗？`)) return
    try {
      await Promise.all(Array.from(selectedCollectionIds).map(id => CollectionService.deleteCollection(id)))
      toast.success('批量删除成功')
      setSelectedCollectionIds(new Set())
      setIsBatchMode(false)
      loadCollections()
    } catch (error) {
      toast.error('批量删除失败')
    }
  }

  const getCategoryForCollection = (collection: Collection) => {
    if (collection.category_id) {
      return categories.find(c => c.id === collection.category_id)
    }
    return null
  }

  const getImageUrl = (url: string | undefined) => {
    if (!url) return ''
    // 如果是外部图片URL，使用代理
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return `/proxy-image/?url=${url}`
    }
    return url
  }

  const handleAddCollection = () => {
    setFormData({
      platform: Platform.OTHER,
      content_id: '',
      title: '',
      content: '',
      url: '',
      author: '',
      cover_image: '',
      content_type: ContentType.POST,
      category_id: undefined,
      tags: []
    })
    setShowAddModal(true)
  }

  const handleParseUrl = async () => {
    if (!formData.url.trim()) {
      toast.error('请输入链接')
      return
    }

    setParsingUrl(true)
    try {
      const parsed = await CollectionService.parseUrl(formData.url)
      setFormData({
        ...formData,
        platform: parsed.platform as Platform,
        content_id: parsed.content_id,
        title: parsed.title,
        content: parsed.content,
        url: parsed.url,
        cover_image: parsed.cover_image,
        content_type: parsed.content_type as ContentType
      })
      
      // 检查是否成功提取到内容
      if (!parsed.title && !parsed.cover_image) {
        toast.success('链接已识别，请手动填写标题和封面图')
      } else {
        toast.success('链接解析成功')
      }
    } catch (error) {
      toast.error('链接解析失败，请手动填写')
    } finally {
      setParsingUrl(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim()) {
      toast.error('请输入标题')
      return
    }
    
    if (!formData.content_id.trim()) {
      toast.error('请输入内容ID')
      return
    }

    try {
      await CollectionService.createCollection(formData)
      toast.success('添加收藏成功')
      setShowAddModal(false)
      loadCollections()
    } catch (error) {
      toast.error('添加收藏失败')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 详情视图 */}
        {isDetailView && currentCollection ? (
          <div>
            <button
              onClick={() => navigate('/collections')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              返回列表
            </button>
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              {currentCollection.cover_image ? (
                <div className="relative w-full h-64 bg-gray-100">
                  <img
                    src={getImageUrl(currentCollection.cover_image)}
                    alt={currentCollection.title}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="w-full h-64 bg-gray-200 flex items-center justify-center">
                  <span className="text-gray-400">无封面图</span>
                </div>
              )}
              <div className="p-8">
                <div className="flex items-center gap-2 mb-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPlatformColor(currentCollection.platform)} text-white`}>
                    {currentCollection.platform}
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                    {currentCollection.content_type}
                  </span>
                </div>
                <h1 className="text-3xl font-bold text-gray-900 mb-4">{currentCollection.title}</h1>
                {currentCollection.author && (
                  <p className="text-gray-600 mb-4">作者: {currentCollection.author}</p>
                )}
                {currentCollection.content && (
                  <div className="prose max-w-none mb-6">
                    <p className="text-gray-700 whitespace-pre-wrap">{currentCollection.content}</p>
                  </div>
                )}
                {currentCollection.url && (
                  <a
                    href={currentCollection.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    查看原文
                  </a>
                )}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <p className="text-sm text-gray-500">
                    收藏时间: {new Date(currentCollection.collected_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* 列表视图 */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">我的收藏</h1>
              <p className="text-gray-600">管理和浏览您收藏的所有内容</p>
            </div>

            {/* 搜索和筛选栏 */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
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

            <div className="flex flex-wrap gap-2">
              {isBatchMode && (
                <div className="flex items-center gap-2 mr-4">
                  <span className="text-sm text-gray-600">已选择 {selectedCollectionIds.size} 项</span>
                  <button
                    onClick={handleBatchDelete}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    批量删除
                  </button>
                  <button
                    onClick={() => {
                      setIsBatchMode(false)
                      setSelectedCollectionIds(new Set())
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    取消
                  </button>
                </div>
              )}

              <button
                onClick={() => {
                  setIsBatchMode(!isBatchMode)
                  setSelectedCollectionIds(new Set())
                }}
                className={`px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors ${isBatchMode ? 'bg-indigo-100 text-indigo-600' : ''}`}
              >
                {isBatchMode ? '退出批量' : '批量管理'}
              </button>

              <select
                value={selectedCategoryId || 'all'}
                onChange={(e) => setSelectedCategoryId(e.target.value === 'all' ? null : Number(e.target.value))}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="all">全部分类</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>

              <select
                value={selectedPlatform}
                onChange={(e) => setSelectedPlatform(e.target.value)}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="all">所有平台</option>
                <option value="xiaohongshu">小红书</option>
                <option value="wechat">微信</option>
                <option value="bilibili">B站</option>
                <option value="douyin">抖音</option>
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
                onClick={() => navigate('/categories')}
                className="flex items-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <FolderPlus className="w-5 h-5" />
                管理分类
              </button>
              <button
                onClick={handleAddCollection}
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
            {filteredCollections.map((collection) => {
              const category = getCategoryForCollection(collection)
              return (
                <motion.div
                  key={collection.id}
                  whileHover={{ y: -2 }}
                  className={`bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden ${
                    viewMode === 'list' ? 'flex' : 'flex flex-col'
                  } relative group ${selectedCollectionIds.has(collection.id) ? 'ring-2 ring-indigo-500' : ''}`}
                  style={{ minHeight: viewMode === 'grid' ? '380px' : 'auto' }}
                >
                  {/* 批量选择复选框 */}
                  {isBatchMode && (
                    <div className="absolute top-3 left-3 z-20">
                      <input
                        type="checkbox"
                        checked={selectedCollectionIds.has(collection.id)}
                        onChange={() => toggleCollectionSelection(collection.id)}
                        className="w-5 h-5 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                      />
                    </div>
                  )}

                  {/* 更多操作菜单 */}
                  <div className="absolute top-3 right-3 z-10">
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setActiveDropdown(activeDropdown === collection.id ? null : collection.id)
                        }}
                        className="p-2 bg-white/80 backdrop-blur-sm rounded-lg hover:bg-white shadow-md"
                      >
                        <MoreHorizontal className="w-4 h-4 text-gray-600" />
                      </button>
                      {activeDropdown === collection.id && (
                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-20">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSetCategory(collection)
                              setActiveDropdown(null)
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                          >
                            <FolderPlus className="w-4 h-4" />
                            设置分类
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteCollection(collection.id)
                              setActiveDropdown(null)
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                          >
                            <Trash2 className="w-4 h-4" />
                            删除
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {collection.cover_image && viewMode === 'grid' && (
                    <div className={`relative h-48 overflow-hidden cursor-pointer bg-gray-100 ${isBatchMode ? '' : 'clickable'}`} onClick={() => !isBatchMode && collection.url && window.open(collection.url, '_blank')}>
                      <img
                        src={getImageUrl(collection.cover_image)}
                        alt={collection.title}
                        className="w-full h-full object-cover"
                      />
                      <div className={`absolute top-3 ${isBatchMode ? 'left-12' : 'left-3'} ${getPlatformColor(collection.platform)} text-white text-xs px-2 py-1 rounded-full`}>
                        {collection.platform}
                      </div>
                    </div>
                  )}

                  <div className={viewMode === 'grid' ? "p-6 flex-1" : "p-6 flex-1 cursor-pointer"} onClick={() => !isBatchMode && collection.url && window.open(collection.url, '_blank')}>
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
                        <button
                          onClick={(e) => handleLike(e, collection)}
                          className="flex items-center gap-1 hover:text-red-500 transition-colors"
                        >
                          <Heart className="w-4 h-4" />
                          {collection.like_count}
                        </button>
                      </div>
                      {category && (
                        <span
                          className="text-xs px-2 py-1 rounded-full"
                          style={{
                            backgroundColor: `${category.color}20`,
                            color: category.color
                          }}
                        >
                          {category.name}
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {!loading && filteredCollections.length === 0 && (
          <div className="text-center py-12">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Heart className="w-12 h-12 text-gray-400" />
            </div>
            <h3 className="text-xl font-medium text-gray-900 mb-2">暂无收藏内容</h3>
            <p className="text-gray-600 mb-6">开始收藏您喜欢的内容吧！</p>
          </div>
        )}

        {/* 分类选择模态框 */}
        {showCategoryModal && collectionToCategorize && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">选择分类</h2>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                <button
                  onClick={() => handleSelectCategory(null)}
                  className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  无分类
                </button>
                {categories.map(cat => (
                  <button
                    key={cat.id}
                    onClick={() => handleSelectCategory(cat.id)}
                    className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-3"
                  >
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: cat.color }}
                    />
                    <span>{cat.name}</span>
                  </button>
                ))}
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCategoryModal(false)}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => navigate('/categories')}
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  新建分类
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 添加收藏模态框 */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">添加收藏</h2>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        平台 *
                      </label>
                      <select
                        value={formData.platform}
                        onChange={(e) => setFormData({ ...formData, platform: e.target.value as Platform })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      >
                        <option value={Platform.XIAOHONGSHU}>小红书</option>
                        <option value={Platform.WECHAT}>微信</option>
                        <option value={Platform.BILIBILI}>B站</option>
                        <option value={Platform.DOUYIN}>抖音</option>
                        <option value={Platform.ZHIHU}>知乎</option>
                        <option value={Platform.OTHER}>其他</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        内容类型 *
                      </label>
                      <select
                        value={formData.content_type}
                        onChange={(e) => setFormData({ ...formData, content_type: e.target.value as ContentType })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      >
                        <option value={ContentType.POST}>文章</option>
                        <option value={ContentType.VIDEO}>视频</option>
                        <option value={ContentType.ARTICLE}>图文</option>
                        <option value={ContentType.IMAGE}>图片</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      内容ID *
                    </label>
                    <input
                      type="text"
                      value={formData.content_id}
                      onChange={(e) => setFormData({ ...formData, content_id: e.target.value })}
                      placeholder="平台原始ID"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      标题 *
                    </label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="收藏标题"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      链接
                    </label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <LinkIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                        <input
                          type="url"
                          value={formData.url}
                          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                          placeholder="https://..."
                          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={handleParseUrl}
                        disabled={parsingUrl}
                        className="px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400 flex items-center gap-2 whitespace-nowrap"
                      >
                        <RefreshCw className={`w-4 h-4 ${parsingUrl ? 'animate-spin' : ''}`} />
                        {parsingUrl ? '解析中...' : '解析'}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      作者
                    </label>
                    <input
                      type="text"
                      value={formData.author}
                      onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                      placeholder="作者名称"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      封面图片
                    </label>
                    <input
                      type="url"
                      value={formData.cover_image}
                      onChange={(e) => setFormData({ ...formData, cover_image: e.target.value })}
                      placeholder="https://..."
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      分类
                    </label>
                    <select
                      value={formData.category_id || ''}
                      onChange={(e) => setFormData({ ...formData, category_id: e.target.value ? Number(e.target.value) : undefined })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value="">无分类</option>
                      {categories.map(cat => (
                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      内容
                    </label>
                    <textarea
                      value={formData.content}
                      onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                      placeholder="收藏内容描述"
                      rows={4}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                    />
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    添加收藏
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
          </>
        )}
      </div>
    </div>
  )
}

export default CollectionsPage