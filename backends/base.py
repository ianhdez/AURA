from abc import ABC, abstractmethod


class ModelBackend(ABC):

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def unload(self):
        pass

    @abstractmethod
    def generate(self, messages, **kwargs):
        pass

    @abstractmethod
    def is_loaded(self):
        pass

    @abstractmethod
    def get_status(self):
        pass