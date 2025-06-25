"""Typed implementation for hotels API requests"""

import base64
from typing import Any, List, Optional, TYPE_CHECKING, Literal, Union
from dataclasses import dataclass

# Import the generated protobuf
try:
    from . import hotels_pb2 as PB
    PB_AVAILABLE = True
except ImportError:
    # Fallback for development
    PB = None
    PB_AVAILABLE = False

if TYPE_CHECKING:
    # Type hints for protobuf
    class PB:
        class Info:
            pass
        class HotelData:
            pass
        class Guests:
            pass
        class RoomType:
            pass
       

class HotelData:
    """Represents hotel search data.

    Args:
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        location (str): Location (city name or IATA airport code).
        room_type (str, optional): Room type preference. Default is None.
        amenities (List[str], optional): Preferred amenities. Default is None.
    """

    __slots__ = ("checkin_date", "checkout_date", "location", "room_type", "amenities")
    checkin_date: str
    checkout_date: str
    location: str
    room_type: Optional[str]
    amenities: Optional[List[str]]

    def __init__(
        self,
        *,
        checkin_date: str,
        checkout_date: str,
        location: str,
        room_type: Optional[str] = None,
        amenities: Optional[List[str]] = None,
    ):
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date
        self.location = location
        self.room_type = room_type
        self.amenities = amenities

    def attach(self, info: Any) -> None:  # type: ignore
        """Attach this hotel data to a protobuf Info object"""
        if not PB_AVAILABLE:
            return  # Skip if protobuf not available
        
        data = info.data.add()
        data.checkin_date = self.checkin_date
        data.checkout_date = self.checkout_date
        
        # Set location
        data.location.city = self.location
        data.location.country = ""  # Could be enhanced with country detection
        
        if self.room_type:
            data.room_type = self.room_type
            
        if self.amenities:
            data.amenities.extend(self.amenities)

    def __repr__(self) -> str:
        return (
            f"HotelData(checkin_date={self.checkin_date!r}, "
            f"checkout_date={self.checkout_date!r}, "
            f"location={self.location!r}, "
            f"room_type={self.room_type!r}, "
            f"amenities={self.amenities!r})"
        )


class Guests:
    """Represents guest information for hotel booking."""
    
    def __init__(
        self,
        *,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
    ):
        assert adults >= 1, "At least one adult is required"
        assert adults + children + infants <= 9, "Too many guests (> 9)"
        assert infants <= adults, "You must have at least one adult per infant"

        self.adults = adults
        self.children = children
        self.infants = infants

    def attach(self, info: Any) -> None:  # type: ignore
        """Attach guest information to a protobuf Info object"""
        if not PB_AVAILABLE:
            return  # Skip if protobuf not available
        
        # Add adults
        for _ in range(self.adults):
            info.guests.guests.append(PB.GuestType.ADULT)
        
        # Add children
        for _ in range(self.children):
            info.guests.guests.append(PB.GuestType.CHILD)
        
        # Add infants
        for _ in range(self.infants):
            info.guests.guests.append(PB.GuestType.INFANT)

    def __repr__(self) -> str:
        return f"Guests(adults={self.adults}, children={self.children}, infants={self.infants})"


class THSData:
    """``?ths=`` data for Google Hotels API. (internal)

    Use `THSData.from_interface` instead.
    """

    def __init__(
        self,
        *,
        hotel_data: List[HotelData],
        room_type: Any,  # type: ignore
        guests: Guests,
        amenities: Optional[List[str]] = None,
    ):
        self.hotel_data = hotel_data
        self.room_type = room_type
        self.guests = guests
        self.amenities = amenities

    def pb(self) -> Any:  # type: ignore
        """Create a protobuf Info object"""
        if not PB_AVAILABLE:
            # Return stub data if protobuf not available
            class StubInfo:
                def SerializeToString(self):
                    return b"stub_data"
            return StubInfo()
        
        info = PB.Info()
        info.room_type = self.room_type

        # Attach guests
        self.guests.attach(info)

        # Attach hotel data
        for hotel in self.hotel_data:
            hotel.attach(info)

        # Attach global amenities
        if self.amenities:
            info.amenities.extend(self.amenities)

        return info

    def to_string(self) -> bytes:
        return self.pb().SerializeToString()

    def as_b64(self) -> bytes:
        return base64.b64encode(self.to_string())

    @staticmethod
    def from_interface(
        *,
        hotel_data: List[HotelData],
        guests: Guests,
        room_type: str,
        amenities: Optional[List[str]] = None,
    ):
        """Use ``?ths=`` from an interface.

        Args:
            hotel_data (list[HotelData]): Hotel data as a list.
            guests (Guests): Guests.
            room_type (str): Room type.
            amenities (list[str], optional): Preferred amenities.
        """
        if not PB_AVAILABLE:
            room_t = 1  # STANDARD
        else:
            room_t = {
                "standard": PB.RoomType.STANDARD,
                "deluxe": PB.RoomType.DELUXE,
                "suite": PB.RoomType.SUITE,
            }[room_type]

        return THSData(
            hotel_data=hotel_data,
            room_type=room_t,
            guests=guests,
            amenities=amenities
        )

    def __repr__(self) -> str:
        return f"THSData(hotel_data={self.hotel_data!r}, amenities={self.amenities!r})" 