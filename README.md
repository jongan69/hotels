# fast-hotels

A fast, simple hotel scraper for Google Hotels, inspired by fast-flights. Fetches hotel data (name, price, rating, amenities, etc.) using a fast HTTP-based approach with protobuf encoding.

## Features
- Scrape Google Hotels for hotel data using fast HTTP requests
- Simple, synchronous API with protobuf-based filtering
- Returns structured hotel data (name, price, rating, amenities, URL)
- **Sort results by price, rating, or best value (rating/price ratio)**
- **Limit the number of results returned**
- **Support for IATA airport codes as locations (e.g., 'HND' → 'Tokyo')**
- **Multiple fetch modes: common, fallback, force-fallback, local**
- **Automatic location conversion from airport codes to city names**

## Installation

```sh
pip install fast-hotels
```

## Usage

```python
from fast_hotels.hotels_impl import HotelData, Guests
from fast_hotels import get_hotels

hotel_data = [
    HotelData(
        checkin_date="2025-06-23",
        checkout_date="2025-06-25",
        location="Tokyo",  # or use an IATA code like "HND"
        room_type="standard",
        amenities=["wifi", "breakfast"]
    )
]
guests = Guests(adults=2, children=1, infants=0)

# Basic usage
result = get_hotels(
    hotel_data=hotel_data,
    guests=guests,
    room_type="standard",
    amenities=["wifi", "breakfast"],
    fetch_mode="common"
)

for hotel in result.hotels:
    print(f"Name: {hotel.name}")
    print(f"Price: ${hotel.price}")
    print(f"Rating: {hotel.rating}")
    print(f"Amenities: {hotel.amenities}")
    print(f"URL: {hotel.url}")
    print("---")

# Limit results to 5 hotels
result = get_hotels(
    hotel_data=hotel_data,
    guests=guests,
    room_type="standard",
    amenities=["wifi", "breakfast"],
    limit=5
)

# Sort by price (descending)
result = get_hotels(
    hotel_data=hotel_data,
    guests=guests,
    room_type="standard",
    amenities=["wifi", "breakfast"],
    sort_by="price"
)

# Sort by rating (descending)
result = get_hotels(
    hotel_data=hotel_data,
    guests=guests,
    room_type="standard",
    amenities=["wifi", "breakfast"],
    sort_by="rating"
)

# Default sort is by best value (highest rating/price ratio)
result = get_hotels(
    hotel_data=hotel_data,
    guests=guests,
    room_type="standard",
    amenities=["wifi", "breakfast"]
)

# Use an IATA airport code as location
hotel_data = [HotelData(
    checkin_date="2025-06-23", 
    checkout_date="2025-06-25", 
    location="HND",  # Haneda Airport
    room_type="standard",
    amenities=["wifi", "breakfast"]
)]
result = get_hotels(
    hotel_data=hotel_data,
    guests=guests,
    room_type="standard",
    amenities=["wifi", "breakfast"]
)
```

## API

### get_hotels(hotel_data, guests, room_type="standard", amenities=None, fetch_mode="common", limit=None, sort_by=None)
- `hotel_data`: List of `HotelData` objects
- `guests`: `Guests` object (adults, children, infants)
- `room_type`: "standard", "deluxe", or "suite"
- `amenities`: List of preferred amenities (e.g., ["wifi", "breakfast"])
- `fetch_mode`: "common", "fallback", "force-fallback", or "local"
- `limit`: Maximum number of hotels to return (default: all)
- `sort_by`: 'price', 'rating', or None (default: best value, i.e., highest rating/price ratio)
- Returns: `Result` with `.hotels` (list of `Hotel`), `.lowest_price`, and `.current_price`

### Models
- `HotelData`: checkin_date, checkout_date, location (city name or IATA airport code), room_type, amenities
- `Guests`: adults, children, infants
- `Hotel`: name, price, rating, amenities, url
- `Result`: hotels (list of Hotel), lowest_price, current_price

### Fetch Modes
- `"common"`: Use fast HTTP requests (default)
- `"fallback"`: Use HTTP requests, fallback to Playwright if needed
- `"force-fallback"`: Use Playwright directly
- `"local"`: Use local Playwright instance

## Location Support
The library automatically converts IATA airport codes to city names using a comprehensive airport database:
- `"HND"` → `"Tokyo"`
- `"CDG"` → `"Paris"`
- `"JFK"` → `"New York"`
- And many more...

## License
MIT
