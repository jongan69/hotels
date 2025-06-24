from .models import HotelData, Guests, Result, Hotel
from .scraper import scrape_hotels
from typing import List
import asyncio

def get_hotels(hotel_data: List[HotelData], guests: Guests, fetch_mode: str = "local") -> Result:
    if fetch_mode == "live":
        hotels = asyncio.run(scrape_hotels(hotel_data[0], guests))
        lowest_price = min(h.price for h in hotels) if hotels else None
        return Result(hotels=hotels, lowest_price=lowest_price, current_price=lowest_price)
    # Fallback to mock data
    hotels = [
        Hotel(name="Hotel Tokyo Central", price=120.0, rating=4.5, address="Tokyo, Japan", url="https://example.com/hotel1"),
        Hotel(name="Shinjuku Stay", price=95.0, rating=4.2, address="Shinjuku, Tokyo", url="https://example.com/hotel2"),
        Hotel(name="Luxury Ginza", price=250.0, rating=4.8, address="Ginza, Tokyo", url="https://example.com/hotel3"),
    ]
    lowest_price = min(h.price for h in hotels)
    return Result(hotels=hotels, lowest_price=lowest_price, current_price=lowest_price) 