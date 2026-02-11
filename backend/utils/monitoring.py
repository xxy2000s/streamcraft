from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from loguru import logger

# 定义监控指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')

class MonitoringMiddleware:
    """监控中间件"""
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        
        # 增加活跃连接数
        ACTIVE_CONNECTIONS.inc()
        
        # 包装send方法来捕获响应状态
        original_send = send
        status_code = [200]  # 使用列表来在内部函数中修改
        
        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await original_send(message)
        
        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            # 减少活跃连接数
            ACTIVE_CONNECTIONS.dec()
            
            # 记录请求指标
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code[0]).inc()
            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} executed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    
    return wrapper

# 数据库监控
DB_QUERY_COUNT = Counter('database_queries_total', 'Total database queries', ['operation'])
DB_QUERY_DURATION = Histogram('database_query_duration_seconds', 'Database query duration', ['operation'])

def monitor_db_operation(operation):
    """数据库操作监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            DB_QUERY_COUNT.labels(operation=operation).inc()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Database operation {operation} failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator