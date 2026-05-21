import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

# ── Load real dataset ─────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), 'Crop_recommendation.csv')

if not os.path.exists(CSV_PATH):
    print("❌ ERROR: Crop_recommendation.csv not found in ml/ folder!")
    print("👉 Download from: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset")
    exit()

df = pd.read_csv(CSV_PATH)
print(f"✅ Dataset loaded: {len(df)} rows")
print(f"✅ Columns: {list(df.columns)}")
print(f"✅ Crops: {sorted(df['label'].unique())}")
print(f"✅ Crop counts:\n{df['label'].value_counts()}")

# ── Features & Target ─────────────────────────────
X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

# ── Train/Test Split ──────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n✅ Training samples : {len(X_train)}")
print(f"✅ Testing  samples : {len(X_test)}")

# ── Train Ensemble Model ──────────────────────────
rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42,
    n_jobs=-1
)

gb = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    random_state=42
)

# Voting classifier for best accuracy
model = VotingClassifier(
    estimators=[('rf', rf), ('gb', gb)],
    voting='soft'
)

print("\n⏳ Training model (may take 1-2 minutes)...")
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────
y_pred   = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅ Model Accuracy: {accuracy * 100:.2f}%")
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

# ── Save Model + Scaler ───────────────────────────
os.makedirs('ml', exist_ok=True)

with open('ml/crop_model.pkl', 'wb') as f:
    pickle.dump(model, f)

# Save feature ranges for validation
feature_stats = {
    'N'          : {'min': float(X['N'].min()),           'max': float(X['N'].max()),
                    'mean': float(X['N'].mean())},
    'P'          : {'min': float(X['P'].min()),           'max': float(X['P'].max()),
                    'mean': float(X['P'].mean())},
    'K'          : {'min': float(X['K'].min()),           'max': float(X['K'].max()),
                    'mean': float(X['K'].mean())},
    'temperature': {'min': float(X['temperature'].min()), 'max': float(X['temperature'].max()),
                    'mean': float(X['temperature'].mean())},
    'humidity'   : {'min': float(X['humidity'].min()),    'max': float(X['humidity'].max()),
                    'mean': float(X['humidity'].mean())},
    'ph'         : {'min': float(X['ph'].min()),          'max': float(X['ph'].max()),
                    'mean': float(X['ph'].mean())},
    'rainfall'   : {'min': float(X['rainfall'].min()),    'max': float(X['rainfall'].max()),
                    'mean': float(X['rainfall'].mean())},
    'crops'      : sorted(y.unique().tolist()),
    'accuracy'   : round(accuracy * 100, 2)
}

with open('ml/feature_stats.pkl', 'wb') as f:
    pickle.dump(feature_stats, f)

print(f"\n✅ Model saved to ml/crop_model.pkl")
print(f"✅ Stats saved to ml/feature_stats.pkl")
print(f"\n🌱 Supported crops ({len(feature_stats['crops'])}):")
for i, crop in enumerate(feature_stats['crops'], 1):
    print(f"   {i:2}. {crop}")