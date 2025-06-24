from fast_hotels import HotelData, Guests, get_hotels

def test_get_hotels_returns_results():
    hotel_data = [HotelData(checkin_date="2025-06-23", checkout_date="2025-06-25", location="Tokyo")]
    guests = Guests(adults=2, children=1)
    result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="mock")
    assert len(result.hotels) > 0 