import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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

const BotPage: React.FC = () => {
  const [messages, setMessages] = useState<BotMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testMessage, setTestMessage] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    fetchMessages();
  }, []);

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
        alert('测试消息发送成功！');
      } else {
        alert(response.data.message);
      }
    } catch (err) {
      alert('发送失败');
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
            <h2 className="text-2xl font-semibold text-slate-800">接收到的消息</h2>
            <button
              onClick={fetchMessages}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
            >
              刷新
            </button>
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-500">加载中...</div>
          ) : error ? (
            <div className="text-center py-12 text-red-500">{error}</div>
          ) : messages.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              暂无消息，发送一条测试消息试试吧！
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6"
                >
                  {/* 消息头部 */}
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                        {msg.source}
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
                    <span className="text-sm text-slate-500">
                      ID: {msg.id}
                    </span>
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
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default BotPage;