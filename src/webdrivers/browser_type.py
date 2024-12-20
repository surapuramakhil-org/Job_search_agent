from enum import Enum

from webdrivers.chrome import Chrome
from webdrivers.firefox import Firefox


class BrowserType(Enum):
    """Enum for supported browser types"""
    CHROME = Chrome
    FIREFOX = Firefox
