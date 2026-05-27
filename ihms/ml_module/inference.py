import os
import numpy as np
import pickle
import tensorflow as tf
from django.conf import settings

# ── Path helpers ────────────────────────────────────────────────
MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml_module', 'models')

MODEL_PATH   = os.path.join(MODEL_DIR, 'bluecradle_lstm_v1.keras')
SCALER_PATH  = os.path.join(MODEL_DIR, 'scaler.pkl')
IMPUTER_PATH = os.path.join(MODEL_DIR, 'imputer.pkl')

# ── Feature order (must match training exactly) ──────────────────
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
        with open(SCALER_PATH,  'rb') as f: _scaler  = pickle.load(f)
        with open(IMPUTER_PATH, 'rb') as f: _imputer = pickle.load(f)


def assemble_feature_array(infant, growth_records):
    """
    Builds the sequence + static arrays the LSTM expects.

    infant        — Infant model instance
    growth_records — QuerySet of GrowthRecord ordered by visit_date (all visits)
    """
    # ── Static features (one row) ────────────────────────────────
    static = np.array([[
        1 if infant.sex == 'M' else 2,
        float(infant.birth_weight_kg),
        float(infant.birth_length_cm),
    ]], dtype=np.float32)

    # ── Sequential features (one row per visit) ──────────────────
    rows = []
    for gr in growth_records:
        rows.append([
            gr.age_in_days,
            float(gr.weight_kg),
            float(gr.height_cm),
            float(gr.muac_mm) if gr.muac_mm is not None else np.nan,
            gr.days_since_last_visit if gr.days_since_last_visit is not None else 0,
            float(gr.weight_delta_kg) if gr.weight_delta_kg is not None else 0.0,
            float(gr.whz) if gr.whz is not None else np.nan,
            float(gr.whz_velocity) if gr.whz_velocity is not None else 0.0,
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

    # ── Impute then scale sequence ───────────────────────────────
    n_visits, n_features = sequence.shape
    seq_flat = sequence.reshape(-1, n_features)
    seq_flat = _imputer.transform(seq_flat)
    seq_flat = _scaler.transform(seq_flat)
    sequence = seq_flat.reshape(1, n_visits, n_features)

    # ── Run prediction ───────────────────────────────────────────
    probs = _model.predict([sequence, static], verbose=0)[0]

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