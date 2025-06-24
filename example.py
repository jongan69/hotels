from fast_hotels import HotelData, Guests, get_hotels
import logging

# Configure logging for demonstration
logging.basicConfig(level=logging.INFO)

# Example search parameters
hotel_data = [
    HotelData(
        checkin_date="2025-06-23",
        checkout_date="2025-06-25",
        location="Tokyo"
    )
]
guests = Guests(adults=2, children=1)

# 1. Fetch hotel results using live scraping (with debug enabled, limit=3)
try:
    # In debug mode, we can see the raw HTML of the page
    result_live = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live", debug=False)
    print("\n--- Live Scraping Results ---")
    for hotel in result_live.hotels:
        print(f"Name: {hotel.name}, Price: {hotel.price}, Rating: {hotel.rating}, "
              f"URL: {hotel.url}, Amenities: {hotel.amenities}")
    print(f"Lowest price: {result_live.lowest_price}, Current price: {result_live.current_price}")
except Exception as e:
    print(f"Error during live scraping: {e}")

# 2. Fetch hotel results using mock data (limit=1)
result_mock = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="local", limit=1)
print("\n--- Mock Data Results (limit=1) ---")
for hotel in result_mock.hotels:
    print(f"Name: {hotel.name}, Price: {hotel.price}, Rating: {hotel.rating}, "
          f"URL: {hotel.url}, Amenities: {hotel.amenities}")
print(f"Lowest price: {result_mock.lowest_price}, Current price: {result_mock.current_price}")

# 3. Demonstrate error handling with invalid input
invalid_result = get_hotels(hotel_data=[], guests="not_a_guests_object", fetch_mode="local")
print("\n--- Invalid Input Results ---")
print(f"Hotels: {invalid_result.hotels}, Lowest price: {invalid_result.lowest_price}") 