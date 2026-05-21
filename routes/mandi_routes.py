from flask import request, jsonify, current_app
import requests


def get_mandi_rates():
    api_key   = current_app.config['MANDI_API_KEY']
    state     = request.args.get('state', 'Madhya Pradesh')
    district  = request.args.get('district', '')
    commodity = request.args.get('commodity', '')
    limit     = request.args.get('limit', '50')

    if not api_key or api_key == 'placeholder':
        return jsonify({'error': 'Mandi API key not configured.'}), 500

    try:
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

        params = {
            'api-key': api_key,
            'format' : 'json',
            'limit'  : limit,
            'offset' : '0',
        }

        if state:
            params['filters[state.keyword]'] = state
        if district:
            params['filters[district.keyword]'] = district
        if commodity:
            params['filters[commodity]'] = commodity

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept'    : 'application/json',
        }

        resp = requests.get(url, params=params, headers=headers, timeout=30)

        if resp.status_code == 403:
            return jsonify({
                'error': '403 Forbidden. Check your API key.'
            }), 403

        if resp.status_code != 200:
            return jsonify({
                'error': f'API returned {resp.status_code}. Try again later.'
            }), 500

        data = resp.json()

        if 'error' in data:
            return jsonify({'error': f"API Error: {data['error']}"}), 400

        if 'records' not in data or not data['records']:
            return jsonify({
                'records': [],
                'total'  : 0,
                'state'  : state,
                'message': 'No records found. Try different filters.',
            }), 200

        records = []
        for r in data['records']:
            records.append({
                'state'      : r.get('state', ''),
                'district'   : r.get('district', ''),
                'market'     : r.get('market', ''),
                'commodity'  : r.get('commodity', ''),
                'variety'    : r.get('variety', ''),
                'grade'      : r.get('grade', ''),
                'min_price'  : r.get('min_price', '0'),
                'max_price'  : r.get('max_price', '0'),
                'modal_price': r.get('modal_price', '0'),
                'date'       : r.get('arrival_date', ''),
            })

        return jsonify({
            'records' : records,
            'total'   : data.get('total', len(records)),
            'state'   : state,
            'district': district,
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 500

    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect. Check internet connection.'}), 500

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500