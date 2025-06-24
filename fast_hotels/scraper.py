from .models import HotelData, Guests, Hotel
from typing import List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re

async def scrape_hotels(hotel_data: HotelData, guests: Guests) -> List[Hotel]:
    hotels = []
    async with async_playwright() as p:
        # Use headed mode for debugging
        browser = await p.chromium.launch(headless=False)
        # Set a realistic user-agent
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        try:
            # Build the Google Hotels search URL
            location = hotel_data.location.replace(' ', '+')
            url = (
                f"https://www.google.com/travel/hotels/{location}"
                f"?checkin={hotel_data.checkin_date}&checkout={hotel_data.checkout_date}"
                f"&adults={guests.adults}&children={guests.children}"
            )
            print(f"Navigating to: {url}")
            await page.goto(url)
            print(f"Landed on: {page.url}")
            print("Current URL after navigation:", page.url)

            # Wait for JS to load results
            await page.wait_for_timeout(5000)  # Wait 5 seconds

            # Dump full HTML to a file for inspection
            html = await page.content()
            with open("google_hotels_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Saved full page HTML to google_hotels_debug.html")

            # Print all divs with children and their class/id
            divs = await page.query_selector_all("div")
            for i, div in enumerate(divs):
                children = await div.query_selector_all(":scope > *")
                if children:
                    class_name = await div.get_attribute("class")
                    div_id = await div.get_attribute("id")
                    print(f"Div {i+1}: class='{class_name}', id='{div_id}', children={len(children)}")

            # Check for consent/cookie popups
            consent = await page.query_selector('form[action*="consent"]')
            if consent:
                print("Consent popup detected!")
                html = await consent.inner_html()
                print(f"Consent popup HTML (first 500 chars): {html[:500]}")
            else:
                print("No consent popup detected.")

            # Print if main container exists
            main_exists = await page.query_selector('div[role="main"]')
            print(f"div[role='main'] exists: {bool(main_exists)}")
            if not main_exists:
                html = await page.content()
                print("Page HTML (first 1000 chars):", html[:1000])

            print("Trying new selectors for hotel cards...")
            hotel_cards = []
            try:
                await page.wait_for_selector('div.x2A2jf', timeout=15000)
                hotel_cards = await page.query_selector_all('div.x2A2jf')
                print(f"Found {len(hotel_cards)} hotel cards with class 'x2A2jf'.")
            except PlaywrightTimeoutError:
                print("Timeout waiting for 'div.x2A2jf'. Trying next selector...")

            if not hotel_cards:
                try:
                    await page.wait_for_selector('div.GIPbOc.sSHqwe', timeout=15000)
                    hotel_cards = await page.query_selector_all('div.GIPbOc.sSHqwe')
                    print(f"Found {len(hotel_cards)} hotel cards with class 'GIPbOc sSHqwe'.")
                except PlaywrightTimeoutError:
                    print("Timeout waiting for 'div.GIPbOc.sSHqwe'.")

            if not hotel_cards:
                print("No hotel cards found with new selectors.")
            else:
                # Print the full HTML of the first card for inspection
                first_card_html = await hotel_cards[0].inner_html()
                print(f"First hotel card FULL HTML:\n{first_card_html}")

                # For the first card, print the class and text content of all descendants
                print("All descendant elements of first hotel card:")
                descendants = await hotel_cards[0].query_selector_all('*')
                for didx, desc in enumerate(descendants):
                    desc_class = await desc.get_attribute('class')
                    desc_text = await desc.text_content()
                    print(f"  Descendant {didx+1}: class={desc_class!r}, text={desc_text!r}")

                # Print parent HTML and text content
                parent = await hotel_cards[0].evaluate_handle('el => el.parentElement')
                parent_html = await parent.inner_html()
                parent_text = await parent.text_content()
                print(f"Parent element HTML:\n{parent_html}\n")
                print(f"Parent element text content:\n{parent_text!r}\n")

                # For each card, print the full HTML and text content of all direct children (for the first 2 cards)
                for idx, card in enumerate(hotel_cards[:2]):  # Just first 2 for now
                    card_html = await card.inner_html()
                    print(f"Hotel {idx+1} FULL Card HTML:\n{card_html}\n")
                    # Print text content of all direct children
                    children = await card.query_selector_all(':scope > *')
                    for cidx, child in enumerate(children):
                        text = await child.text_content()
                        print(f"  Child {cidx+1} text: {text!r}")

                # Get both hotel name cards and price cards by index
                name_cards = await page.query_selector_all('div.uaTTDe')
                price_cards = await page.query_selector_all('div.x2A2jf')
                print(f"Found {len(name_cards)} hotel name cards with class 'uaTTDe'.")
                print(f"Found {len(price_cards)} hotel price cards with class 'x2A2jf'.")
                hotels = []
                for idx in range(min(len(name_cards), len(price_cards), 10)):
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
                        # Fallback: aria-label
                        rating_elem = await card.query_selector('span[aria-label*="out of 5 stars"]')
                        if rating_elem:
                            aria_label = await rating_elem.get_attribute('aria-label')
                            import re
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

                    # --- PRICE EXTRACTION (from price_cards) ---
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
                    # Parse price to float
                    price_value = None
                    if price:
                        import re
                        m = re.search(r'\$([0-9,.]+)', price)
                        if m:
                            try:
                                price_value = float(m.group(1).replace(',', ''))
                            except Exception:
                                pass

                    print(f"Hotel {idx+1}: Name: {name}, Price: {price_value}, Rating: {rating}, Amenities: {amenities}")

                    if name and price_value is not None:
                        hotels.append(Hotel(name=name, price=price_value, rating=rating, amenities=amenities))
        except PlaywrightTimeoutError:
            print("Timeout while loading Google Hotels page or results.")
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()
    print(f"Returning {len(hotels)} hotels.")
    return hotels 