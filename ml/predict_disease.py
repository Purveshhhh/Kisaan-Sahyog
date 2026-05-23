import numpy as np
import json
import os
from PIL import Image
import io

_model       = None
_labels      = None
_model_stats = None

BASE = os.path.dirname(os.path.abspath(__file__))

def load_model():
    global _model, _labels, _model_stats

    if _model is not None:
        return _model, _labels, _model_stats

    import tensorflow as tf

    model_path = os.path.join(BASE, 'disease_model.h5')
    label_path = os.path.join(BASE, 'disease_labels.json')
    stats_path = os.path.join(BASE, 'disease_model_stats.json')

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            "disease_model.h5 not found. Run: python ml/train_disease_model.py"
        )

    print("⏳ Loading disease model...")
    _model = tf.keras.models.load_model(model_path)

    with open(label_path) as f:
        _labels = json.load(f)

    if os.path.exists(stats_path):
        with open(stats_path) as f:
            _model_stats = json.load(f)

    print(f"✅ Disease model loaded. Classes: {len(_labels)}")
    return _model, _labels, _model_stats


def preprocess_image(img_bytes, img_size=224):
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    img = img.resize((img_size, img_size), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def parse_class_label(label):
    """Parse class label like Tomato___Early_blight into plant + condition"""
    # Handle both ___ and __ separators
    if '___' in label:
        parts = label.split('___', 1)
    elif '__' in label:
        parts = label.split('__', 1)
    else:
        parts = label.split('_', 1)

    plant     = parts[0].replace('_', ' ').strip()
    condition = parts[1].replace('_', ' ').strip() if len(parts) > 1 else 'Unknown'
    is_healthy = 'healthy' in condition.lower()

    return plant, condition, is_healthy


def predict_disease(img_bytes, top_k=3):
    model, labels, stats = load_model()

    img_size = stats.get('img_size', 224) if stats else 224
    img      = preprocess_image(img_bytes, img_size)
    preds    = model.predict(img, verbose=0)[0]

    top_idx = np.argsort(preds)[::-1][:top_k]
    results = []

    for idx in top_idx:
        label               = labels[str(idx)]
        plant, condition, is_healthy = parse_class_label(label)

        results.append({
            'label'     : label,
            'plant'     : plant,
            'condition' : condition,
            'is_healthy': is_healthy,
            'confidence': round(float(preds[idx]) * 100, 2),
        })

    return results