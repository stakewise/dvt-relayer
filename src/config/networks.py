from dataclasses import asdict, dataclass

from sw_utils.networks import GNOSIS, HOODI, MAINNET
from sw_utils.networks import NETWORKS as BASE_NETWORKS
from sw_utils.networks import BaseNetworkConfig


@dataclass
class NetworkConfig(BaseNetworkConfig):
    pass


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
}
