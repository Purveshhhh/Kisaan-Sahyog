import os
import numpy as np
import json
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (Dense, Dropout, BatchNormalization,
                                      GlobalAveragePooling2D)
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (ModelCheckpoint, EarlyStopping,
                                         ReduceLROnPlateau)
from tensorflow.keras.preprocessing.image import ImageDataGenerator

print(f"✅ TensorFlow version: {tf.__version__}")

# ── Config ────────────────────────────────────────
IMG_SIZE   = 224
BATCH_SIZE = 16        # reduced for low RAM
EPOCHS     = 15
BASE       = os.path.dirname(os.path.abspath(__file__))

# Try multiple possible dataset locations
POSSIBLE_PATHS = [
    os.path.join(BASE, 'PlantVillage'),
]

DATASET_DIR = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        # Check if it has subdirectories with images
        subdirs = [d for d in os.listdir(path)
                   if os.path.isdir(os.path.join(path, d))]
        if len(subdirs) > 3:
            DATASET_DIR = path
            break

if DATASET_DIR is None:
    print("❌ Dataset not found!")
    print("📂 Looked in these locations:")
    for p in POSSIBLE_PATHS:
        print(f"   {p}")
    print("\n👉 Please check your ml/ folder structure and tell me what you see.")
    exit()

print(f"✅ Dataset found: {DATASET_DIR}")

# ── List all classes ──────────────────────────────
classes = sorted([
    d for d in os.listdir(DATASET_DIR)
    if os.path.isdir(os.path.join(DATASET_DIR, d))
])

print(f"✅ Found {len(classes)} classes:")
total_images = 0
for i, c in enumerate(classes, 1):
    count = len([
        f for f in os.listdir(os.path.join(DATASET_DIR, c))
        if f.lower().endswith(('.jpg','.jpeg','.png'))
    ])
    total_images += count
    print(f"   {i:2}. {c:<50} ({count} images)")

print(f"\n✅ Total images: {total_images}")

if total_images < 100:
    print("❌ Too few images found. Check dataset path.")
    exit()

# ── Data Augmentation ─────────────────────────────
train_datagen = ImageDataGenerator(
    rescale            = 1./255,
    validation_split   = 0.2,
    rotation_range     = 25,
    width_shift_range  = 0.15,
    height_shift_range = 0.15,
    shear_range        = 0.15,
    zoom_range         = 0.15,
    horizontal_flip    = True,
    vertical_flip      = True,
    fill_mode          = 'nearest',
    brightness_range   = [0.85, 1.15],
)

val_datagen = ImageDataGenerator(
    rescale          = 1./255,
    validation_split = 0.2,
)

print("\n⏳ Loading dataset...")
train_gen = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size = (IMG_SIZE, IMG_SIZE),
    batch_size  = BATCH_SIZE,
    class_mode  = 'categorical',
    subset      = 'training',
    shuffle     = True,
)

val_gen = val_datagen.flow_from_directory(
    DATASET_DIR,
    target_size = (IMG_SIZE, IMG_SIZE),
    batch_size  = BATCH_SIZE,
    class_mode  = 'categorical',
    subset      = 'validation',
    shuffle     = False,
)

NUM_CLASSES = len(train_gen.class_indices)
print(f"✅ Training   : {train_gen.samples} images")
print(f"✅ Validation : {val_gen.samples} images")
print(f"✅ Classes    : {NUM_CLASSES}")

# ── Save class labels ─────────────────────────────
class_labels = {str(v): k for k, v in train_gen.class_indices.items()}
with open(os.path.join(BASE, 'disease_labels.json'), 'w') as f:
    json.dump(class_labels, f, indent=2)
print("✅ Labels saved to ml/disease_labels.json")

# ── Build Model ───────────────────────────────────
print("\n⏳ Building MobileNetV2 model...")

base_model = MobileNetV2(
    weights     = 'imagenet',
    include_top = False,
    input_shape = (IMG_SIZE, IMG_SIZE, 3)
)
base_model.trainable = False

model = Sequential([
    base_model,
    GlobalAveragePooling2D(),
    BatchNormalization(),
    Dense(512, activation='relu'),
    Dropout(0.4),
    Dense(256, activation='relu'),
    Dropout(0.3),
    Dense(NUM_CLASSES, activation='softmax')
])

model.compile(
    optimizer = Adam(learning_rate=0.001),
    loss      = 'categorical_crossentropy',
    metrics   = ['accuracy']
)

total_params = model.count_params()
print(f"✅ Model parameters: {total_params:,}")

# ── Callbacks ─────────────────────────────────────
checkpoint_path = os.path.join(BASE, 'disease_model_best.h5')
callbacks = [
    ModelCheckpoint(
        checkpoint_path,
        monitor        = 'val_accuracy',
        save_best_only = True,
        verbose        = 1
    ),
    EarlyStopping(
        monitor              = 'val_accuracy',
        patience             = 4,
        restore_best_weights = True,
        verbose              = 1
    ),
    ReduceLROnPlateau(
        monitor  = 'val_loss',
        factor   = 0.3,
        patience = 2,
        min_lr   = 1e-7,
        verbose  = 1
    ),
]

# ── Phase 1: Train top layers only ───────────────
print("\n" + "="*50)
print("PHASE 1: Training top layers (frozen base)")
print("="*50)

history1 = model.fit(
    train_gen,
    epochs          = 5,
    validation_data = val_gen,
    callbacks       = callbacks,
    verbose         = 1
)

# ── Phase 2: Fine-tune ────────────────────────────
print("\n" + "="*50)
print("PHASE 2: Fine-tuning last 30 layers")
print("="*50)

base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer = Adam(learning_rate=0.0001),
    loss      = 'categorical_crossentropy',
    metrics   = ['accuracy']
)

history2 = model.fit(
    train_gen,
    epochs          = EPOCHS,
    initial_epoch   = 5,
    validation_data = val_gen,
    callbacks       = callbacks,
    verbose         = 1
)

# ── Evaluate ──────────────────────────────────────
print("\n⏳ Final evaluation...")
val_loss, val_acc = model.evaluate(val_gen, verbose=1)
print(f"\n{'='*50}")
print(f"✅ Final Accuracy : {val_acc  * 100:.2f}%")
print(f"✅ Final Loss     : {val_loss:.4f}")
print(f"{'='*50}")

# ── Save final model ──────────────────────────────
final_path = os.path.join(BASE, 'disease_model.h5')
model.save(final_path)
print(f"✅ Final model saved: {final_path}")

# Save accuracy info
stats = {
    'accuracy'   : round(val_acc * 100, 2),
    'num_classes': NUM_CLASSES,
    'img_size'   : IMG_SIZE,
    'classes'    : list(train_gen.class_indices.keys()),
}
with open(os.path.join(BASE, 'disease_model_stats.json'), 'w') as f:
    json.dump(stats, f, indent=2)
print(f"✅ Stats saved: ml/disease_model_stats.json")
print(f"\n🎉 Training complete! Model accuracy: {val_acc*100:.2f}%")
print(f"🌿 Your model can detect {NUM_CLASSES} plant diseases!")