from .models import HotelData, Guests, Hotel
from typing import List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import logging

async def scrape_hotels(hotel_data: HotelData, guests: Guests, debug: bool = False, limit: int = 10) -> List[Hotel]:
    """
    Scrape hotel data from Google Hotels for the given hotel_data and guests.
    Args:
        hotel_data (HotelData): Search parameters for hotels.
        guests (Guests): Guest information.
        debug (bool): If True, dumps HTML and extra debug info.
        limit (int): Maximum number of hotels to return.
    Returns:
        List[Hotel]: List of scraped hotels.
    """
    hotels = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        try:
            # Validate input
            if not hotel_data.location or not hotel_data.checkin_date or not hotel_data.checkout_date:
                logging.error("Missing required hotel_data fields.")
                return []
            if guests.adults < 1:
                logging.error("At least one adult guest is required.")
                return []
            location = hotel_data.location.replace(' ', '+')
            url = (
                f"https://www.google.com/travel/hotels/{location}"
                f"?checkin={hotel_data.checkin_date}&checkout={hotel_data.checkout_date}"
                f"&adults={guests.adults}&children={guests.children}"
            )
            logging.info(f"Navigating to: {url}")
            await page.goto(url)
            await page.wait_for_timeout(5000)  # Wait for JS to load results
            if debug:
                html = await page.content()
                with open("google_hotels_debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
                logging.debug("Saved full page HTML to google_hotels_debug.html")
            # Check for consent/cookie popups
            consent = await page.query_selector('form[action*="consent"]')
            if consent:
                logging.warning("Consent popup detected! Scraper may not work as expected.")
                return []
            # Try selectors for hotel cards
            hotel_cards = []
            try:
                await page.wait_for_selector('div.x2A2jf', timeout=15000)
                hotel_cards = await page.query_selector_all('div.x2A2jf')
            except PlaywrightTimeoutError:
                logging.warning("Timeout waiting for 'div.x2A2jf'. Trying next selector...")
            if not hotel_cards:
                try:
                    await page.wait_for_selector('div.GIPbOc.sSHqwe', timeout=15000)
                    hotel_cards = await page.query_selector_all('div.GIPbOc.sSHqwe')
                except PlaywrightTimeoutError:
                    logging.error("Timeout waiting for 'div.GIPbOc.sSHqwe'. No hotel cards found.")
                    return []
            # Get hotel name and price cards
            name_cards = await page.query_selector_all('div.uaTTDe')
            price_cards = await page.query_selector_all('div.x2A2jf')
            for idx in range(min(len(name_cards), len(price_cards), limit)):
                card = name_cards[idx]
                # --- NAME EXTRACTION ---
                name = None
                name_elem = await card.query_selector('h2.BgYkof')
                if name_elem:
                    name = (await name_elem.text_content()).strip()
                # --- RATING EXTRACTION ---
                rating = None
                rating_elem = await card.query_selector('span.KFi5wf.lA0BZ')
                if rating_elem:
                    rating_text = await rating_elem.text_content()
                    try:
                        rating = float(rating_text)
                    except Exception:
                        pass
                else:
                    rating_elem = await card.query_selector('span[aria-label*="out of 5 stars"]')
                    if rating_elem:
                        aria_label = await rating_elem.get_attribute('aria-label')
                        m = re.search(r'([0-9.]+) out of 5', aria_label or '')
                        if m:
                            rating = float(m.group(1))
                # --- AMENITIES EXTRACTION ---
                amenities = []
                amenity_elems = await card.query_selector_all('span.LtjZ2d')
                if not amenity_elems:
                    amenity_elems = await card.query_selector_all('span[class*="QYEgn"]')
                for a in amenity_elems:
                    text = await a.text_content()
                    if text:
                        amenities.append(text.strip())
                # --- PRICE EXTRACTION ---
                price = None
                price_card = price_cards[idx]
                price_container = await price_card.query_selector('div.GIPbOc.sSHqwe')
                if price_container:
                    price_divs = await price_container.query_selector_all('div')
                    for div in price_divs:
                        div_text = await div.text_content()
                        if div_text and '$' in div_text:
                            price = div_text.strip()
                            break
                price_value = None
                if price:
                    m = re.search(r'\$([0-9,.]+)', price)
                    if m:
                        try:
                            price_value = float(m.group(1).replace(',', ''))
                        except Exception:
                            pass
                # --- URL EXTRACTION ---
                url = None
                link_elem = await card.query_selector('a[href]')
                if link_elem:
                    url = await link_elem.get_attribute('href')
                    if url and url.startswith('/travel/'):
                        url = 'https://www.google.com' + url
                # ---
                if name and price_value is not None:
                    hotels.append(Hotel(name=name, price=price_value, rating=rating, amenities=amenities, url=url))
        except PlaywrightTimeoutError:
            logging.error("Timeout while loading Google Hotels page or results.")
        except Exception as e:
            logging.exception(f"Error during scraping: {e}")
        finally:
            await browser.close()
    logging.info(f"Returning {len(hotels)} hotels.")
    return hotels[:limit] 