from fast_hotels.hotels_impl import HotelData, Guests
from fast_hotels import get_hotels
from fast_hotels.core import _diagnose_empty_response, _validate_location
import pytest


def test_get_hotels_returns_results():
    hotel_data = [HotelData(
        checkin_date="2025-06-23",
        checkout_date="2025-06-25",
        location="Tokyo",
        room_type="standard",
        amenities=["wifi", "breakfast"]
    )]
    guests = Guests(adults=2, children=1, infants=0)

    result = get_hotels(
        hotel_data=hotel_data,
        guests=guests,
        room_type="standard",
        amenities=["wifi", "breakfast"],
        fetch_mode="common",
        limit=5,
        sort_by="price"
    )

    assert len(result.hotels) > 0
    assert result.lowest_price is not None
    assert result.current_price is not None

    # Test that hotels have the expected structure
    for hotel in result.hotels:
        assert hotel.name is not None
        assert hotel.price is not None
        assert isinstance(hotel.amenities, list)


# ── Unit tests for _diagnose_empty_response ──────────────────────────

def test_diagnose_captcha_page():
    msg = _diagnose_empty_response("<html>Please verify you are human. Solve this captcha</html>")
    assert "CAPTCHA" in msg or "bot-detection" in msg


def test_diagnose_unusual_traffic():
    msg = _diagnose_empty_response(
        "<html>Our systems have detected unusual traffic from your computer network.</html>"
    )
    assert "CAPTCHA" in msg or "bot-detection" in msg


def test_diagnose_locale_page():
    msg = _diagnose_empty_response(
        '<html><h1>Select your language</h1><ul><li>English</li><li>Español</li></ul></html>'
    )
    assert "language" in msg or "region" in msg


def test_diagnose_empty_page():
    msg = _diagnose_empty_response("<html></html>")
    assert "empty" in msg or "redirect" in msg


def test_diagnose_error_page():
    msg = _diagnose_empty_response("<html><h1>403 Forbidden</h1></html>")
    assert "403" in msg or "error" in msg


def test_diagnose_429_rate_limit():
    msg = _diagnose_empty_response("<html><h1>429 Too Many Requests</h1></html>")
    assert "429" in msg or "error" in msg


def test_diagnose_generic_fallback():
    msg = _diagnose_empty_response(
        "<html><body><p>Some random page content without hotels</p></body></html>"
        + " extra padding " * 20
    )
    assert "No hotels found" in msg


# ── Unit tests for _validate_location ─────────────────────────────────

def test_validate_location_url_raises():
    with pytest.raises(ValueError, match="URL"):
        _validate_location("https://google.com")


def test_validate_location_empty_raises():
    with pytest.raises(ValueError, match="No location"):
        _validate_location("")
    with pytest.raises(ValueError, match="No location"):
        _validate_location("   ")


def test_validate_location_too_long_raises():
    long_str = "A" * 101
    with pytest.raises(ValueError, match="unusually long"):
        _validate_location(long_str)


def test_validate_location_valid_city_passes():
    result = _validate_location("Tokyo")
    assert result == "Tokyo"


def test_validate_location_iata_code_resolves():
    # JFK should resolve to a city name
    result = _validate_location("JFK")
    assert len(result) > 0
    assert result != "JFK"


# ── Integration test: parse_response raises descriptive error ─────────

class _FakeResponse:
    """Mimics the primp Response interface for unit testing."""
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.text_markdown = text
        self.status_code = status_code
        self.headers = {}
        self.url = "https://www.google.com/travel/hotels/test"


def test_parse_response_raises_descriptive_runtime_error():
    """When parse_response receives a page with no hotel cards and no
    recoverable data, it should raise RuntimeError with a human-readable
    message, not a raw HTML dump."""
    from fast_hotels.core import parse_response

    fake = _FakeResponse(
        text="<html><body>Please verify you are human</body></html>"
    )

    with pytest.raises(RuntimeError) as exc_info:
        parse_response(fake)

    err = str(exc_info.value)
    # Should be descriptive, not a raw HTML dump
    assert "bot-detection" in err or "CAPTCHA" in err
    assert len(err) < 500  # not a wall of HTML
