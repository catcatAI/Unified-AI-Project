from abc import ABC, abstractmethod
import numpy as np

class BasePixelObject(ABC):
    """所有像素世界物件的基類"""
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.matrix = np.zeros((h, w), dtype=np.uint8)

    @abstractmethod
    def interact(self, angela):
        """交互邏輯"""
        pass

    @abstractmethod
    def get_metabolic_impact(self) -> float:
        """對 Angela 代謝的影響數值"""
        pass
