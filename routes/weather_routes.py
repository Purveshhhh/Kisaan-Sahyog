from flask import request, jsonify, current_app
import requests

def get_weather():
    api_key = current_app.config['OPENWEATHER_API_KEY']

    city = request.args.get('city', '').strip()
    lat  = request.args.get('lat', '').strip()
    lon  = request.args.get('lon', '').strip()

    try:
        # ── Build URL based on input type ──────────────
        if lat and lon:
            # Direct coordinates (from live location)
            current_url  = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&cnt=40"

        elif city:
            # Try city name first
            current_url  = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&cnt=40"

            # If city not found, try geocoding to get coordinates
            test = requests.get(current_url, timeout=10).json()
            if test.get('cod') != 200:
                # Fallback: use geocoding API to find nearest location
                geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city},IN&limit=5&appid={api_key}"
                geo_resp = requests.get(geo_url, timeout=10).json()

                if not geo_resp:
                    # Last fallback: search without country
                    geo_url2 = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={api_key}"
                    geo_resp = requests.get(geo_url2, timeout=10).json()

                if not geo_resp:
                    return jsonify({
                        'error': f"'{city}' not found. Try nearest big city or district headquarters.",
                        'suggestion': True
                    }), 404

                # Use first result coordinates
                found_lat = geo_resp[0]['lat']
                found_lon = geo_resp[0]['lon']
                found_name = geo_resp[0].get('local_names', {}).get('hi') or geo_resp[0]['name']

                current_url  = f"https://api.openweathermap.org/data/2.5/weather?lat={found_lat}&lon={found_lon}&appid={api_key}&units=metric"
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={found_lat}&lon={found_lon}&appid={api_key}&units=metric&cnt=40"
        else:
            # Default to Delhi
            current_url  = f"https://api.openweathermap.org/data/2.5/weather?q=Delhi&appid={api_key}&units=metric"
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q=Delhi&appid={api_key}&units=metric&cnt=40"

        # ── Fetch data ─────────────────────────────────
        current_resp  = requests.get(current_url,  timeout=10)
        forecast_resp = requests.get(forecast_url, timeout=10)

        current_data  = current_resp.json()
        forecast_data = forecast_resp.json()

        if current_data.get('cod') != 200:
            return jsonify({'error': 'Could not fetch weather. Try nearest district/city name.'}), 404

        # ── Process forecast ───────────────────────────
        daily = {}
        for item in forecast_data.get('list', []):
            date = item['dt_txt'].split(' ')[0]
            if date not in daily:
                daily[date] = {
                    'date':        date,
                    'temp_max':    item['main']['temp_max'],
                    'temp_min':    item['main']['temp_min'],
                    'description': item['weather'][0]['description'],
                    'icon':        item['weather'][0]['icon'],
                    'humidity':    item['main']['humidity'],
                    'wind':        item['wind']['speed'],
                }

        # ── Build response ─────────────────────────────
        result = {
            'city':        current_data['name'],
            'country':     current_data['sys']['country'],
            'temp':        round(current_data['main']['temp']),
            'feels_like':  round(current_data['main']['feels_like']),
            'temp_min':    round(current_data['main']['temp_min']),
            'temp_max':    round(current_data['main']['temp_max']),
            'humidity':    current_data['main']['humidity'],
            'pressure':    current_data['main']['pressure'],
            'wind_speed':  current_data['wind']['speed'],
            'wind_deg':    current_data['wind'].get('deg', 0),
            'description': current_data['weather'][0]['description'].title(),
            'icon':        current_data['weather'][0]['icon'],
            'visibility':  current_data.get('visibility', 0) // 1000,
            'clouds':      current_data['clouds']['all'],
            'sunrise':     current_data['sys']['sunrise'],
            'sunset':      current_data['sys']['sunset'],
            'lat':         current_data['coord']['lat'],
            'lon':         current_data['coord']['lon'],
            'forecast':    list(daily.values())[:5]
        }

        return jsonify(result)

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500