from abc import ABC, abstractmethod
from typing import Any


class BaseConverter(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def convert(self, source: Any) -> str:
        pass
