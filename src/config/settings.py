from decouple import config

deposit_data_path: str = config('DEPOSIT_DATA_PATH')

# logging
LOG_PLAIN = 'plain'
LOG_JSON = 'json'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

log_level: str = config('LOG_LEVEL', default='INFO')
log_format: str = config('LOG_FORMAT', default=LOG_PLAIN)

sentry_dsn: str = config('SENTRY_DSN', default='')
sentry_environment = config('SENTRY_ENVIRONMENT', default='')
