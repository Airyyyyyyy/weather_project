import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import CityForm
from django.contrib import messages
import json

def index(request):
    url = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=30ece25e8bed6b4c716a892435758ff8"

    # Get cities from session or initialize empty list
    cities = request.session.get('user_cities', [])
    
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['name'].strip()
            
            # Check if city is already in session
            if city_name.lower() in [city.lower() for city in cities]:
                messages.info(request, f"{city_name} already exists in your list.")
                return redirect('index')
            
            # Verify city exists using API
            r = requests.get(url.format(city_name)).json()
            
            if r.get('cod') == 200:
                # Add city to session
                cities.append(city_name)
                request.session['user_cities'] = cities
                request.session.modified = True
                messages.success(request, f"{city_name} added!")
            else:
                messages.error(request, f"City '{city_name}' not found!")
        
        return redirect('index')
    
    form = CityForm()
    weather_data = []

    # Get weather for all cities in session
    for city_name in cities:
        r = requests.get(url.format(city_name)).json()
        if r.get('main'):
            temp = r['main']['temp']
            city_weather = {
                'city': city_name,
                'temperature': temp,
                'description': r['weather'][0]['description'],
                'icon': r['weather'][0]['icon'],
            }
            weather_data.append(city_weather)

    context = {'weather_data': weather_data, 'form': form}
    return render(request, 'weather/weather.html', context)

def delete_city(request, city_name):
    if request.method == 'POST':
        # Get cities from session
        cities = request.session.get('user_cities', [])
        
        # Remove the city (case-insensitive)
        cities = [city for city in cities if city.lower() != city_name.lower()]
        
        # Update session
        request.session['user_cities'] = cities
        request.session.modified = True
        
        messages.success(request, f"{city_name} deleted!")
    
    return redirect('index')