import requests
from django.shortcuts import render, redirect
from .models import City
from .forms import CityForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
def index(request):
    url = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=30ece25e8bed6b4c716a892435758ff8"

    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['name']
            r = requests.get(url.format(city_name)).json()
            if r.get('cod') == 200:
                if not City.objects.filter(name__iexact=city_name).exists():
                    City.objects.create(name=city_name)
                    messages.success(request, f"{city_name} added!")
                else:
                    messages.info(request, f"{city_name} already exists.")
            else:
                messages.error(request, f"City '{city_name}' not found!")
        return redirect('index')
    
    form = CityForm()
    cities = City.objects.all()

    weather_data = []

    for city in cities:
        r = requests.get(url.format(city)).json()
        if r.get('main'):
            temp = r['main']['temp']
            city_weather = {
                'city': city.name,
                'temperature': temp,
                'description': r['weather'][0]['description'],
                'icon': r['weather'][0]['icon'],
                # 'temp_class': get_temperature_class(temp)
            }
            weather_data.append(city_weather)

    context = {'weather_data': weather_data, 'form': form}
    return render(request, 'weather/weather.html', context)

@csrf_exempt
def delete_city(request, city_name):
    if request.method == 'POST':
        City.objects.filter(name=city_name).delete()
        messages.success(request, f"{city_name} deleted!")
    return redirect('index')

# def get_temperature_class(temperature):
#     if temperature >= 30:
#         return 'Hot'
#     elif 25 <= temperature <= 29:
#         return 'warm' 
#     elif 20 <= temperature < 25:
#         return 'mild'     
#     elif 15 <= temperature < 20:
#         return 'cool'     
#     elif 0 <= temperature < 15:
#         return 'cold'     
#     else:
#         return 'freezing'
    