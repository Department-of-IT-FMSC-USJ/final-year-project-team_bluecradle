import os
import numpy as np
import joblib
import tensorflow as tf
from django.conf import settings

# ── Path helpers ────────────────────────────────────────────────
MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml_module', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'bluecradle_lstm_v1.keras')
SCALER_PATH = os.path.join(MODEL_DIR, 'bluecradle_scaler.pkl')
IMPUTER_PATH = os.path.join(MODEL_DIR, 'bluecradle_imputer.pkl')

# ── Feature order — must match training exactly ──────────────────
SEQUENCE_FEATURES = [
    'age_in_days', 'weight_kg', 'height_cm', 'MUAC_mm',
    'days_since_last_visit', 'weight_delta_kg', 'WHZ', 'whz_velocity'
]
STATIC_FEATURES = [
    'sex', 'birth_weight_kg', 'birth_length_cm'
]

RISK_MAP = {0: 'NORMAL', 1: 'MAM', 2: 'SAM'}

# ── Lazy-loaded singletons ───────────────────────────────────────
_model   = None
_scaler  = None
_imputer = None


def _load_artifacts():
    global _model, _scaler, _imputer
    if _model is None:
        _model   = tf.keras.models.load_model(MODEL_PATH)
        _scaler  = joblib.load(SCALER_PATH)
        _imputer = joblib.load(IMPUTER_PATH)


def assemble_feature_array(infant, growth_records):
    """
    Builds the sequence + static arrays the LSTM expects.
    Sequence: (n_visits, 8) — one row per visit
    Static:   (1, 3)        — birth stats, constant across visits
    """
    static = np.array([[
        1 if infant.sex == 'M' else 0,
        float(infant.birth_weight_kg),
        float(infant.birth_length_cm),
    ]], dtype=np.float32)

    rows = []
    for gr in growth_records:
        rows.append([
            float(gr.age_in_days),
            float(gr.weight_kg),
            float(gr.height_cm),
            float(gr.muac_mm)          if gr.muac_mm          is not None else np.nan,
            float(gr.days_since_last_visit) if gr.days_since_last_visit is not None else 0.0,
            float(gr.weight_delta_kg)  if gr.weight_delta_kg  is not None else 0.0,
            float(gr.whz)              if gr.whz              is not None else np.nan,
            float(gr.whz_velocity)     if gr.whz_velocity     is not None else 0.0,
        ])

    sequence = np.array(rows, dtype=np.float32)
    return sequence, static


def run_inference(infant, growth_records):
    """
    Runs the LSTM inference pipeline.
    Returns a dict with risk_level, confidence_score, and all three probabilities.
    """
    _load_artifacts()

    sequence, static = assemble_feature_array(infant, growth_records)

    n_visits, n_features = sequence.shape

    # ── Impute missing values ────────────────────────────────────
    seq_flat = sequence.reshape(-1, n_features)
    seq_flat = _imputer.transform(seq_flat)

    # ── Scale ────────────────────────────────────────────────────
    seq_flat = _scaler.transform(seq_flat)

    # ── Pad or truncate to exactly 6 timesteps ───────────────────
    MAX_TIMESTEPS = 6
    seq_scaled = seq_flat.reshape(n_visits, n_features)

    if n_visits < MAX_TIMESTEPS:
        # Pad with -999.0 (same masking value used during training)
        padding = np.full((MAX_TIMESTEPS - n_visits, n_features), -999.0, dtype=np.float32)
        seq_scaled = np.vstack([seq_scaled, padding])
    elif n_visits > MAX_TIMESTEPS:
        # Take the most recent 6 visits
        seq_scaled = seq_scaled[-MAX_TIMESTEPS:]

    sequence = seq_scaled.reshape(1, MAX_TIMESTEPS, n_features)

    # ── Run prediction ───────────────────────────────────────────
    probs = _model.predict([sequence, static], verbose=0)[0]

    # LSTM returns (n_visits, 3) — take the last timestep
    if probs.ndim == 2:
        probs = probs[-1]

    predicted_class = int(np.argmax(probs))
    risk_level      = RISK_MAP[predicted_class]
    confidence      = float(probs[predicted_class])

    return {
        'risk_level':       risk_level,
        'confidence_score': round(confidence, 4),
        'prob_normal':      round(float(probs[0]), 4),
        'prob_mam':         round(float(probs[1]), 4),
        'prob_sam':         round(float(probs[2]), 4),
    }