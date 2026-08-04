from abc import ABC, abstractmethod


class BaseConnection(ABC):

    @property
    @abstractmethod
    def url(self) -> str:
        ...
