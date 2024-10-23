import sqlite3
from sqlite3 import Connection

from sw_utils import IpfsFetchClient, get_consensus_client, get_execution_client

from src.config import settings

execution_client = get_execution_client(
    [settings.execution_endpoint],
    timeout=settings.execution_timeout,
    retry_timeout=settings.execution_retry_timeout,
)
consensus_client = get_consensus_client(
    [settings.consensus_endpoint],
    timeout=settings.consensus_timeout,
    retry_timeout=settings.consensus_retry_timeout,
)


class Database:
    def get_db_connection(self) -> Connection:
        return sqlite3.connect(settings.database)


db_client = Database()

ipfs_fetch_client = IpfsFetchClient(
    ipfs_endpoints=settings.ipfs_fetch_endpoints,
    timeout=settings.ipfs_timeout,
    retry_timeout=settings.ipfs_retry_timeout,
)
