from .models import HotelData, Guests, Result, Hotel
from .scraper import scrape_hotels
from typing import List
import asyncio
import logging

def get_hotels(hotel_data: List[HotelData], guests: Guests, fetch_mode: str = "local", debug: bool = False, limit: int = 10) -> Result:
    """
    Get hotels using either live scraping or mock data.
    Args:
        hotel_data (List[HotelData]): List of hotel search data (first item used).
        guests (Guests): Guest information.
        fetch_mode (str): 'live' for scraping, otherwise returns mock data.
        debug (bool): If True, enables debug mode in scraper.
        limit (int): Maximum number of hotels to return.
    Returns:
        Result: Result object containing hotels and price info.
    """
    if not hotel_data or not isinstance(hotel_data[0], HotelData):
        logging.error("hotel_data must be a non-empty list of HotelData.")
        return Result()
    if not isinstance(guests, Guests):
        logging.error("guests must be a Guests object.")
        return Result()
    if fetch_mode == "live":
        hotels = asyncio.run(scrape_hotels(hotel_data[0], guests, debug=debug, limit=limit))
        hotels = hotels[:limit]
        lowest_price = min((h.price for h in hotels), default=None)
        return Result(hotels=hotels, lowest_price=lowest_price, current_price=lowest_price)
    # Fallback to mock data
    hotels = [
        Hotel(name="Hotel Tokyo Central", price=120.0, rating=4.5, url="https://example.com/hotel1"),
        Hotel(name="Shinjuku Stay", price=95.0, rating=4.2, url="https://example.com/hotel2"),
        Hotel(name="Luxury Ginza", price=250.0, rating=4.8, url="https://example.com/hotel3"),
    ]
    hotels = hotels[:limit]
    lowest_price = min(h.price for h in hotels)
    return Result(hotels=hotels, lowest_price=lowest_price, current_price=lowest_price) 