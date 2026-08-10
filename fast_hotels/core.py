from typing import List, Literal, Optional
import time
import re

from selectolax.lexbor import LexborHTMLParser, LexborNode

from .schema import Hotel, Result
from .hotels_impl import HotelData, Guests
from .filter import THSData
from .fallback_playwright import fallback_playwright_fetch
from .primp import Client, Response
from .utils import get_city_from_iata


def _validate_location(location: str) -> str:
    """Validate and normalize a location string for hotel search.

    Returns the normalized city name or raises ValueError with a
    descriptive message if the input looks invalid.
    """
    if not location or not location.strip():
        raise ValueError("No location provided for hotel search.")
    stripped = location.strip()
    # Reject obviously non-geographic strings (URLs, random chars)
    if re.search(r'^https?://', stripped):
        raise ValueError(
            f"Location appears to be a URL, not a city: '{stripped}'. "
            "Please provide a city name or IATA airport code."
        )
    # Reject extremely long or gibberish-like strings
    if len(stripped) > 100:
        raise ValueError(
            f"Location is unusually long ({len(stripped)} chars). "
            "Please provide a city name or IATA airport code."
        )
    # Convert airport code to city name if needed
    city = get_city_from_iata(stripped)
    return city


def fetch(params: dict, location: str, max_retries: int = 2) -> Response:
    """Fast HTTP request to Google Hotels API with retry on transient failures."""
    city = _validate_location(location)
    location_url = city.strip().replace(' ', '+').lower()
    url = f"https://www.google.com/travel/hotels/{location_url}"

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            client = Client(impersonate="chrome_126", verify=False)
            res = client.get(url, params=params)
            if res.status_code == 200:
                return res
            # Non-200 response — raise to trigger retry or error
            raise AssertionError(f"{res.status_code} Result: {res.text_markdown[:300]}")
        except AssertionError as e:
            last_error = e
            if attempt < max_retries:
                delay = 2 ** attempt  # 1s, 2s backoff
                time.sleep(delay)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = 2 ** attempt
                time.sleep(delay)

    # Exhausted retries
    raise RuntimeError(
        f"Failed to fetch hotel results after {max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )


def get_hotels_from_filter(
    filter: THSData,
    currency: str = "",
    *,
    mode: Literal["common", "fallback", "force-fallback", "local"] = "common",
    sort_by: Optional[str] = None,
    limit: Optional[int] = None,
) -> Result:
    """Get hotels using a filter with multiple fallback strategies"""
    data = filter.as_b64()
    params = {
        "ths": data.decode("utf-8"),
        "hl": "en",
        "curr": currency,
    }
    # Extract location from the first HotelData
    if not filter.hotel_data or not getattr(filter.hotel_data[0], 'location', None):
        raise ValueError("No location found in hotel filter. Please specify a valid location in HotelData.")
    location = filter.hotel_data[0].location
    if mode in {"common", "fallback"}:
        try:
            res = fetch(params, location)
        except AssertionError as e:
            if mode == "fallback":
                res = fallback_playwright_fetch(params)
            else:
                raise e
    elif mode == "local":
        from .local_playwright import local_playwright_fetch
        res = local_playwright_fetch(params)
    else:
        res = fallback_playwright_fetch(params)
    try:
        return parse_response(res, sort_by=sort_by, limit=limit)
    except RuntimeError as e:
        # If parsing failed in common mode, try the fallback path automatically
        if mode == "common":
            return get_hotels_from_filter(filter, mode="fallback", sort_by=sort_by, limit=limit)
        if mode == "fallback":
            return get_hotels_from_filter(filter, mode="force-fallback", sort_by=sort_by, limit=limit)
        # For other modes, re-raise the parsing error
        raise e


def get_hotels(
    *,
    hotel_data: List[HotelData],
   
    guests: Guests,
    room_type: Literal["standard", "deluxe", "suite"] = "standard",
    fetch_mode: Literal["common", "fallback", "force-fallback", "local"] = "common",
    amenities: Optional[List[str]] = None,
    limit: Optional[int] = None,
    sort_by: Optional[str] = None,
) -> Result:
    """Main API function for getting hotels"""
    return get_hotels_from_filter(
        THSData.from_interface(
            hotel_data=hotel_data,
            guests=guests,
            room_type=room_type,
            amenities=amenities,
        ),
        mode=fetch_mode,
        sort_by=sort_by,
        limit=limit,
    )


def _diagnose_empty_response(text: str) -> str:
    """Inspect HTML response text for known failure patterns and return a
    descriptive message, or empty string if no pattern matched.
    """
    text_lower = text.lower()

    # Check for CAPTCHA / bot-detection pages
    captcha_indicators = [
        "captcha", "recaptcha", "verify you are human",
        "are you a robot", "unusual traffic", "automated queries",
        "sorry/index", "show that you're not a robot",
    ]
    for indicator in captcha_indicators:
        if indicator in text_lower:
            return (
                "Google Hotels returned a bot-detection or CAPTCHA page. "
                "The request was likely blocked due to rate limiting or "
                "suspicious traffic patterns. Try again later or use "
                "fetch_mode='fallback' or 'local'."
            )

    # Check for locale/region selection pages
    locale_indicators = [
        "select your language", "choose your country",
        "pick your region", "select a language",
    ]
    for indicator in locale_indicators:
        if indicator in text_lower:
            return (
                "Google Hotels returned a language/region selection page. "
                "The location may not be valid for hotel search, or Google "
                "redirected the request. Check that the location is a real city "
                "name or IATA code."
            )

    # Check for error/blocked pages (before empty-page check, since
    # status-code error pages can be very short)
    error_indicators = [
        "403 forbidden", "404 not found", "500 internal server error",
        "502 bad gateway", "503 service unavailable", "429 too many requests",
        "access denied", "blocked",
    ]
    for indicator in error_indicators:
        if indicator in text_lower:
            return (
                f"Google Hotels returned an error page: '{indicator}'. "
                "The service may be temporarily unavailable or the request "
                "may have been blocked."
            )

    # Check for empty/redirect pages
    if len(text.strip()) < 200:
        return (
            "Google Hotels returned a near-empty or redirect page "
            f"({len(text.strip())} bytes). The location may be invalid "
            "or Google may have changed their page structure."
        )

    # No pattern matched — generic message with snippet
    snippet = text[:500].replace('\n', ' ')[:300]
    return (
        "No hotels found. The page structure may have changed, "
        "or the location returned no results. "
        f"Response snippet: {snippet}..."
    )


def parse_response(
    r: Response, *, dangerously_allow_looping_last_item: bool = False, sort_by: Optional[str] = None, limit: Optional[int] = None
) -> Result:
    """Parse the HTML response from Google Hotels"""
    class _blank:
        def text(self, *_, **__):
            return ""
        def iter(self):
            return []
    blank = _blank()
    def safe(n: Optional[LexborNode]):
        return n or blank
    parser = LexborHTMLParser(r.text)
    hotels = []
    # Use div.uaTTDe for hotel cards
    hotel_cards = parser.css('div.uaTTDe')
    for idx, card in enumerate(hotel_cards):
        # --- NAME EXTRACTION ---
        name = None
        name_elem = card.css_first('h2.BgYkof')
        if name_elem:
            name = name_elem.text(strip=True)
        # --- RATING EXTRACTION ---
        rating = None
        rating_elem = card.css_first('span.KFi5wf.lA0BZ')
        if rating_elem:
            rating_text = rating_elem.text(strip=True)
            try:
                rating = float(rating_text)
            except Exception:
                pass
        else:
            rating_elem = card.css_first('span[aria-label*="out of 5 stars"]')
            if rating_elem:
                aria_label = rating_elem.attributes.get('aria-label', '')
                import re
                m = re.search(r'([0-9.]+) out of 5', aria_label)
                if m:
                    rating = float(m.group(1))
        # --- AMENITIES EXTRACTION ---
        amenities = []
        amenity_selectors = [
            'span.LtjZ2d',
            'span[class*="QYEgn"]',
            'span[class*="amenity"]',
            'div[class*="amenity"]',
            'span[class*="feature"]',
            'div[class*="feature"]'
        ]
        for selector in amenity_selectors:
            amenity_elems = card.css(selector)
            if amenity_elems:
                for a in amenity_elems:
                    text = a.text(strip=True)
                    if text and text not in amenities and len(text) > 2:
                        amenities.append(text)
                if amenities:
                    break
        if not amenities:
            card_text = card.text(strip=True)
            import re
            amenity_patterns = [
                r'Amenities for [^:]+: ([^.]+)',
                r'([A-Za-z\s]+(?:\s*\(\$\))?)(?=,|$)',
            ]
            for pattern in amenity_patterns:
                matches = re.findall(pattern, card_text)
                for match in matches:
                    if isinstance(match, str):
                        potential_amenities = [a.strip() for a in match.split(',') if a.strip() and len(a.strip()) > 2]
                        for amenity in potential_amenities:
                            if amenity not in amenities and not amenity.isdigit():
                                amenities.append(amenity)
                    if amenities:
                        break
        # --- URL EXTRACTION ---
        url = None
        link_elem = card.css_first('a[href]')
        if link_elem:
            url = link_elem.attributes.get('href')
            if url and url.startswith('/travel/'):
                url = 'https://www.google.com' + url
        # --- PRICE EXTRACTION ---
        price = None
        import re
        card_text = card.text(strip=True)
        price_matches = re.findall(r'[$₹£€]\s?([0-9][0-9,.]*)', card_text)
        if price_matches:
            try:
                parsed_prices = [float(p.replace(',', '')) for p in price_matches]
                # When a discount is shown, Google renders both the original
                # (crossed-out) and current price; the current price is the
                # lower of the two, so take the minimum rather than the first match.
                price = min(parsed_prices)
            except Exception:
                price = None
        if name and price is not None:
            hotels.append({
                "name": name,
                "price": price,
                "rating": rating,
                "amenities": amenities,
                "url": url,
            })
    if not hotels:
        # Fallback: try to extract any hotel-like data from the HTML
        import re
        price_pattern = r'[$₹£€]\s?(\d[\d,]*(?:\.\d+)?)'
        prices = re.findall(price_pattern, r.text)
        name_pattern = r'<h2[^>]*>([^<]+)</h2>'
        names = re.findall(name_pattern, r.text)
        potential_names = []
        for line in r.text.split('\n'):
            line = line.strip()
            if len(line) > 10 and len(line) < 100 and not line.startswith('<') and not line.startswith('$'):
                potential_names.append(line)
        for i, price_str in enumerate(prices[:10]):
            try:
                price = float(price_str.replace(',', ''))
                name = f"Hotel {i+1}"
                if i < len(names):
                    name = names[i].strip()
                elif i < len(potential_names):
                    name = potential_names[i]
                hotels.append({
                    "name": name,
                    "price": price,
                    "rating": None,
                    "amenities": [],
                    "url": None,
                })
            except:
                continue
    if not hotels:
        diagnosis = _diagnose_empty_response(r.text)
        raise RuntimeError(diagnosis)
    if sort_by == "price":
        hotels.sort(key=lambda h: h["price"], reverse=True)
    elif sort_by == "rating":
        hotels.sort(key=lambda h: h["rating"] or 0, reverse=True)
    else:
        def value_ratio(h):
            if h["rating"] and h["price"] and h["price"] > 0:
                return h["rating"] / h["price"]
            return 0
        hotels.sort(key=value_ratio, reverse=True)
    if limit:
        hotels = hotels[:limit]
    lowest_price = min((h["price"] for h in hotels if h["price"] > 0), default=None)
    return Result(
        hotels=[Hotel(**hotel) for hotel in hotels],
        lowest_price=lowest_price,
        current_price=lowest_price
    ) 