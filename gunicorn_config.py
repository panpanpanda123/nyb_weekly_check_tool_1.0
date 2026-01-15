"""
Gunicorn配置文件
Gunicorn Configuration for Production
"""
import multiprocessing
import os

# 服务器绑定
bind = f"0.0.0.0:{os.getenv('PORT', 5001)}"

# Worker进程数（推荐：CPU核心数 * 2 + 1）
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Worker类型（sync, gevent, eventlet）
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')

# 每个worker的线程数
threads = int(os.getenv('GUNICORN_THREADS', 2))

# Worker超时时间（秒）
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))

# 保持连接时间（秒）
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 5))

# 最大请求数（防止内存泄漏）
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 50))

# 日志配置
accesslog = os.getenv('GUNICORN_ACCESS_LOG', 'logs/access.log')
errorlog = os.getenv('GUNICORN_ERROR_LOG', 'logs/error.log')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# 访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = 'inspection_system'

# Daemon模式（生产环境建议使用systemd管理，不使用daemon）
daemon = False

# PID文件
pidfile = os.getenv('GUNICORN_PID_FILE', 'logs/gunicorn.pid')

# 用户和组（如果以root启动，会切换到这个用户）
# user = 'www-data'
# group = 'www-data'

# 临时目录
worker_tmp_dir = '/dev/shm'

# 优雅重启超时
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))

# 预加载应用（提高性能，但重启时需要重新加载）
preload_app = True

# 回调函数
def on_starting(server):
    """服务器启动时调用"""
    print("=" * 60)
    print("门店检查项图片审核系统启动中...")
    print(f"Workers: {workers}")
    print(f"Bind: {bind}")
    print("=" * 60)

def on_reload(server):
    """重新加载时调用"""
    print("服务器重新加载...")

def when_ready(server):
    """服务器准备就绪时调用"""
    print("✓ 服务器已准备就绪，可以接受请求")

def on_exit(server):
    """服务器退出时调用"""
    print("服务器正在关闭...")
