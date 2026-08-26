from importlib.metadata import PackageNotFoundError, version

from skeletal.config import Settings, get_settings
from skeletal.logging_setup import configure_logging

try:
    __version__ = version("python-skeletal")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["Settings", "__version__", "configure_logging", "get_settings"]
