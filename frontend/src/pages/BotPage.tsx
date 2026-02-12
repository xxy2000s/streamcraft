import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trash2, CheckSquare, Square, RefreshCw, RotateCcw, Trash } from 'lucide-react';
import apiClient from '../services/apiClient';

interface LinkInfo {
  url: string;
  platform: string;
  content_id?: string;
  short_link: boolean;
}

interface BotMessage {
  id: number;
  message: string;
  source: string;
  parsed_urls: LinkInfo[];
  total_links: number;
  processed: boolean;
  received_at: string;
}

interface TrashMessage extends BotMessage {
  original_id: number;
  deleted_at: string;
  expires_at: string;
  expires_in_days: number;
}

const BotPage: React.FC = () => {
  const [messages, setMessages] = useState<BotMessage[]>([]);
  const [trashMessages, setTrashMessages] = useState<TrashMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testMessage, setTestMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectedTrashIds, setSelectedTrashIds] = useState<Set<number>>(new Set());
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [isTrashBatchMode, setIsTrashBatchMode] = useState(false);
  const [viewMode, setViewMode] = useState<'messages' | 'trash'>('messages');
  const [confirmDialog, setConfirmDialog] = useState<{
    show: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({ show: false, title: '', message: '', onConfirm: () => {} });
  const [toast, setToast] = useState<{ show: boolean; message: string; type: 'success' | 'error' }>({ show: false, message: '', type: 'success' });

  useEffect(() => {
    fetchMessages();
  }, []);

  useEffect(() => {
    if (viewMode === 'trash') {
      fetchTrashMessages();
    }
  }, [viewMode]);

  const fetchMessages = async () => {
    try {
      setLoading(true);
      const response: any = await apiClient.get('/bot/messages?limit=20');
      setMessages(response.data.messages);
      setError(null);
    } catch (err) {
      setError('获取消息失败');
      console.error('Failed to fetch messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrashMessages = async () => {
    try {
      setLoading(true);
      const response: any = await apiClient.get('/bot/trash?limit=20');
      setTrashMessages(response.data.messages);
      setError(null);
    } catch (err) {
      setError('获取回收站消息失败');
      console.error('Failed to fetch trash messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectTrash = (id: number) => {
    const newSelected = new Set(selectedTrashIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedTrashIds(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === messages.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(messages.map(m => m.id)));
    }
  };

  const toggleSelectAllTrash = () => {
    if (selectedTrashIds.size === trashMessages.length) {
      setSelectedTrashIds(new Set());
    } else {
      setSelectedTrashIds(new Set(trashMessages.map(m => m.id)));
    }
  };

  const deleteMessage = (id: number) => {
    setConfirmDialog({
      show: true,
      title: '确认删除',
      message: '确定要删除这条消息吗？删除后可在回收站恢复。',
      onConfirm: async () => {
        setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
        try {
          await apiClient.delete(`/bot/messages/${id}`);
          fetchMessages();
          showToast('消息已移至回收站', 'success');
        } catch (err) {
          showToast('删除失败', 'error');
          console.error('Failed to delete message:', err);
        }
      }
    });
  };

  const batchDelete = () => {
    if (selectedIds.size === 0) {
      showToast('请先选择要删除的消息', 'error');
      return;
    }

    setConfirmDialog({
      show: true,
      title: '确认批量删除',
      message: `确定要删除选中的 ${selectedIds.size} 条消息吗？删除后可在回收站恢复。`,
      onConfirm: async () => {
        setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
        try {
          await apiClient.post('/bot/messages/batch-delete', Array.from(selectedIds));
          setSelectedIds(new Set());
          setIsBatchMode(false);
          fetchMessages();
          showToast('已将选中消息移至回收站', 'success');
        } catch (err) {
          showToast('批量删除失败', 'error');
          console.error('Failed to batch delete:', err);
        }
      }
    });
  };

  const clearAll = () => {
    setConfirmDialog({
      show: true,
      title: '确认清空',
      message: '确定要清空所有消息吗？删除后可在回收站恢复。',
      onConfirm: async () => {
        setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
        try {
          await apiClient.delete('/bot/messages');
          fetchMessages();
          showToast('已将所有消息移至回收站', 'success');
        } catch (err) {
          showToast('清空失败', 'error');
          console.error('Failed to clear all:', err);
        }
      }
    });
  };

  const restoreMessage = (trashId: number) => {
    setConfirmDialog({
      show: true,
      title: '确认恢复',
      message: '确定要恢复这条消息吗？',
      onConfirm: async () => {
        setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
        try {
          await apiClient.post(`/bot/trash/${trashId}/restore`);
          fetchTrashMessages();
          fetchMessages();
          showToast('消息恢复成功', 'success');
        } catch (err) {
          showToast('恢复失败', 'error');
          console.error('Failed to restore message:', err);
        }
      }
    });
  };

  const batchRestoreTrash = () => {
    if (selectedTrashIds.size === 0) {
      showToast('请先选择要恢复的消息', 'error');
      return;
    }

    setConfirmDialog({
      show: true,
      title: '确认批量恢复',
      message: `确定要恢复选中的 ${selectedTrashIds.size} 条消息吗？`,
      onConfirm: async () => {
        setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
        try {
          await Promise.all(
            Array.from(selectedTrashIds).map(id => apiClient.post(`/bot/trash/${id}/restore`))
          );
          setSelectedTrashIds(new Set());
          setIsTrashBatchMode(false);
          fetchTrashMessages();
          fetchMessages();
          showToast(`已恢复 ${selectedTrashIds.size} 条消息`, 'success');
        } catch (err) {
          showToast('批量恢复失败', 'error');
          console.error('Failed to batch restore:', err);
        }
      }
    });
  };

  const permanentDelete = (trashId: number) => {
    setConfirmDialog({
      show: true,
      title: '确认永久删除',
      message: '确定要永久删除这条消息吗？此操作不可恢复！',
      onConfirm: async () => {
        setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
        try {
          await apiClient.delete(`/bot/trash/${trashId}`);
          fetchTrashMessages();
          showToast('消息已永久删除', 'success');
        } catch (err) {
          showToast('永久删除失败', 'error');
          console.error('Failed to permanently delete:', err);
        }
      }
    });
  };

  const clearAllTrash = () => {
    setConfirmDialog({
      show: true,
      title: '确认清空回收站',
      message: '确定要清空回收站吗？此操作将永久删除所有回收站中的消息，不可恢复！',
      onConfirm: async () => {
        setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
        try {
          await apiClient.delete('/bot/trash');
          fetchTrashMessages();
          showToast('回收站已清空', 'success');
        } catch (err) {
          showToast('清空回收站失败', 'error');
          console.error('Failed to clear trash:', err);
        }
      }
    });
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type: 'success' }), 3000);
  };

  const sendTestMessage = async () => {
    if (!testMessage.trim()) return;

    try {
      setSending(true);
      const response = await apiClient.post('/bot/parse', {
        message: testMessage
      }, {
        headers: {
          'Authorization': 'Bearer usXHlHA9f2orfVTODNrYs5Xa1axqTIeA',
          'X-Message-Source': 'web-test'
        }
      });

      if (response.data.success) {
        setTestMessage('');
        fetchMessages();
        showToast('测试消息发送成功！', 'success');
      } else {
        showToast(response.data.message, 'error');
      }
    } catch (err) {
      showToast('发送失败', 'error');
      console.error('Failed to send test message:', err);
    } finally {
      setSending(false);
    }
  };

  const getPlatformColor = (platform: string) => {
    const colors: Record<string, string> = {
      xiaohongshu: 'bg-red-500',
      wechat: 'bg-green-500',
      bilibili: 'bg-pink-500',
      zhihu: 'bg-blue-600',
      douyin: 'bg-black',
      other: 'bg-gray-500'
    };
    return colors[platform] || 'bg-gray-500';
  };

  const getPlatformName = (platform: string) => {
    const names: Record<string, string> = {
      xiaohongshu: '小红书',
      wechat: '微信',
      bilibili: 'B站',
      zhihu: '知乎',
      douyin: '抖音',
      other: '其他'
    };
    return names[platform] || platform;
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getSourceName = (source: string) => {
    const names: Record<string, string> = {
      manual: '手动',
      lark: '飞书',
      feishu: '飞书',
      dingtalk: '钉钉',
      web: '网页',
      api: 'API',
      webhook: 'Webhook',
      slack: 'Slack',
      telegram: 'Telegram',
      unknown: '未知'
    };
    return names[source] || source;
  };

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      manual: 'bg-slate-100 text-slate-700',
      lark: 'bg-blue-100 text-blue-700',
      feishu: 'bg-blue-100 text-blue-700',
      dingtalk: 'bg-red-100 text-red-700',
      web: 'bg-purple-100 text-purple-700',
      api: 'bg-green-100 text-green-700',
      webhook: 'bg-orange-100 text-orange-700',
      slack: 'bg-pink-100 text-pink-700',
      telegram: 'bg-cyan-100 text-cyan-700',
      unknown: 'bg-gray-100 text-gray-700'
    };
    return colors[source] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-slate-800 mb-2">机器人消息</h1>
          <p className="text-slate-600">查看和管理通过机器人接口接收到的消息</p>
        </motion.div>

        {/* 测试消息发送区域 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-lg p-6 mb-8"
        >
          <h2 className="text-xl font-semibold text-slate-800 mb-4">发送测试消息</h2>
          <div className="flex gap-4">
            <input
              type="text"
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              placeholder="输入包含链接的消息内容，例如：年后明牌主线 算力！ http://xhslink.com/o/375N4Taih1F"
              className="flex-1 px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && sendTestMessage()}
            />
            <button
              onClick={sendTestMessage}
              disabled={sending || !testMessage.trim()}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors disabled:bg-slate-300 disabled:cursor-not-allowed font-medium"
            >
              {sending ? '发送中...' : '发送测试消息'}
            </button>
          </div>
        </motion.div>

        {/* 消息列表 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex justify-between items-center mb-6">
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('messages')}
                className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors ${
                  viewMode === 'messages'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                消息列表
              </button>
              <button
                onClick={() => setViewMode('trash')}
                className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors ${
                  viewMode === 'trash'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                回收站 {trashMessages.length > 0 && `(${trashMessages.length})`}
              </button>
            </div>
            {viewMode === 'messages' && (
              <div className="flex gap-2">
                {!isBatchMode ? (
                  <>
                    <button
                      onClick={fetchMessages}
                      className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium flex items-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      刷新
                    </button>
                    <button
                      onClick={() => setIsBatchMode(true)}
                      className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors font-medium flex items-center gap-2"
                    >
                      <CheckSquare className="w-4 h-4" />
                      批量管理
                    </button>
                    <button
                      onClick={clearAll}
                      disabled={messages.length === 0}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium flex items-center gap-2 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
                    >
                      <Trash2 className="w-4 h-4" />
                      清空全部
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setIsBatchMode(false);
                        setSelectedIds(new Set());
                      }}
                      className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
                    >
                      取消
                    </button>
                    <button
                      onClick={toggleSelectAll}
                      className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors font-medium flex items-center gap-2"
                    >
                      {selectedIds.size === messages.length ? (
                        <>
                          <CheckSquare className="w-4 h-4" />
                          取消全选
                        </>
                      ) : (
                        <>
                          <Square className="w-4 h-4" />
                          全选
                        </>
                      )}
                    </button>
                    <button
                      onClick={batchDelete}
                      disabled={selectedIds.size === 0}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium flex items-center gap-2 disabled:bg-slate-300 disabled:cursor-not-allowed"
                    >
                      <Trash2 className="w-4 h-4" />
                      删除选中 ({selectedIds.size})
                    </button>
                  </>
                )}
              </div>
            )}
            {viewMode === 'trash' && (
              <div className="flex gap-2">
                {!isTrashBatchMode ? (
                  <>
                    <button
                      onClick={fetchTrashMessages}
                      className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium flex items-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      刷新
                    </button>
                    <button
                      onClick={() => setIsTrashBatchMode(true)}
                      className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors font-medium flex items-center gap-2"
                    >
                      <CheckSquare className="w-4 h-4" />
                      批量管理
                    </button>
                    <button
                      onClick={clearAllTrash}
                      disabled={trashMessages.length === 0}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium flex items-center gap-2 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
                    >
                      <Trash2 className="w-4 h-4" />
                      清空回收站
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setIsTrashBatchMode(false);
                        setSelectedTrashIds(new Set());
                      }}
                      className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
                    >
                      取消
                    </button>
                    <button
                      onClick={toggleSelectAllTrash}
                      className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors font-medium flex items-center gap-2"
                    >
                      {selectedTrashIds.size === trashMessages.length ? (
                        <>
                          <CheckSquare className="w-4 h-4" />
                          取消全选
                        </>
                      ) : (
                        <>
                          <Square className="w-4 h-4" />
                          全选
                        </>
                      )}
                    </button>
                    <button
                      onClick={batchRestoreTrash}
                      disabled={selectedTrashIds.size === 0}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2 disabled:bg-slate-300 disabled:cursor-not-allowed"
                    >
                      <RotateCcw className="w-4 h-4" />
                      恢复选中 ({selectedTrashIds.size})
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-500">加载中...</div>
          ) : error ? (
            <div className="text-center py-12 text-red-500">{error}</div>
          ) : viewMode === 'messages' && messages.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              暂无消息，发送一条测试消息试试吧！
            </div>
          ) : viewMode === 'trash' && trashMessages.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              回收站为空
            </div>
          ) : (
            <div className="space-y-4">
              {viewMode === 'messages' ? (
                // 消息列表视图
                messages.map((msg, index) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 relative ${selectedIds.has(msg.id) ? 'ring-2 ring-indigo-500' : ''}`}
                  >
                    {/* 批量选择模式下的选择框 */}
                    {isBatchMode && (
                      <button
                        onClick={() => toggleSelect(msg.id)}
                        className="absolute top-4 left-4 z-10"
                      >
                        {selectedIds.has(msg.id) ? (
                          <CheckSquare className="w-6 h-6 text-indigo-600" />
                        ) : (
                          <Square className="w-6 h-6 text-slate-400 hover:text-indigo-600" />
                        )}
                      </button>
                    )}

                    {/* 消息头部 */}
                    <div className="flex justify-between items-start mb-4">
                      <div className={`flex items-center gap-3 ${isBatchMode ? 'ml-10' : ''}`}>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSourceColor(msg.source)}`}>
                          {getSourceName(msg.source)}
                        </span>
                        <span className="text-sm text-slate-500">
                          {formatTime(msg.received_at)}
                        </span>
                        {msg.processed && (
                          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                            已处理
                          </span>
                        )}
                      </div>
                      {!isBatchMode && (
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-slate-500">ID: {msg.id}</span>
                          <button
                                                    onClick={() => deleteMessage(msg.id)}
                                                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                                    title="删除"
                                                  >
                                                    <Trash2 className="w-5 h-5" />
                                                  </button>                        </div>
                      )}
                    </div>

                    {/* 消息内容 */}
                    <div className="mb-4">
                      <p className="text-slate-700 whitespace-pre-wrap break-words">
                        {msg.message}
                      </p>
                    </div>

                    {/* 解析出的链接 */}
                    {msg.total_links > 0 && (
                      <div className="border-t border-slate-200 pt-4">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-sm font-medium text-slate-600">
                            解析出 {msg.total_links} 个链接：
                          </span>
                        </div>
                        <div className="space-y-2">
                          {msg.parsed_urls.map((link, linkIndex) => (
                            <div
                              key={linkIndex}
                              className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                            >
                              <span className={`px-2 py-1 ${getPlatformColor(link.platform)} text-white rounded text-xs font-medium`}>
                                {getPlatformName(link.platform)}
                              </span>
                              <a
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-1 text-sm text-indigo-600 hover:text-indigo-800 truncate"
                              >
                                {link.url}
                              </a>
                              {link.short_link && (
                                <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-xs font-medium">
                                  短链接
                                </span>
                              )}
                              {link.content_id && (
                                <span className="text-xs text-slate-500">
                                  ID: {link.content_id}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))
              ) : (
                // 回收站视图
                trashMessages.map((msg, index) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 relative border-l-4 border-red-500 ${selectedTrashIds.has(msg.id) ? 'ring-2 ring-indigo-500' : ''}`}
                  >
                    {/* 批量选择模式下的选择框 */}
                    {isTrashBatchMode && (
                      <button
                        onClick={() => toggleSelectTrash(msg.id)}
                        className="absolute top-4 left-4 z-10"
                      >
                        {selectedTrashIds.has(msg.id) ? (
                          <CheckSquare className="w-6 h-6 text-indigo-600" />
                        ) : (
                          <Square className="w-6 h-6 text-slate-400 hover:text-indigo-600" />
                        )}
                      </button>
                    )}

                    {/* 回收站标记 */}
                    <div className={`flex justify-between items-start mb-4 ${isTrashBatchMode ? 'ml-10' : ''}`}>
                      <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                          已删除
                        </span>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSourceColor(msg.source)}`}>
                          {getSourceName(msg.source)}
                        </span>
                        <span className="text-sm text-slate-500">
                          原始接收: {formatTime(msg.received_at)}
                        </span>
                        <span className="text-sm text-slate-500">
                          删除于: {formatTime(msg.deleted_at)}
                        </span>
                        {msg.expires_in_days > 0 ? (
                          <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-medium">
                            {msg.expires_in_days}天后过期
                          </span>
                        ) : (
                          <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                            已过期
                          </span>
                        )}
                      </div>
                      {!isTrashBatchMode && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => restoreMessage(msg.id)}
                            disabled={msg.expires_in_days <= 0}
                            className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="恢复"
                          >
                            <RotateCcw className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => permanentDelete(msg.id)}
                            className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="永久删除"
                          >
                            <Trash className="w-5 h-5" />
                          </button>
                        </div>
                      )}
                    </div>

                    {/* 消息内容 */}
                    <div className="mb-4">
                      <p className="text-slate-700 whitespace-pre-wrap break-words">
                        {msg.message}
                      </p>
                    </div>

                    {/* 解析出的链接 */}
                    {msg.total_links > 0 && (
                      <div className="border-t border-slate-200 pt-4">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-sm font-medium text-slate-600">
                            解析出 {msg.total_links} 个链接：
                          </span>
                        </div>
                        <div className="space-y-2">
                          {msg.parsed_urls.map((link, linkIndex) => (
                            <div
                              key={linkIndex}
                              className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                            >
                              <span className={`px-2 py-1 ${getPlatformColor(link.platform)} text-white rounded text-xs font-medium`}>
                                {getPlatformName(link.platform)}
                              </span>
                              <a
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-1 text-sm text-indigo-600 hover:text-indigo-800 truncate"
                              >
                                {link.url}
                              </a>
                              {link.short_link && (
                                <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-xs font-medium">
                                  短链接
                                </span>
                              )}
                              {link.content_id && (
                                <span className="text-xs text-slate-500">
                                  ID: {link.content_id}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))
              )}
            </div>
          )}
        </motion.div>

        {/* 确认弹窗 */}
        {confirmDialog.show && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4"
            >
              <h3 className="text-xl font-semibold text-slate-800 mb-2">{confirmDialog.title}</h3>
              <p className="text-slate-600 mb-6">{confirmDialog.message}</p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} })}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
                >
                  取消
                </button>
                <button
                  onClick={confirmDialog.onConfirm}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                >
                  确认
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Toast 提示 */}
        {toast.show && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`fixed bottom-6 right-6 px-6 py-3 rounded-lg shadow-lg z-50 ${
              toast.type === 'success' ? 'bg-green-500' : 'bg-red-500'
            } text-white font-medium`}
          >
            {toast.message}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default BotPage;