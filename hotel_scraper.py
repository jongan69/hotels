from fast_hotels import HotelData, Guests, get_hotels

# Example search parameters
hotel_data = [
    HotelData(
        checkin_date="2025-06-23",
        checkout_date="2025-06-25",
        location="Tokyo"
    )
]
guests = Guests(adults=2, children=1)

# Fetch hotel results using the package (live scraping)
result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live")

# Print hotel results
for hotel in result.hotels:
    print(f"Name: {hotel.name}, Price: {hotel.price}, Rating: {hotel.rating}") 