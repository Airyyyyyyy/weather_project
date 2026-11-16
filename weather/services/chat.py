"""Quick Help widget logic — plain keyword matching, not AI/NLP."""
import logging

from .recommendations import get_activity_suggestion, get_clothing_advice
from .weather_api import get_current_weather_many

logger = logging.getLogger(__name__)


def get_tracked_cities_weather(cities):
    """Get detailed current weather for all tracked cities."""
    return [info for info in get_current_weather_many(cities) if info]


def generate_enhanced_chat_response(user_message, tracked_cities_weather, cities):
    """Generate a response based on keyword matches and city context."""
    user_message = user_message.lower()

    mentioned_city = extract_city_from_message(user_message, cities)

    if any(word in user_message for word in ['hello', 'hi', 'hey', 'greetings']):
        if cities:
            city_list = ", ".join(cities)
            return f"Hello! I'm your weather assistant. I see you're tracking: {city_list}. You can ask about specific cities or say 'help' for options."
        else:
            return "Hello! I'm your weather assistant. You haven't added any cities yet. Add cities to get personalized weather insights!"

    elif any(word in user_message for word in ['help', 'what can you do', 'options']):
        help_text = "I can help you with:\n• Current weather in your tracked cities\n• Specific city details (mention the city name)\n• Clothing recommendations\n• Activity suggestions\n• Weather alerts and insights\n\nTry: 'What's the weather in [city]?' or 'What should I wear in [city]?'"
        return help_text

    elif any(word in user_message for word in ['cities', 'tracking', 'list', 'my cities']):
        if cities:
            city_list = ", ".join(cities)
            return f"You're currently tracking: {city_list}. Which city would you like to know more about?"
        else:
            return "You haven't added any cities yet. Use the search box above to add cities to your list!"

    elif any(phrase in user_message for phrase in ['what should i wear', 'what to wear', "what should i pack", 'wear', 'clothing', 'jacket', 'umbrella', 'outfit']):
        if mentioned_city:
            return get_clothing_recommendation(mentioned_city, tracked_cities_weather)
        elif tracked_cities_weather:
            return get_clothing_recommendation(tracked_cities_weather[0]['city'], tracked_cities_weather)
        else:
            return "I can give clothing recommendations if you add cities to track. Which city are you interested in?"

    elif mentioned_city and any(word in user_message for word in ['weather', 'temperature', 'how hot', 'how cold', 'forecast']):
        return get_city_specific_response(mentioned_city, tracked_cities_weather, user_message)

    elif any(word in user_message for word in ['weather', 'temperature', 'how hot', 'how cold', 'forecast']):
        if tracked_cities_weather:
            weather_summary = generate_weather_summary(tracked_cities_weather)
            return f"Here's your current weather:\n{weather_summary}\n\nAsk about a specific city for more details!"
        else:
            return "I don't see any tracked cities. Add cities first to get weather information."

    elif any(word in user_message for word in ['do', 'activity', 'outdoor', 'indoor', 'recommend']):
        if mentioned_city:
            return get_activity_recommendation(mentioned_city, tracked_cities_weather)
        elif tracked_cities_weather:
            return get_activity_recommendation(tracked_cities_weather[0]['city'], tracked_cities_weather)
        else:
            return "I can suggest activities based on weather conditions. Add a city to get started!"

    else:
        if cities:
            return "I'm not sure I understand. You can ask me about weather in your tracked cities, clothing recommendations, or activity suggestions. Try mentioning a city name or say 'help' for options."
        else:
            return "I'm here to help with weather! First, add some cities to track using the search box above, then you can ask me about weather conditions, clothing, or activities."


def extract_city_from_message(message, cities):
    """Extract a mentioned city name from the user message."""
    for city in cities:
        if city.lower() in message:
            return city
    return None


def get_city_specific_response(city_name, tracked_cities_weather, user_message):
    """Generate a detailed response for a specific city."""
    city_weather = next((w for w in tracked_cities_weather if w['city'].lower() == city_name.lower()), None)

    if not city_weather:
        return f"I couldn't find weather data for {city_name}. It might not be in your tracked cities list."

    temp = city_weather['temperature']
    desc = city_weather['description']
    humidity = city_weather['humidity']
    wind = city_weather['wind_speed']

    response = f"Weather in {city_name}\n\n"
    response += f"• Temperature: {temp}°C (feels like {city_weather['feels_like']}°C)\n"
    response += f"• Conditions: {desc.title()}\n"
    response += f"• Humidity: {humidity}%\n"
    response += f"• Wind Speed: {wind} m/s\n"
    response += f"• Pressure: {city_weather['pressure']} hPa\n"

    return response


def generate_weather_summary(weather_data):
    """Summarize all tracked cities' current weather."""
    summary = []
    for weather in weather_data:
        summary.append(f"• {weather['city']}: {weather['temperature']}°C, {weather['description'].title()}")
    return "\n".join(summary)


def get_clothing_recommendation(city_name, tracked_cities_weather):
    """Clothing recommendation for a specific tracked city."""
    city_weather = next((w for w in tracked_cities_weather if w['city'].lower() == city_name.lower()), None)

    if not city_weather:
        return f"I don't have current weather data for {city_name}."

    temp = city_weather['temperature']
    desc = city_weather['description'].lower()

    advice = get_clothing_advice(temp, desc)
    return f"Clothing recommendation for {city_name} ({temp}°C, {desc.title()}):\n{advice}"


def get_activity_recommendation(city_name, tracked_cities_weather):
    """Activity recommendation for a specific tracked city."""
    city_weather = next((w for w in tracked_cities_weather if w['city'].lower() == city_name.lower()), None)

    if not city_weather:
        return f"I don't have current weather data for {city_name}."

    temp = city_weather['temperature']
    desc = city_weather['description'].lower()

    activity = get_activity_suggestion(temp, desc)
    return f"Activity suggestion for {city_name} ({temp}°C, {desc.title()}):\n{activity}"
