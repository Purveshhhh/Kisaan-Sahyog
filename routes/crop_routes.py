import warnings
warnings.filterwarnings('ignore', category=UserWarning)
from flask import request, jsonify
import pickle
import numpy as np
import os

BASE = os.path.dirname(__file__)

# Load model
try:
    with open(os.path.join(BASE, '..', 'ml', 'crop_model.pkl'), 'rb') as f:
        model = pickle.load(f)
    print("✅ Crop model loaded.")
except Exception as e:
    model = None
    print(f"❌ Model load error: {e}")

# Load feature stats
try:
    with open(os.path.join(BASE, '..', 'ml', 'feature_stats.pkl'), 'rb') as f:
        stats = pickle.load(f)
    print(f"✅ Stats loaded. Accuracy: {stats['accuracy']}%")
except:
    stats = None

# ── Crop information database ─────────────────────
CROP_INFO = {
    'rice'       : {'name_hi':'चावल',      'emoji':'🌾','season':'Kharif (Jun–Nov)',
                    'season_hi':'खरीफ (जून–नवंबर)','duration':'90–150 days',
                    'water':'High','profit':'⭐⭐⭐⭐',
                    'states':'West Bengal, Punjab, UP, Andhra Pradesh',
                    'msp':'₹2,183/quintal',
                    'tips':'Requires standing water. Transplant at 25 days. SRI method gives 30% more yield.',
                    'tips_hi':'खड़े पानी की जरूरत। 25 दिनों में रोपाई। SRI विधि से 30% अधिक उपज।'},
    'wheat'      : {'name_hi':'गेहूं',      'emoji':'🌿','season':'Rabi (Oct–Mar)',
                    'season_hi':'रबी (अक्टूबर–मार्च)','duration':'100–150 days',
                    'water':'Medium','profit':'⭐⭐⭐⭐',
                    'states':'Punjab, Haryana, UP, MP, Rajasthan',
                    'msp':'₹2,275/quintal',
                    'tips':'Sow at 20-25°C. Use certified seeds. Irrigate at crown root stage.',
                    'tips_hi':'20-25°C पर बुवाई। प्रमाणित बीज। क्राउन रूट पर सिंचाई।'},
    'maize'      : {'name_hi':'मक्का',      'emoji':'🌽','season':'Kharif & Rabi',
                    'season_hi':'खरीफ और रबी','duration':'80–110 days',
                    'water':'Medium','profit':'⭐⭐⭐',
                    'states':'Karnataka, MP, Bihar, Rajasthan',
                    'msp':'₹1,962/quintal',
                    'tips':'60x20 cm spacing. Well-drained soil. Critical irrigation at tasseling.',
                    'tips_hi':'60x20 सेमी दूरी। अच्छी जल निकासी। टैसेलिंग पर सिंचाई जरूरी।'},
    'cotton'     : {'name_hi':'कपास',       'emoji':'🌸','season':'Kharif (May–Nov)',
                    'season_hi':'खरीफ (मई–नवंबर)','duration':'150–180 days',
                    'water':'Medium','profit':'⭐⭐⭐⭐⭐',
                    'states':'Gujarat, Maharashtra, Telangana, Punjab',
                    'msp':'₹6,620/quintal',
                    'tips':'Use BT cotton for pest resistance. Deep plowing. 4-5 irrigations.',
                    'tips_hi':'BT कपास उपयोग करें। गहरी जुताई। 4-5 सिंचाई पर्याप्त।'},
    'sugarcane'  : {'name_hi':'गन्ना',      'emoji':'🎋','season':'Year-round',
                    'season_hi':'पूरे साल','duration':'12–18 months',
                    'water':'Very High','profit':'⭐⭐⭐⭐',
                    'states':'UP, Maharashtra, Karnataka, Tamil Nadu',
                    'msp':'₹340/quintal',
                    'tips':'Plant setts with 3 buds. Ratoon crop saves 30% cost.',
                    'tips_hi':'3 कली वाले टुकड़े लगाएं। रैटून से 30% लागत बचत।'},
    'jute'       : {'name_hi':'जूट',        'emoji':'🪢','season':'Kharif (Mar–Jun)',
                    'season_hi':'खरीफ (मार्च–जून)','duration':'100–120 days',
                    'water':'High','profit':'⭐⭐⭐',
                    'states':'West Bengal, Bihar, Assam, Odisha',
                    'msp':'₹5,050/quintal',
                    'tips':'Requires humid climate. Water retting for fiber extraction.',
                    'tips_hi':'नम जलवायु जरूरी। रेशे के लिए पानी में रेटिंग।'},
    'chickpea'   : {'name_hi':'चना',        'emoji':'🫘','season':'Rabi (Oct–Mar)',
                    'season_hi':'रबी (अक्टूबर–मार्च)','duration':'90–120 days',
                    'water':'Low','profit':'⭐⭐⭐⭐',
                    'states':'MP, Rajasthan, Maharashtra, UP',
                    'msp':'₹5,440/quintal',
                    'tips':'Drought tolerant. Fixes atmospheric nitrogen naturally.',
                    'tips_hi':'सूखा सहिष्णु। प्राकृतिक नाइट्रोजन स्थिरीकरण।'},
    'lentil'     : {'name_hi':'मसूर',       'emoji':'🫘','season':'Rabi (Oct–Mar)',
                    'season_hi':'रबी (अक्टूबर–मार्च)','duration':'100–120 days',
                    'water':'Low','profit':'⭐⭐⭐',
                    'states':'MP, UP, Bihar, Rajasthan',
                    'msp':'₹6,425/quintal',
                    'tips':'Cool dry climate. Avoid waterlogging. High protein content.',
                    'tips_hi':'ठंडी शुष्क जलवायु। जलभराव से बचें।'},
    'mungbean'   : {'name_hi':'मूंग',       'emoji':'🫘','season':'Kharif (Jun–Sep)',
                    'season_hi':'खरीफ (जून–सितंबर)','duration':'60–90 days',
                    'water':'Low','profit':'⭐⭐⭐',
                    'states':'Rajasthan, MP, Maharashtra, UP',
                    'msp':'₹8,682/quintal',
                    'tips':'Short duration. Good catch crop. Improves soil health.',
                    'tips_hi':'अल्पकालिक। पकड़ फसल। मिट्टी स्वास्थ्य सुधारती है।'},
    'blackgram'  : {'name_hi':'उड़द',       'emoji':'🫘','season':'Kharif & Rabi',
                    'season_hi':'खरीफ और रबी','duration':'70–90 days',
                    'water':'Low–Medium','profit':'⭐⭐⭐',
                    'states':'MP, UP, Andhra Pradesh, Tamil Nadu',
                    'msp':'₹6,950/quintal',
                    'tips':'Tolerates drought. Nitrogen fixing. Good for intercropping.',
                    'tips_hi':'सूखा सहिष्णु। नाइट्रोजन स्थिरीकरण। अंतर-फसल के लिए अच्छा।'},
    'mothbeans'  : {'name_hi':'मोठ',        'emoji':'🫘','season':'Kharif',
                    'season_hi':'खरीफ','duration':'75–90 days',
                    'water':'Very Low','profit':'⭐⭐',
                    'states':'Rajasthan, Gujarat, MP',
                    'msp':'₹7,000/quintal',
                    'tips':'Highly drought tolerant. Sandy soil. Arid regions.',
                    'tips_hi':'अत्यधिक सूखा सहिष्णु। बलुई मिट्टी।'},
    'pigeonpeas' : {'name_hi':'अरहर',       'emoji':'🫘','season':'Kharif (Jun–Jan)',
                    'season_hi':'खरीफ (जून–जनवरी)','duration':'150–180 days',
                    'water':'Low–Medium','profit':'⭐⭐⭐⭐',
                    'states':'Maharashtra, UP, MP, Karnataka',
                    'msp':'₹7,000/quintal',
                    'tips':'Deep taproot. Drought resistant. Intercrop with sorghum.',
                    'tips_hi':'गहरी जड़। सूखा प्रतिरोधी। ज्वार के साथ अंतर-फसल।'},
    'kidneybeans': {'name_hi':'राजमा',      'emoji':'🫘','season':'Kharif & Rabi',
                    'season_hi':'खरीफ और रबी','duration':'90–120 days',
                    'water':'Medium','profit':'⭐⭐⭐⭐',
                    'states':'HP, J&K, Uttarakhand, UP hills',
                    'msp':'₹6,000/quintal',
                    'tips':'Cool climate. Well-drained loamy soil. High protein.',
                    'tips_hi':'ठंडी जलवायु। दोमट मिट्टी। उच्च प्रोटीन।'},
    'banana'     : {'name_hi':'केला',       'emoji':'🍌','season':'Year-round',
                    'season_hi':'पूरे साल','duration':'10–15 months',
                    'water':'High','profit':'⭐⭐⭐⭐⭐',
                    'states':'Tamil Nadu, Maharashtra, Gujarat, AP',
                    'msp':'Market price',
                    'tips':'Plant suckers. Remove side shoots. 8-10 irrigations/month.',
                    'tips_hi':'सकर लगाएं। साइड शूट हटाएं। महीने में 8-10 सिंचाई।'},
    'mango'      : {'name_hi':'आम',         'emoji':'🥭','season':'Harvest: Apr–Jun',
                    'season_hi':'फसल: अप्रैल–जून','duration':'Perennial',
                    'water':'Low–Medium','profit':'⭐⭐⭐⭐⭐',
                    'states':'UP, Andhra Pradesh, Maharashtra, Bihar',
                    'msp':'Market price',
                    'tips':'10x10m spacing. Prune after harvest. Needs dry flowering season.',
                    'tips_hi':'10x10 मीटर दूरी। फसल के बाद छंटाई। फूल आने पर शुष्क मौसम चाहिए।'},
    'grapes'     : {'name_hi':'अंगूर',      'emoji':'🍇','season':'Harvest: Feb–May',
                    'season_hi':'फसल: फरवरी–मई','duration':'Perennial',
                    'water':'Medium','profit':'⭐⭐⭐⭐⭐',
                    'states':'Maharashtra, Karnataka, AP, TN',
                    'msp':'Market price',
                    'tips':'Trellis system. Prune twice yearly. Drip irrigation recommended.',
                    'tips_hi':'ट्रेलिस सिस्टम। साल में दो बार छंटाई। ड्रिप सिंचाई।'},
    'watermelon' : {'name_hi':'तरबूज',      'emoji':'🍉','season':'Summer (Feb–Jun)',
                    'season_hi':'गर्मी (फरवरी–जून)','duration':'70–90 days',
                    'water':'Medium','profit':'⭐⭐⭐⭐',
                    'states':'UP, Karnataka, Tamil Nadu, Rajasthan',
                    'msp':'Market price',
                    'tips':'Sandy loam ideal. Drip irrigation. High demand in summer.',
                    'tips_hi':'बलुई दोमट मिट्टी। ड्रिप सिंचाई। गर्मियों में उच्च मांग।'},
    'muskmelon'  : {'name_hi':'खरबूजा',     'emoji':'🍈','season':'Summer (Feb–May)',
                    'season_hi':'गर्मी (फरवरी–मई)','duration':'70–90 days',
                    'water':'Medium','profit':'⭐⭐⭐',
                    'states':'UP, Rajasthan, Punjab, Haryana',
                    'msp':'Market price',
                    'tips':'Sandy soil. 2x1m spacing. Stop irrigation before harvest.',
                    'tips_hi':'बलुई मिट्टी। 2x1 मीटर दूरी। फसल से पहले सिंचाई बंद करें।'},
    'apple'      : {'name_hi':'सेब',        'emoji':'🍎','season':'Harvest: Aug–Oct',
                    'season_hi':'फसल: अगस्त–अक्टूबर','duration':'Perennial (5+ yrs)',
                    'water':'Medium','profit':'⭐⭐⭐⭐⭐',
                    'states':'HP, J&K, Uttarakhand',
                    'msp':'Market price',
                    'tips':'Needs chilling hours. Annual pruning. High returns long-term.',
                    'tips_hi':'ठंड के घंटे जरूरी। सालाना छंटाई। लंबे समय तक उच्च आय।'},
    'orange'     : {'name_hi':'संतरा',      'emoji':'🍊','season':'Harvest: Nov–Feb',
                    'season_hi':'फसल: नवंबर–फरवरी','duration':'Perennial',
                    'water':'Medium','profit':'⭐⭐⭐⭐',
                    'states':'Maharashtra, MP, Rajasthan, Punjab',
                    'msp':'Market price',
                    'tips':'6x6m spacing. Drip irrigation best. High vitamin C demand.',
                    'tips_hi':'6x6 मीटर दूरी। ड्रिप सिंचाई। उच्च विटामिन C मांग।'},
    'papaya'     : {'name_hi':'पपीता',      'emoji':'🧡','season':'Year-round',
                    'season_hi':'पूरे साल','duration':'9–12 months',
                    'water':'Medium','profit':'⭐⭐⭐⭐',
                    'states':'AP, Tamil Nadu, Karnataka, Gujarat',
                    'msp':'Market price',
                    'tips':'Fast growing. Avoid waterlogging. 3x3m spacing.',
                    'tips_hi':'तेजी से बढ़ता है। जलभराव से बचें। 3x3 मीटर दूरी।'},
    'coconut'    : {'name_hi':'नारियल',     'emoji':'🥥','season':'Year-round (perennial)',
                    'season_hi':'पूरे साल (बारहमासी)','duration':'Perennial (7–10 yrs)',
                    'water':'High','profit':'⭐⭐⭐⭐',
                    'states':'Kerala, Tamil Nadu, Karnataka, AP',
                    'msp':'Market price',
                    'tips':'Coastal areas best. 7.5x7.5m spacing. Intercrop with banana.',
                    'tips_hi':'तटीय क्षेत्र सर्वोत्तम। 7.5x7.5 मीटर दूरी।'},
    'pomegranate': {'name_hi':'अनार',       'emoji':'🍎','season':'Harvest: Aug–Feb',
                    'season_hi':'फसल: अगस्त–फरवरी','duration':'Perennial',
                    'water':'Low–Medium','profit':'⭐⭐⭐⭐⭐',
                    'states':'Maharashtra, Gujarat, Rajasthan, Karnataka',
                    'msp':'Market price',
                    'tips':'Drought tolerant once established. Drip irrigation ideal.',
                    'tips_hi':'स्थापित होने के बाद सूखा सहिष्णु। ड्रिप सिंचाई आदर्श।'},
}


def suggest_crop():
    if model is None:
        return jsonify({
            'error': 'ML model not loaded. Please run: python ml/train_model.py'
        }), 500

    try:
        data = request.get_json()

        N           = float(data.get('nitrogen',    0))
        P           = float(data.get('phosphorus',  0))
        K           = float(data.get('potassium',   0))
        temperature = float(data.get('temperature', 25))
        humidity    = float(data.get('humidity',    70))
        ph          = float(data.get('ph',          6.5))
        rainfall    = float(data.get('rainfall',    100))

        # Validate
        errors = []
        if not 0  <= N           <= 200: errors.append('Nitrogen: 0–200 kg/ha')
        if not 0  <= P           <= 200: errors.append('Phosphorus: 0–200 kg/ha')
        if not 0  <= K           <= 200: errors.append('Potassium: 0–200 kg/ha')
        if not 0  <= temperature <= 50:  errors.append('Temperature: 0–50°C')
        if not 0  <= humidity    <= 100: errors.append('Humidity: 0–100%')
        if not 0  <= ph          <= 14:  errors.append('pH: 0–14')
        if not 0  <= rainfall    <= 500: errors.append('Rainfall: 0–500 mm')

        if errors:
            return jsonify({'error': 'Invalid values — ' + ', '.join(errors)}), 400

        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])

        # Get top 3 with probabilities
        probs    = model.predict_proba(features)[0]
        top3_idx = np.argsort(probs)[::-1][:3]
        classes  = model.classes_

        results = []
        for i, idx in enumerate(top3_idx):
            crop = classes[idx]
            info = CROP_INFO.get(crop, {})
            results.append({
                'rank'      : i + 1,
                'crop'      : crop,
                'crop_hi'   : info.get('name_hi',   crop),
                'emoji'     : info.get('emoji',     '🌱'),
                'confidence': round(float(probs[idx]) * 100, 1),
                'season'    : info.get('season',    'N/A'),
                'season_hi' : info.get('season_hi', 'N/A'),
                'duration'  : info.get('duration',  'N/A'),
                'water'     : info.get('water',     'N/A'),
                'profit'    : info.get('profit',    '⭐⭐⭐'),
                'states'    : info.get('states',    'N/A'),
                'tips'      : info.get('tips',      ''),
                'tips_hi'   : info.get('tips_hi',   ''),
                'msp'       : info.get('msp',       'N/A'),
            })

        return jsonify({
            'success'      : True,
            'top_crops'    : results,
            'soil_analysis': analyze_soil(N, P, K, ph, rainfall, temperature),
            'model_accuracy': stats['accuracy'] if stats else 'N/A',
        })

    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500


def analyze_soil(N, P, K, ph, rainfall, temperature):
    result = []

    # Nitrogen
    if N < 30:
        result.append({'type':'warning','icon':'🔴','label':'Nitrogen Low','label_hi':'नाइट्रोजन कम',
            'msg':'Add urea or compost to boost nitrogen levels.',
            'msg_hi':'नाइट्रोजन बढ़ाने के लिए यूरिया या खाद डालें।'})
    elif N > 120:
        result.append({'type':'warning','icon':'🟡','label':'Nitrogen High','label_hi':'नाइट्रोजन अधिक',
            'msg':'Excess nitrogen causes leaf burn. Reduce fertilizer.',
            'msg_hi':'अधिक नाइट्रोजन से पत्तियां जलती हैं। उर्वरक कम करें।'})
    else:
        result.append({'type':'good','icon':'🟢','label':'Nitrogen Optimal','label_hi':'नाइट्रोजन उचित',
            'msg':'Nitrogen level is ideal for crop growth.',
            'msg_hi':'नाइट्रोजन स्तर फसल वृद्धि के लिए आदर्श है।'})

    # Phosphorus
    if P < 20:
        result.append({'type':'warning','icon':'🔴','label':'Phosphorus Low','label_hi':'फास्फोरस कम',
            'msg':'Apply DAP (Di-Ammonium Phosphate) fertilizer.',
            'msg_hi':'DAP उर्वरक लगाएं।'})
    elif P > 100:
        result.append({'type':'warning','icon':'🟡','label':'Phosphorus High','label_hi':'फास्फोरस अधिक',
            'msg':'High P may reduce zinc and iron absorption.',
            'msg_hi':'अधिक P जिंक और आयरन अवशोषण कम करता है।'})
    else:
        result.append({'type':'good','icon':'🟢','label':'Phosphorus Optimal','label_hi':'फास्फोरस उचित',
            'msg':'Phosphorus level is good for root development.',
            'msg_hi':'जड़ विकास के लिए फास्फोरस स्तर अच्छा है।'})

    # Potassium
    if K < 15:
        result.append({'type':'warning','icon':'🔴','label':'Potassium Low','label_hi':'पोटाश कम',
            'msg':'Apply MOP (Muriate of Potash) to improve K levels.',
            'msg_hi':'पोटाश का स्तर बढ़ाने के लिए MOP लगाएं।'})
    elif K > 150:
        result.append({'type':'warning','icon':'🟡','label':'Potassium High','label_hi':'पोटाश अधिक',
            'msg':'Very high K can reduce magnesium uptake.',
            'msg_hi':'अधिक पोटाश मैग्नीशियम अवशोषण कम करता है।'})
    else:
        result.append({'type':'good','icon':'🟢','label':'Potassium Optimal','label_hi':'पोटाश उचित',
            'msg':'Potassium level supports good crop immunity.',
            'msg_hi':'पोटाश स्तर फसल की रोग प्रतिरोधक क्षमता बढ़ाता है।'})

    # pH
    if ph < 5.5:
        result.append({'type':'warning','icon':'🔴','label':'Soil Too Acidic','label_hi':'मिट्टी बहुत अम्लीय',
            'msg':'Apply agricultural lime (CaCO3) to raise pH to 6.0–7.0.',
            'msg_hi':'pH 6.0–7.0 करने के लिए चूना पत्थर डालें।'})
    elif ph > 8.0:
        result.append({'type':'warning','icon':'🟡','label':'Soil Too Alkaline','label_hi':'मिट्टी क्षारीय',
            'msg':'Apply gypsum or elemental sulfur to lower pH.',
            'msg_hi':'pH कम करने के लिए जिप्सम या सल्फर डालें।'})
    else:
        result.append({'type':'good','icon':'🟢','label':'pH Optimal','label_hi':'pH उचित',
            'msg':'Soil pH is in ideal range (5.5–8.0).',
            'msg_hi':'मिट्टी pH आदर्श सीमा (5.5–8.0) में है।'})

    # Rainfall
    if rainfall < 50:
        result.append({'type':'warning','icon':'💧','label':'Low Rainfall','label_hi':'कम वर्षा',
            'msg':'Irrigation essential. Drip system saves 40% water.',
            'msg_hi':'सिंचाई जरूरी। ड्रिप सिस्टम 40% पानी बचाता है।'})
    elif rainfall > 300:
        result.append({'type':'warning','icon':'🌧️','label':'High Rainfall','label_hi':'अधिक वर्षा',
            'msg':'Ensure drainage channels to prevent waterlogging.',
            'msg_hi':'जलभराव रोकने के लिए नालियां बनाएं।'})
    else:
        result.append({'type':'good','icon':'🟢','label':'Rainfall Adequate','label_hi':'वर्षा पर्याप्त',
            'msg':'Rainfall is suitable for most crops.',
            'msg_hi':'वर्षा अधिकांश फसलों के लिए उपयुक्त है।'})

    # Temperature
    if temperature > 40:
        result.append({'type':'warning','icon':'🔥','label':'Too Hot','label_hi':'अत्यधिक गर्मी',
            'msg':'Use shade nets. Irrigate in early morning or evening.',
            'msg_hi':'शेड नेट उपयोग करें। सुबह या शाम सिंचाई करें।'})
    elif temperature < 10:
        result.append({'type':'warning','icon':'❄️','label':'Too Cold','label_hi':'अत्यधिक ठंड',
            'msg':'Protect crops from frost using covers or smoke.',
            'msg_hi':'धुएं या ढकने से पाले से फसल बचाएं।'})
    else:
        result.append({'type':'good','icon':'🌡️','label':'Temperature OK','label_hi':'तापमान उचित',
            'msg':'Temperature is suitable for crop growth.',
            'msg_hi':'तापमान फसल वृद्धि के लिए उपयुक्त है।'})

    return result