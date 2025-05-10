import logging
import logging.config
import yaml
import os
from pythonjsonlogger import jsonlogger
from datetime import datetime
from flask import request, has_request_context

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()
            
        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
            
        # Add request context if available
        if has_request_context():
            log_record['method'] = request.method
            log_record['path'] = request.path
            log_record['ip'] = request.remote_addr
            log_record['user_agent'] = request.user_agent.string

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.method = request.method
            record.ip = request.remote_addr
        else:
            record.url = None
            record.method = None
            record.ip = None
        return super().format(record)

def setup_logging(config_path=None):
    """Setup logging configuration"""
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), 'logging_config.yml')
        
    if os.path.exists(config_path):
        with open(config_path, 'rt') as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
            except Exception as e:
                print(f"Error loading logging configuration: {e}")
                setup_default_logging()
    else:
        setup_default_logging()

def init_logging(config_path=None):
    setup_logging(config_path)

def setup_default_logging():
    """Setup basic default logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('server.log')
        ]
    )

def get_logger(name):
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

# Metrics for monitoring
class LogMetrics:
    def __init__(self):
        self.error_count = 0
        self.warning_count = 0
        self.request_count = 0
        
    def increment_error(self):
        self.error_count += 1
        
    def increment_warning(self):
        self.warning_count += 1
        
    def increment_request(self):
        self.request_count += 1
        
    def get_metrics(self):
        return {
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'request_count': self.request_count
        }

# Create metrics instance
metrics = LogMetrics()
