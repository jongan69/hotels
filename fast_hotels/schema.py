from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional


@dataclass
class Result:
    hotels: List[Hotel]
    lowest_price: Optional[float] = None
    current_price: Optional[float] = None


@dataclass
class Hotel:
    name: str
    price: float
    rating: Optional[float] = None
    url: Optional[str] = None
    amenities: List[str] = None
    
    def __post_init__(self):
        if self.amenities is None:
            self.amenities = [] 