# fast-hotels

A fast, simple hotel scraper for Google Hotels, inspired by fast-flights. Fetches hotel data (name, price, rating, amenities, etc.) using Playwright, with a simple synchronous API.

## Features
- Scrape Google Hotels for hotel data
- Simple, synchronous API (no Playwright or async knowledge needed)
- Returns structured hotel data (name, price, rating, amenities, ...)
- **Sort results by price, rating, or best value (rating/price ratio)**
- **Limit the number of results returned**
- **Support for IATA airport codes as locations (e.g., 'CDG' → 'Charles de Gaulle Airport')**
- **Validates that check-in date is not in the past**

## Installation

```sh
pip install fast-hotels
# Then install Playwright browsers:
python -m playwright install
```

## Usage

```python
from fast_hotels import HotelData, Guests, get_hotels

hotel_data = [
    HotelData(
        checkin_date="2025-06-23",
        checkout_date="2025-06-25",
        location="Tokyo"  # or use an IATA code like "CDG"
    )
]
guests = Guests(adults=2, children=1)

# Basic usage
result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live")
for hotel in result.hotels:
    print(f"Name: {hotel.name}, Price: {hotel.price}, Rating: {hotel.rating}, Amenities: {hotel.amenities}")

# Limit results to 5 hotels
result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live", limit=5)

# Sort by price (descending)
result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live", sort_by="price")

# Sort by rating (descending)
result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live", sort_by="rating")

# Default sort is by best value (highest rating/price ratio)
result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live")

# Use an IATA airport code as location
hotel_data = [HotelData(checkin_date="2025-06-23", checkout_date="2025-06-25", location="CDG")]
result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live")

```

## API

### get_hotels(hotel_data, guests, fetch_mode="live", debug=False, limit=None, sort_by=None)
- `hotel_data`: List of `HotelData` (checkin_date, checkout_date, location)
- `guests`: `Guests` (adults, children)
- `fetch_mode`: "live" (scrape Google) or "mock" (return sample data)
- `debug`: If True, enables debug mode in scraper
- `limit`: Maximum number of hotels to return (default: all)
- `sort_by`: 'price', 'rating', or None (default: best value, i.e., highest rating/price ratio)
- Returns: `Result` with `.hotels` (list of `Hotel`)

### Models
- `HotelData`: checkin_date, checkout_date, location (city name or IATA airport code)
- `Guests`: adults, children
- `Hotel`: name, price, rating, amenities, ...
- `Result`: hotels (list of Hotel)

## Playwright
This package uses Playwright. After install, run:

```sh
python -m playwright install
```

## License
MIT
