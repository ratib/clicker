# clicker/core/interfaces.py
from abc import ABC, abstractmethod


class ClickBackend(ABC):
    @abstractmethod
    def click(self, x: int, y: int):
        pass
