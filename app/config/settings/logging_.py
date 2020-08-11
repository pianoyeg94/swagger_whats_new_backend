import os
import pathlib

LOGGING_DIR = os.path.join(pathlib.Path(__file__).parents[2], 'logs')

pathlib.Path(LOGGING_DIR).mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'development_logfile': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGGING_DIR, 'dev.log'),
            'maxBytes': 1024 * 1024 * 300,
            'backupCount': 5,
            'formatter': 'verbose'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
    'loggers': {
        'apps': {
            'handlers': ['development_logfile'],
        },
        'django': {
            'handlers': ['development_logfile'],
        }
    }
}
