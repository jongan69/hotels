from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class HotelData:
    checkin_date: str
    checkout_date: str
    location: str

@dataclass
class Guests:
    adults: int = 1
    children: int = 0
    infants: int = 0

@dataclass
class Hotel:
    name: str
    price: float
    rating: Optional[float] = None
    address: Optional[str] = None
    url: Optional[str] = None
    amenities: List[str] = field(default_factory=list)

@dataclass
class Result:
    hotels: List[Hotel] = field(default_factory=list)
    lowest_price: Optional[float] = None
    current_price: Optional[float] = None 