from .models import HotelData, Guests, Result, Hotel
from .scraper import scrape_hotels
from typing import List, Optional
import asyncio
import logging
import datetime

def get_hotels(hotel_data: List[HotelData], guests: Guests, fetch_mode: str = "local", debug: bool = False, limit: Optional[int] = None, sort_by: Optional[str] = None) -> Result:
    """
    Get hotels using either live scraping or mock data.
    Args:
        hotel_data (List[HotelData]): List of hotel search data (first item used).
        guests (Guests): Guest information.
        fetch_mode (str): 'live' for scraping, otherwise returns mock data.
        debug (bool): If True, enables debug mode in scraper.
        limit (Optional[int]): Maximum number of hotels to return. If None, return all.
        sort_by (Optional[str]): 'price' or 'rating' to sort by that field, or None for best value (rating/price).
    Returns:
        Result: Result object containing hotels and price info.
    """
    if not hotel_data or not isinstance(hotel_data[0], HotelData):
        logging.error("hotel_data must be a non-empty list of HotelData.")
        return Result()
    if not isinstance(guests, Guests):
        logging.error("guests must be a Guests object.")
        return Result()
    # Validate checkin_date is not in the past
    try:
        checkin = datetime.datetime.strptime(hotel_data[0].checkin_date, "%Y-%m-%d").date()
        today = datetime.date.today()
        if checkin < today:
            logging.error("checkin_date cannot be in the past.")
            return Result()
    except Exception as e:
        logging.error(f"Invalid checkin_date format: {e}")
        return Result()
    if fetch_mode == "live":
        hotels = asyncio.run(scrape_hotels(hotel_data[0], guests, debug=debug, limit=limit))
    else:
        hotels = [
            Hotel(name="Hotel Tokyo Central", price=120.0, rating=4.5, url="https://example.com/hotel1"),
            Hotel(name="Shinjuku Stay", price=95.0, rating=4.2, url="https://example.com/hotel2"),
            Hotel(name="Luxury Ginza", price=250.0, rating=4.8, url="https://example.com/hotel3"),
        ]
    # Sorting logic
    if sort_by == "price":
        hotels.sort(key=lambda h: (h.price if h.price is not None else float('-inf')), reverse=True)
    elif sort_by == "rating":
        hotels.sort(key=lambda h: (h.rating if h.rating is not None else float('-inf')), reverse=True)
    else:
        # Best value: highest rating/price ratio
        def value_ratio(h):
            if h.rating is not None and h.price and h.price > 0:
                return h.rating / h.price
            return float('-inf')
        hotels.sort(key=value_ratio, reverse=True)
    if limit is not None:
        hotels = hotels[:limit]
    lowest_price = min((h.price for h in hotels if h.price is not None), default=None)
    return Result(hotels=hotels, lowest_price=lowest_price, current_price=lowest_price) 