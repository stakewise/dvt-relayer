from decouple import Csv, config

from src.config.networks import NETWORKS

relayer_host: str = config('RELAYER_HOST', default='127.0.0.1')
relayer_port: int = config('RELAYER_PORT', cast=int, default=8000)

deposit_data_path: str = config('DEPOSIT_DATA_PATH')
signature_threshold: int = config('SIGNATURE_THRESHOLD', cast=int)

network: str = config('NETWORK')
network_config = NETWORKS[network]

execution_endpoint: str = config('EXECUTION_ENDPOINT')
execution_timeout: int = config('EXECUTION_TIMEOUT', cast=int, default=60)
execution_retry_timeout: int = config('EXECUTION_RETRY_TIMEOUT', cast=int, default=60)

consensus_endpoint: str = config('CONSENSUS_ENDPOINT')
consensus_timeout: int = config('CONSENSUS_TIMEOUT', cast=int, default=60)
consensus_retry_timeout: int = config('CONSENSUS_RETRY_TIMEOUT', cast=int, default=60)

ipfs_fetch_endpoints: list[str] = config(
    'IPFS_FETCH_ENDPOINTS',
    cast=Csv(),
    default=','.join(
        [
            'https://stakewise-v3.infura-ipfs.io',
            'http://cloudflare-ipfs.com',
            'https://gateway.pinata.cloud',
            'https://ipfs.io',
        ]
    ),
)
ipfs_timeout: int = config('IPFS_TIMEOUT', default=60, cast=int)
ipfs_retry_timeout: int = config('IPFS_RETRY_TIMEOUT', default=120, cast=int)
genesis_validators_ipfs_timeout: int = config(
    'GENESIS_VALIDATORS_IPFS_TIMEOUT', default=300, cast=int
)
genesis_validators_ipfs_retry_timeout: int = config(
    'GENESIS_VALIDATORS_IPFS_RETRY_TIMEOUT', default=600, cast=int
)

database: str = config('DATABASE')

# logging
LOG_PLAIN = 'plain'
LOG_JSON = 'json'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

log_level: str = config('LOG_LEVEL', default='INFO')
log_format: str = config('LOG_FORMAT', default=LOG_PLAIN)

sentry_dsn: str = config('SENTRY_DSN', default='')
sentry_environment = config('SENTRY_ENVIRONMENT', default='')

VALIDATOR_LIFETIME: int = config('VALIDATOR_LIFETIME', default=3600, cast=int)
