"""Source adapter registry."""

from macro_publisher.sources.cbsl_fx import CBSLFXAdapter
from macro_publisher.sources.dcs_ccpi import DCSCCPIAdapter
from macro_publisher.sources.doa_vegetable_prices import DOAVegetablePricesAdapter

SOURCE_REGISTRY = {
    "cbsl_fx": CBSLFXAdapter,
    "dcs_ccpi": DCSCCPIAdapter,
    "doa_vegetable_prices": DOAVegetablePricesAdapter,
}

__all__ = [
    "CBSLFXAdapter",
    "DCSCCPIAdapter",
    "DOAVegetablePricesAdapter",
    "SOURCE_REGISTRY",
]
