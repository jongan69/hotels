from typing import Literal, List, Optional
from .hotels_impl import HotelData, Guests, THSData

def create_filter(
    *,
    hotel_data: List[HotelData],
    guests: Guests,
    room_type: Optional[str] = None,
    amenities: Optional[List[str]] = None,
) -> THSData:
    """Create a filter for Google Hotels API. (``?ths=``)

    Args:
        hotel_data (list[HotelData]): Hotel data as a list.
        guests (Guests): Guests.
        room_type (str, optional): Room type. If not provided, taken from first HotelData.
        amenities (list[str], optional): Preferred amenities. If not provided, taken from first HotelData.
    """
    # Extract from first HotelData if not provided
    if not room_type and hotel_data and hasattr(hotel_data[0], "room_type"):
        room_type = hotel_data[0].room_type
    if amenities is None and hotel_data and hasattr(hotel_data[0], "amenities"):
        amenities = hotel_data[0].amenities
    return THSData.from_interface(
        hotel_data=hotel_data, 
        guests=guests, 
        room_type=room_type,
        amenities=amenities
    ) 