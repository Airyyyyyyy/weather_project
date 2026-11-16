import json
import logging
from datetime import date

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import CityForm
from .ml.forecast_model import forecast_model
from .services import chat
from .services.recommendations import generate_rule_based_insight, generate_smart_alerts
from .services.weather_api import city_exists, get_current_weather

logger = logging.getLogger(__name__)


def index(request):
    cities = request.session.get('user_cities', [])

    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['name'].strip()

            if city_name.lower() in [city.lower() for city in cities]:
                messages.info(request, f"{city_name} already exists in your list.")
                return redirect('index')

            if city_exists(city_name):
                cities.append(city_name)
                request.session['user_cities'] = cities
                request.session.modified = True
                messages.success(request, f"{city_name} added!")
            else:
                messages.error(request, f"City '{city_name}' not found!")

        return redirect('index')

    form = CityForm()
    weather_data = []

    for city_name in cities:
        info = get_current_weather(city_name)
        if not info:
            logger.warning("Could not fetch weather for %s", city_name)
            continue

        insight = generate_rule_based_insight(
            city_name, info['temperature'], info['description'], info['humidity'], info['wind_speed']
        )
        forecast = forecast_model.predict(
            lat=info['lat'], lon=info['lon'], temp=info['temperature'],
            humidity=info['humidity'], pressure=info['pressure'],
            wind_speed=info['wind_speed'], description=info['description'], date=date.today(),
        )

        weather_data.append({
            **info,
            'insight': insight,
            'forecast': forecast,
        })

    context = {
        'weather_data': weather_data,
        'form': form,
        'smart_alerts': generate_smart_alerts(weather_data),
    }
    return render(request, 'weather/weather.html', context)


def delete_city(request, city_name):
    if request.method == 'POST':
        cities = request.session.get('user_cities', [])
        cities = [city for city in cities if city.lower() != city_name.lower()]
        request.session['user_cities'] = cities
        request.session.modified = True
        messages.success(request, f"{city_name} deleted!")

    return redirect('index')


def weather_chat(request):
    """Quick Help widget: keyword-matched responses, not AI/NLP."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').lower()
        cities = request.session.get('user_cities', [])

        tracked_cities_weather = chat.get_tracked_cities_weather(cities)
        response = chat.generate_enhanced_chat_response(user_message, tracked_cities_weather, cities)

        return JsonResponse({'response': response})
    except (json.JSONDecodeError, KeyError):
        logger.exception("Chat request failed")
        return JsonResponse({'error': 'Sorry, I encountered an error. Please try again.'})
