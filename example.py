from fast_hotels.hotels_impl import HotelData, Guests
from fast_hotels import create_filter, get_hotels
import time

def main():
    # Create hotel search data (similar to FlightData in flights package)
    hotel_data = [
        HotelData(
            checkin_date="2025-06-23",
            checkout_date="2025-06-25",
            location="Tokyo",
            room_type="standard",
            amenities=["wifi", "breakfast"]
        )
    ]
    
    # Create guests (similar to Passengers in flights package)
    guests = Guests(
        adults=2,
        children=1,
        infants=0
    )
    
    # Create a filter (similar to flights package)
    filter = create_filter(
        hotel_data=hotel_data,
        guests=guests,
        room_type="standard",
        amenities=["wifi", "breakfast"]
    )
    
    # Print the base64 encoded filter (for debugging)
    print("Generated filter:")
    print(filter.as_b64().decode('utf-8'))
    
    # Test the new fast API
    print("\n--- Testing New Fast API ---")
    start_time = time.time()
    
    try:
        # Use the new fast architecture
        result = get_hotels(
            hotel_data=hotel_data,
            guests=guests,
            room_type="standard",
            amenities=["wifi", "breakfast"],
            fetch_mode="common",
            limit=5,
            sort_by="price"
        )
        
        elapsed = time.time() - start_time
        print(f"New API took {elapsed:.2f} seconds")
        print(f"Found {len(result.hotels)} hotels")
        
        for hotel in result.hotels:
            print(f"Name: {hotel.name}")
            print(f"Price: ${hotel.price}")
            print(f"Rating: {hotel.rating}")
            print(f"Amenities: {hotel.amenities}")
            print(f"URL: {hotel.url}")
            print("---")
            
        print(f"Lowest price: ${result.lowest_price}")
        print(f"Current price: ${result.current_price}")
        
    except Exception as e:
        print(f"New API failed: {e}")

if __name__ == "__main__":
    main() 