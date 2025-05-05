from prometheus_client import Counter, Histogram, Gauge, start_http_server
import psutil
import threading
import time
from logger import get_logger
from redis_client import redis_client

logger = get_logger(__name__)

# Metrics definitions
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

repository_size_bytes = Gauge(
    'repository_size_bytes',
    'Size of repositories in bytes',
    ['repo_id']
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

cache_hits = Counter(
    'cache_hits_total',
    'Total number of cache hits'
)

cache_misses = Counter(
    'cache_misses_total',
    'Total number of cache misses'
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

class SystemMonitor:
    def __init__(self, interval=60):
        self.interval = interval
        self.running = False
        self.monitor_thread = None

    def start(self):
        """Start the monitoring thread"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("System monitoring started")

    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
            logger.info("System monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Update system metrics
                self._update_system_metrics()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    def _update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.used)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)

            # Redis stats
            if redis_client and redis_client.ping():
                info = redis_client.info()
                active_connections.set(info.get('connected_clients', 0))

        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

def start_metrics_server(port=8000):
    """Start the Prometheus metrics server"""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        raise

def update_repository_size(repo_id, size):
    """Update repository size metric"""
    try:
        repository_size_bytes.labels(repo_id=str(repo_id)).set(size)
    except Exception as e:
        logger.error(f"Failed to update repository size metric: {e}")

def increment_cache_hit():
    """Increment cache hits counter"""
    cache_hits.inc()

def increment_cache_miss():
    """Increment cache misses counter"""
    cache_misses.inc()

def set_active_connections(count):
    """Set number of active connections"""
    active_connections.set(count)

# Initialize system monitor
system_monitor = SystemMonitor()

def initialize_monitoring():
    """Initialize all monitoring components"""
    try:
        # Start metrics server
        start_metrics_server()
        
        # Start system monitor
        system_monitor.start()
        
        logger.info("Monitoring system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize monitoring: {e}")
        raise