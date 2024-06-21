from decouple import config

from src.config.networks import NETWORKS

relayer_host: str = config('RELAYER_HOST', default='127.0.0.1')
relayer_port: int = config('RELAYER_PORT', cast=int, default=8000)

deposit_data_path: str = config('DEPOSIT_DATA_PATH')
signature_threshold: int = config('SIGNATURE_THRESHOLD', cast=int)

validators_manager_key_file: str = config('VALIDATORS_MANAGER_KEY_FILE')
validators_manager_password_file: str = config('VALIDATORS_MANAGER_PASSWORD_FILE')

network: str = config('NETWORK')
network_config = NETWORKS[network]

execution_endpoint: str = config('EXECUTION_ENDPOINT')
execution_timeout: int = config('EXECUTION_TIMEOUT', cast=int, default=60)
execution_retry_timeout: int = config('EXECUTION_RETRY_TIMEOUT', cast=int, default=60)

# logging
LOG_PLAIN = 'plain'
LOG_JSON = 'json'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

log_level: str = config('LOG_LEVEL', default='INFO')
log_format: str = config('LOG_FORMAT', default=LOG_PLAIN)

sentry_dsn: str = config('SENTRY_DSN', default='')
sentry_environment = config('SENTRY_ENVIRONMENT', default='')
