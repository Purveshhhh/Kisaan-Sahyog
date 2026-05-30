from flask import request, jsonify
import json
import os
from PIL import Image
import io


def detect_disease():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded.'}), 400

    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    allowed = {'jpg', 'jpeg', 'png', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed:
        return jsonify({'error': 'Only JPG, PNG, WEBP allowed.'}), 400

    img_bytes = file.read()
    model_path = os.path.join('ml', 'disease_model.h5')

    # ── Step 1: Try own trained model FIRST ───────
    if os.path.exists(model_path):
        print("🌿 disease_model.h5 found — using own trained model...")
        try:
            result = detect_with_own_model(img_bytes)
            if result is not None:
                print("✅ Own model succeeded.")
                return result
            else:
                print("⚠️ Own model returned no result — falling back to Gemini.")
        except FileNotFoundError as e:
            print(f"⚠️ Model file missing: {e} — falling back to Gemini.")
        except MemoryError:
            print("⚠️ Not enough memory for own model — falling back to Gemini.")
        except Exception as e:
            print(f"⚠️ Own model error: {type(e).__name__}: {e} — falling back to Gemini.")
    else:
        print("⚠️ disease_model.h5 not found — using Gemini directly.")

    # ── Step 2: Fallback to Gemini API ────────────
    print("🤖 Using Gemini API as fallback...")
    return detect_with_gemini(img_bytes)


def detect_with_own_model(img_bytes):
    from flask import jsonify
    try:
        from ml.predict_disease import predict_disease
        print("⏳ Running inference on own model...")
        results = predict_disease(img_bytes)

        if not results:
            print("⚠️ No results from own model.")
            return None

        print(f"✅ Own model top prediction: {results[0]['label']} ({results[0]['confidence']}%)")

        diseases = []
        for r in results:
            if not r['is_healthy']:
                info = get_disease_info(r['label'])
                diseases.append({
                    'name'          : r['condition'].replace('_', ' '),
                    'probability'   : r['confidence'],
                    'description'   : f"Detected in {r['plant']} plant with {r['confidence']}% confidence.",
                    'severity'      : 'High' if r['confidence'] > 70 else 'Medium',
                    'treatment'     : {
                        'chemical'  : info.get('chemical',   []),
                        'biological': info.get('biological', []),
                        'prevention': info.get('prevention', []),
                    },
                    'similar_images': [],
                })

        top        = results[0]
        is_healthy = top.get('is_healthy', True)

        return jsonify({
            'success'          : True,
            'plant_name'       : top.get('plant', 'Unknown Plant'),
            'plant_probability': top.get('confidence', 0),
            'is_healthy'       : is_healthy,
            'is_healthy_prob'  : top.get('confidence', 0) if is_healthy else round(100 - top.get('confidence', 0), 1),
            'diseases'         : diseases,
            'general_advice'   : 'Result from your locally trained AI model.',
            'model_type'       : 'custom_model',
        })

    except Exception as e:
        print(f"Own model error: {type(e).__name__}: {e}")
        return None


def detect_with_gemini(img_bytes):
    from flask import jsonify
    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        return jsonify({
            'error': 'Gemini API key not configured. Add GEMINI_API_KEY to .env'
        }), 500

    try:
        from google import genai
        from google.genai import types

        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        client = genai.Client(api_key=api_key)

        prompt = (
            "You are an expert agricultural scientist and plant pathologist. "
            "Analyze this plant/leaf image and provide a detailed disease assessment. "
            "Respond ONLY in this exact JSON format with no extra text or markdown: "
            '{"plant_name":"Common name","plant_probability":95,"is_healthy":false,'
            '"is_healthy_prob":10,"diseases":[{"name":"Disease name","probability":85,'
            '"description":"Brief description of symptoms","severity":"High",'
            '"treatment":{"chemical":["Chemical 1 with dosage","Chemical 2"],'
            '"biological":["Organic treatment","Natural remedy"],'
            '"prevention":["Prevention 1","Prevention 2","Prevention 3"]}}],'
            '"general_advice":"One line advice for Indian farmers"} '
            "Rules: if healthy set is_healthy=true and diseases=[]. "
            "List up to 3 diseases ordered by probability. "
            "Use Indian farming context and locally available chemicals. "
            "If not a plant set plant_name=Not a plant leaf and diseases=[]."
        )

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_bytes_out = img_byte_arr.getvalue()

        # Try models in order until one works
        models_to_try = [
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
]

        response = None
        last_error = None

        for model_name in models_to_try:
            try:
                print(f"⏳ Trying Gemini model: {model_name}")
                response = client.models.generate_content(
                    model    = model_name,
                    contents = [
                        types.Part.from_bytes(
                            data      = img_bytes_out,
                            mime_type = 'image/jpeg'
                        ),
                        prompt
                    ]
                )
                print(f"✅ Gemini model {model_name} succeeded.")
                break
            except Exception as e:
                print(f"⚠️ Model {model_name} failed: {e}")
                last_error = e
                continue

        if response is None:
            raise last_error

        text = response.text.strip()
        print(f"✅ Gemini response: {text[:200]}")

        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        data = json.loads(text)

        return jsonify({
            'success'          : True,
            'plant_name'       : data.get('plant_name',        'Unknown'),
            'plant_probability': data.get('plant_probability', 0),
            'is_healthy'       : data.get('is_healthy',        True),
            'is_healthy_prob'  : data.get('is_healthy_prob',   100),
            'diseases'         : data.get('diseases',          []),
            'general_advice'   : data.get('general_advice',    ''),
            'model_type'       : 'gemini',
        })

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return jsonify({
            'success'          : True,
            'plant_name'       : 'Plant detected',
            'plant_probability': 80,
            'is_healthy'       : True,
            'is_healthy_prob'  : 80,
            'diseases'         : [],
            'general_advice'   : 'Please try again with a clearer image.',
            'model_type'       : 'gemini',
        })

    except Exception as e:
        print(f"Gemini error: {type(e).__name__}: {e}")
        return jsonify({
            'error': f'Disease analysis failed. Please try again later. ({type(e).__name__})'
        }), 500


DISEASE_INFO = {
    'Tomato_Early_blight': {
        'chemical'  : ['Mancozeb 75WP @ 2g/L', 'Chlorothalonil 75WP @ 2g/L'],
        'biological': ['Trichoderma viride @ 5g/L', 'Neem oil 3ml/L'],
        'prevention': ['Crop rotation every 2 years', 'Remove infected leaves immediately'],
    },
    'Tomato_Late_blight': {
        'chemical'  : ['Metalaxyl + Mancozeb @ 2.5g/L', 'Cymoxanil @ 0.6g/L'],
        'biological': ['Bacillus subtilis spray', 'Copper hydroxide 0.3%'],
        'prevention': ['Use resistant varieties', 'Avoid wet foliage'],
    },
    'Tomato_Leaf_Mold': {
        'chemical'  : ['Carbendazim 50WP @ 1g/L', 'Iprodione 50WP @ 1.5g/L'],
        'biological': ['Increase ventilation', 'Trichoderma harzianum'],
        'prevention': ['Reduce humidity below 85%', 'Remove old plant debris'],
    },
    'Tomato_Bacterial_spot': {
        'chemical'  : ['Copper oxychloride @ 3g/L', 'Streptomycin sulfate @ 0.5g/L'],
        'biological': ['Pseudomonas fluorescens spray', 'Neem oil 5ml/L'],
        'prevention': ['Use disease-free seeds', 'Avoid overhead irrigation'],
    },
    'Tomato_Septoria_leaf_spot': {
        'chemical'  : ['Mancozeb @ 2g/L', 'Copper oxychloride @ 3g/L'],
        'biological': ['Neem oil spray', 'Proper plant spacing'],
        'prevention': ['Water at base only', 'Mulching to prevent soil splash'],
    },
    'Tomato_Spider_mites': {
        'chemical'  : ['Abamectin 1.8EC @ 0.5ml/L', 'Propargite 57EC @ 2ml/L'],
        'biological': ['Neem oil 5ml/L', 'Release predatory mites'],
        'prevention': ['Maintain humidity', 'Regular water spraying on leaves'],
    },
    'Tomato_Target_Spot': {
        'chemical'  : ['Azoxystrobin @ 1ml/L', 'Mancozeb 75WP @ 2g/L'],
        'biological': ['Trichoderma-based spray', 'Neem oil 3ml/L'],
        'prevention': ['Improve air circulation', 'Remove infected leaves'],
    },
    'Tomato_mosaic_virus': {
        'chemical'  : ['No chemical cure — remove infected plants immediately'],
        'biological': ['Control aphid vectors with neem oil', 'Use virus-free seedlings'],
        'prevention': ['Use resistant varieties', 'Control insect vectors', 'Sanitize tools'],
    },
    'Tomato_YellowLeaf_Curl_Virus': {
        'chemical'  : ['Imidacloprid @ 0.3ml/L for whitefly control'],
        'biological': ['Yellow sticky traps for whiteflies', 'Neem oil 5ml/L'],
        'prevention': ['Use virus-resistant varieties', 'Install insect-proof nets'],
    },
    'Potato_Early_blight': {
        'chemical'  : ['Mancozeb 75WP @ 2g/L', 'Azoxystrobin @ 1ml/L'],
        'biological': ['Trichoderma viride', 'Copper-based fungicide'],
        'prevention': ['Use certified seed tubers', 'Proper irrigation management'],
    },
    'Potato_Late_blight': {
        'chemical'  : ['Metalaxyl 8% + Mancozeb 64% @ 2.5g/L', 'Fenamidone @ 1.5g/L'],
        'biological': ['Bacillus subtilis', 'Copper hydroxide 0.3%'],
        'prevention': ['Plant disease-free tubers', 'Avoid excessive irrigation'],
    },
    'Pepper_Bacterial_spot': {
        'chemical'  : ['Copper oxychloride @ 3g/L', 'Streptomycin @ 0.5g/L'],
        'biological': ['Pseudomonas fluorescens', 'Neem oil 3ml/L'],
        'prevention': ['Use disease-free seeds', 'Crop rotation'],
    },
    'healthy': {
        'chemical'  : [],
        'biological': ['Continue regular monitoring', 'Preventive neem spray monthly'],
        'prevention': ['Maintain proper irrigation', 'Balanced fertilization'],
    },
}


def get_disease_info(label):
    for key in DISEASE_INFO:
        if key.lower() in label.lower():
            return DISEASE_INFO[key]
    return {
        'chemical'  : ['Consult local Krishi Vigyan Kendra'],
        'biological': ['Neem oil 5ml/L as preventive spray'],
        'prevention': ['Remove infected parts', 'Maintain field hygiene'],
    }