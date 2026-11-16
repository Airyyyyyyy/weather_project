"""Rule-based weather recommendations (clothing, activities, alerts).

These are plain threshold-based heuristics, not machine learning — kept
separate from weather/ml/ so the two are never confused in the UI or code.
"""


def generate_rule_based_insight(city_name, temperature, description, humidity, wind_speed):
    """Rule-based weather tips for a city."""
    description_lower = description.lower()

    insights = []

    if temperature > 30:
        insights.append(f"Hot day in {city_name}! Stay hydrated, wear light clothing, and avoid prolonged sun exposure.")
    elif temperature > 25:
        insights.append(f"Warm weather in {city_name}. Perfect for outdoor activities with light clothing.")
    elif temperature > 15:
        insights.append(f"Pleasant temperatures in {city_name}. Great for walks and outdoor exploration.")
    elif temperature > 5:
        insights.append(f"Cool day in {city_name}. A light jacket would be comfortable.")
    else:
        insights.append(f"Cold weather in {city_name}. Dress warmly and protect against frostbite.")

    if 'rain' in description_lower:
        insights.append(f"Rainy conditions in {city_name}. Don't forget your umbrella and waterproof gear.")
    elif 'cloud' in description_lower:
        insights.append(f"Cloudy skies in {city_name}. Good lighting for photography and comfortable for outdoor activities.")
    elif 'clear' in description_lower:
        insights.append(f"Clear skies in {city_name}. Perfect for stargazing and outdoor events.")

    if wind_speed > 15:
        insights.append(f"Windy conditions in {city_name}. Secure loose objects and be cautious outdoors.")

    if humidity > 80:
        insights.append(f"High humidity in {city_name}. Stay hydrated and take breaks in air-conditioned spaces.")
    elif humidity < 30:
        insights.append(f"Low humidity in {city_name}. Use moisturizer and stay hydrated.")

    return " ".join(insights)


def generate_smart_alerts(weather_data):
    """Generate rule-based weather alerts based on current conditions."""
    alerts = []

    for weather in weather_data:
        city = weather['city']
        temp = weather['temperature']
        description = weather['description']
        humidity = weather.get('humidity', 0)
        wind_speed = weather.get('wind_speed', 0)

        if temp > 35:
            alerts.append({
                'city': city,
                'alert': 'Extreme heat warning! Stay indoors during peak hours and drink plenty of water.',
                'type': 'warning'
            })
        elif temp > 30:
            alerts.append({
                'city': city,
                'alert': 'Hot weather alert! Stay hydrated and avoid prolonged sun exposure.',
                'type': 'warning'
            })
        elif temp < 0:
            alerts.append({
                'city': city,
                'alert': 'Freezing temperatures! Dress in layers and protect against frostbite.',
                'type': 'warning'
            })
        elif temp < 5:
            alerts.append({
                'city': city,
                'alert': 'Cold weather warning. Wear warm clothing and limit time outdoors.',
                'type': 'info'
            })

        if 'rain' in description.lower():
            alerts.append({
                'city': city,
                'alert': 'Rain expected. Carry an umbrella and drive safely.',
                'type': 'info'
            })
        elif 'thunderstorm' in description.lower():
            alerts.append({
                'city': city,
                'alert': 'Thunderstorm warning! Stay indoors and avoid electronic devices.',
                'type': 'warning'
            })
        elif wind_speed > 15:
            alerts.append({
                'city': city,
                'alert': 'High wind advisory! Secure loose objects and be cautious outdoors.',
                'type': 'warning'
            })
        elif wind_speed > 10:
            alerts.append({
                'city': city,
                'alert': 'Windy conditions. Hold onto hats and be careful near buildings.',
                'type': 'info'
            })

        if humidity > 80:
            alerts.append({
                'city': city,
                'alert': 'High humidity. Stay hydrated and take breaks in air-conditioned spaces.',
                'type': 'info'
            })
        elif humidity < 30:
            alerts.append({
                'city': city,
                'alert': 'Low humidity. Use moisturizer and stay hydrated.',
                'type': 'info'
            })

    return alerts


def get_clothing_advice(temperature, description):
    """Rule-based clothing advice from temperature and conditions."""
    desc = description.lower()

    if temperature > 30:
        base = "Lightweight, breathable fabrics like cotton and linen. Short sleeves, shorts, and a wide-brimmed hat."
    elif temperature > 20:
        base = "Light layers - t-shirts with a light jacket or cardigan. Comfortable for most activities."
    elif temperature > 10:
        base = "Medium layers - long sleeves, light sweater, and a jacket. Consider a scarf."
    elif temperature > 0:
        base = "Warm layers - sweater, coat, gloves, and a warm hat. Multiple layers recommended."
    else:
        base = "Heavy winter clothing - thermal layers, heavy coat, insulated gloves, warm hat, and scarf."

    if 'rain' in desc:
        base += " Waterproof jacket and umbrella essential."
    if 'sun' in desc or 'clear' in desc:
        base += " Sunglasses and sunscreen recommended."
    if 'wind' in desc:
        base += " Wind-resistant outer layer advised."

    return base


def get_activity_suggestion(temperature, description):
    """Rule-based activity suggestion from temperature and conditions."""
    desc = description.lower()

    if 'rain' in desc or 'storm' in desc:
        return "Perfect for indoor activities: museums, libraries, cooking, movie marathon, or visiting cafes."
    elif temperature > 25:
        return "Great for water activities, early morning/late evening walks, or air-conditioned indoor spaces."
    elif temperature > 15:
        return "Ideal for outdoor activities: hiking, picnics, cycling, gardening, or exploring parks."
    elif temperature > 5:
        return "Good for brisk walks, visiting indoor attractions, coffee shops, or light outdoor activities."
    else:
        return "Best for indoor activities, winter sports if available, or short outdoor trips with proper gear."
