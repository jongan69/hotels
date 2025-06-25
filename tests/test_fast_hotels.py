from fast_hotels.hotels_impl import HotelData, Guests
from fast_hotels import get_hotels

def test_get_hotels_returns_results():
    hotel_data = [HotelData(
        checkin_date="2025-06-23", 
        checkout_date="2025-06-25", 
        location="Tokyo",
        room_type="standard",
        amenities=["wifi", "breakfast"]
    )]
    guests = Guests(adults=2, children=1, infants=0)
    
    result = get_hotels(
        hotel_data=hotel_data,
        guests=guests,
        room_type="standard",
        amenities=["wifi", "breakfast"],
        fetch_mode="common",
        limit=5,
        sort_by="price"
    )
    
    assert len(result.hotels) > 0
    assert result.lowest_price is not None
    assert result.current_price is not None
    
    # Test that hotels have the expected structure
    for hotel in result.hotels:
        assert hotel.name is not None
        assert hotel.price is not None
        assert isinstance(hotel.amenities, list) 