import logging
import logging.config

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Default App Name"
    api_url: str = ""
    api_key: str = ""
    model_id: str = ""

    # 配置 .env 文件路径 (Pydantic v1)
    class Config:
        env_file = ".env"

# 创建配置实例，它会自动从 .env 文件和环境变量加载值
settings = Settings()

# 定义日志配置字典
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False, # 不禁用已存在的 logger
    'formatters': { # 定义日志格式
        'standard': {
            'format': '%(asctime)s %(module)s:%(lineno)d [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s %(module)s:%(lineno)d [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': { # 定义日志处理器
        'console': { # 控制台处理器
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout', # 默认是 stderr
        },
        'file': { # 文件处理器
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'mode': 'a', # 追加模式
            'encoding': 'utf-8', # 指定编码
        },
    },
    'loggers': { # 定义 Logger
        '': {  # root logger (空字符串是根 logger)
            'handlers': ['console', 'file'], # 使用这两个处理器
            'level': 'DEBUG', # 记录 DEBUG 级别及以上的日志
            'propagate': False # 不向父 logger 传播 (对于 root logger，通常设为 False)
        }
        # 你可以为特定模块定义不同的 logger
        # 'my_module.special': {
        #     'handlers': ['file'],
        #     'level': 'WARNING',
        #     'propagate': False
        # }
    }
}


# 获取日志logger
def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger()