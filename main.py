from fast_flights import FlightData, Passengers, Result, get_flights
from datetime import datetime, timedelta

# Set departure date 90 days from today
departure_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

result: Result = get_flights(
    flight_data=[
        FlightData(date=departure_date, from_airport="TPE", to_airport="MYJ")
    ],
    trip="one-way",
    seat="economy",
    passengers=Passengers(adults=2, children=1, infants_in_seat=0, infants_on_lap=0),
    fetch_mode="local",
)

print(result)

# The price is currently... low/typical/high
print("The price is currently", result.current_price)