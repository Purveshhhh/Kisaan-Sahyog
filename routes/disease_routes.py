from flask import request, jsonify, current_app
import requests
import base64
import os

def detect_disease():
    api_key = current_app.config['PLANTID_API_KEY']

    if not api_key or api_key == 'placeholder':
        return jsonify({'error': 'Plant.id API key not configured.'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded.'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    allowed = {'jpg','jpeg','png','webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed:
        return jsonify({'error': 'Only JPG, PNG, WEBP images allowed.'}), 400

    try:
        # Read and encode image
        img_data    = file.read()
        img_base64  = base64.b64encode(img_data).decode('utf-8')

        # Call Plant.id Health Assessment API
        url = "https://api.plant.id/v2/health_assessment"

        payload = {
            "images"          : [img_base64],
            "modifiers"       : ["crops_fast", "similar_images"],
            "plant_language"  : "en",
            "health_assessment": {
                "generate_causes"       : True,
                "treatments"            : {"chemical": True, "biological": True, "prevention": True},
                "disease_details"       : ["description", "treatment"],
            }
        }

        headers = {
            "Content-Type" : "application/json",
            "Api-Key"      : api_key,
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)

        if resp.status_code == 401:
            return jsonify({'error': 'Invalid Plant.id API key.'}), 401

        if resp.status_code != 200:
            return jsonify({'error': f'API error: {resp.status_code}'}), 500

        data = resp.json()

        # Parse health assessment
        health = data.get('health_assessment', {})
        is_healthy = health.get('is_healthy', True)
        is_healthy_prob = health.get('is_healthy_probability', 1.0)

        diseases = []
        for d in health.get('diseases', [])[:5]:
            disease_details = d.get('disease_details', {})
            treatment       = disease_details.get('treatment', {})

            diseases.append({
                'name'       : d.get('name', 'Unknown'),
                'probability': round(d.get('probability', 0) * 100, 1),
                'description': disease_details.get('description', ''),
                'treatment'  : {
                    'chemical'  : treatment.get('chemical',   []),
                    'biological': treatment.get('biological', []),
                    'prevention': treatment.get('prevention', []),
                },
                'similar_images': [
                    img.get('url', '') for img in d.get('similar_images', [])[:2]
                ],
            })

        # Plant identification
        suggestions = data.get('suggestions', [])
        plant_name  = suggestions[0].get('plant_name', 'Unknown Plant') if suggestions else 'Unknown Plant'
        plant_prob  = round(suggestions[0].get('probability', 0) * 100, 1) if suggestions else 0

        return jsonify({
            'success'          : True,
            'plant_name'       : plant_name,
            'plant_probability': plant_prob,
            'is_healthy'       : is_healthy,
            'is_healthy_prob'  : round(is_healthy_prob * 100, 1),
            'diseases'         : diseases,
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500