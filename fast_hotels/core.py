from typing import List, Literal, Optional

from selectolax.lexbor import LexborHTMLParser, LexborNode

from .schema import Hotel, Result
from .hotels_impl import HotelData, Guests
from .filter import THSData
from .fallback_playwright import fallback_playwright_fetch
from .primp import Client, Response
from .utils import get_city_from_iata


def fetch(params: dict, location: str) -> Response:
    """Fast HTTP request to Google Hotels API"""
    client = Client(impersonate="chrome_126", verify=False)
    if not location:
        raise ValueError("No location provided for hotel search.")
    # Convert airport code to city name if needed
    city = get_city_from_iata(location)
    # Clean up city for URL
    location_url = city.strip().replace(' ', '+').lower()
    url = f"https://www.google.com/travel/hotels/{location_url}"
    res = client.get(url, params=params)
    assert res.status_code == 200, f"{res.status_code} Result: {res.text_markdown}"
    return res


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
        if mode == "fallback":
            return get_hotels_from_filter(filter, mode="force-fallback", sort_by=sort_by, limit=limit)
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
        price_matches = re.findall(r'\$([0-9,.]+)', card_text)
        if price_matches:
            try:
                price = float(price_matches[0].replace(',', ''))
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
        price_pattern = r'\$(\d+(?:,\d+)?)'
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
        raise RuntimeError("No hotels found:\n{}".format(r.text_markdown))
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