# fast-hotels

A fast, simple hotel scraper for Google Hotels, inspired by fast-flights. Fetches hotel data (name, price, rating, amenities, etc.) using Playwright, with a simple synchronous API.

## Features
- Scrape Google Hotels for hotel data
- Simple, synchronous API (no Playwright or async knowledge needed)
- Returns structured hotel data (name, price, rating, amenities, ...)

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
        location="Tokyo"
    )
]
guests = Guests(adults=2, children=1)

result = get_hotels(hotel_data=hotel_data, guests=guests, fetch_mode="live")
for hotel in result.hotels:
    print(f"Name: {hotel.name}, Price: {hotel.price}, Rating: {hotel.rating}, Amenities: {hotel.amenities}")
```

## API

### get_hotels(hotel_data, guests, fetch_mode="live")
- `hotel_data`: List of `HotelData` (checkin_date, checkout_date, location)
- `guests`: `Guests` (adults, children)
- `fetch_mode`: "live" (scrape Google) or "mock" (return sample data)
- Returns: `Result` with `.hotels` (list of `Hotel`)

### Models
- `HotelData`: checkin_date, checkout_date, location
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
