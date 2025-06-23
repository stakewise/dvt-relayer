from dataclasses import asdict, dataclass

from sw_utils.networks import CHIADO, GNOSIS, HOODI, MAINNET
from sw_utils.networks import NETWORKS as BASE_NETWORKS
from sw_utils.networks import BaseNetworkConfig


@dataclass
class NetworkConfig(BaseNetworkConfig):
    DEFAULT_DVT_RELAYER_ENDPOINT: str


NETWORKS: dict[str, NetworkConfig] = {
    MAINNET: NetworkConfig(
        **asdict(BASE_NETWORKS[MAINNET]),
    ),
    HOODI: NetworkConfig(
        **asdict(BASE_NETWORKS[HOODI]),
    ),
    GNOSIS: NetworkConfig(
        **asdict(BASE_NETWORKS[GNOSIS]),
    ),
    CHIADO: NetworkConfig(
        **asdict(BASE_NETWORKS[CHIADO]),
    ),
}
