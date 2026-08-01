"""
Machine Learning Predictor with Continuous Self-Learning Integration
======================================================================
Trains ML models on historical technical indicators and incorporates
feedback learned from actual past trade outcome data.
"""

import os
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from ai.technical_analysis import TechnicalAnalysisEngine

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
LEARNING_DIR = os.path.join(os.path.dirname(__file__), "learning_data")
os.makedirs(MODEL_DIR, exist_ok=True)

class MLStockPredictor:
    def __init__(self):
        self.models = {}
        self.self_learned_model = None
        self._load_self_learned_model()

    def _load_self_learned_model(self):
        learned_path = os.path.join(LEARNING_DIR, "self_learned_model.pkl")
        if os.path.exists(learned_path):
            try:
                self.self_learned_model = joblib.load(learned_path)
                logger.info("🧠 Loaded self-learned outcome model into ML ensemble.")
            except Exception as e:
                logger.error(f"Failed loading self-learned model: {e}")

    def prepare_features(self, df: pd.DataFrame) -> tuple:
        if df.empty or len(df) < 60:
            return pd.DataFrame(), pd.Series(dtype=int)

        data = TechnicalAnalysisEngine.compute_indicators(df)
        data['Target'] = (data['Close'].shift(-1) > data['Close'] * 1.003).astype(int)

        feature_cols = [
            'Return_1d', 'Return_5d', 'Return_20d',
            'RSI', 'MACD', 'MACD_Hist', 'BB_Pct', 'ATR'
        ]

        data = data.dropna(subset=feature_cols + ['Target'])
        X = data[feature_cols]
        y = data['Target']

        return X, y

    def train_model(self, symbol: str, df: pd.DataFrame) -> bool:
        X, y = self.prepare_features(df)
        if len(X) < 100:
            return False

        try:
            model = GradientBoostingClassifier(n_estimators=120, learning_rate=0.04, max_depth=4, random_state=42)
            model.fit(X, y)
            
            model_path = os.path.join(MODEL_DIR, f"{symbol}_model.pkl")
            joblib.dump(model, model_path)
            self.models[symbol] = model
            return True
        except Exception as e:
            logger.error(f"Error training ML model for {symbol}: {e}")
            return False

    def predict(self, symbol: str, df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 30:
            return {"direction": "FLAT", "confidence": 0.50, "score": 50, "feature_vector": {}}

        model_path = os.path.join(MODEL_DIR, f"{symbol}_model.pkl")
        model = self.models.get(symbol)
        
        if model is None and os.path.exists(model_path):
            try:
                model = joblib.load(model_path)
                self.models[symbol] = model
            except Exception:
                pass

        if model is None:
            self.train_model(symbol, df)
            model = self.models.get(symbol)

        data = TechnicalAnalysisEngine.compute_indicators(df)
        feature_cols = [
            'Return_1d', 'Return_5d', 'Return_20d',
            'RSI', 'MACD', 'MACD_Hist', 'BB_Pct', 'ATR'
        ]
        latest_X = data[feature_cols].iloc[[-1]].fillna(0)
        feature_vector = latest_X.iloc[0].to_dict()

        base_prob = 0.50
        if model is not None:
            try:
                probs = model.predict_proba(latest_X)[0]
                base_prob = float(probs[1]) if len(probs) > 1 else 0.50
            except Exception:
                base_prob = 0.50

        # Self-learning model ensemble adjustment
        self._load_self_learned_model()
        if self.self_learned_model is not None:
            try:
                learned_probs = self.self_learned_model.predict_proba(latest_X)[0]
                learned_win_prob = float(learned_probs[1]) if len(learned_probs) > 1 else 0.50
                # Ensemble: 70% Base Historical Model + 30% Self-Learned Outcome Model
                final_prob = (base_prob * 0.70) + (learned_win_prob * 0.30)
            except Exception:
                final_prob = base_prob
        else:
            final_prob = base_prob

        direction = "UP" if final_prob >= 0.55 else ("DOWN" if final_prob <= 0.45 else "FLAT")
        confidence = max(final_prob, 1 - final_prob)
        score = round(final_prob * 100, 2)

        return {
            "direction": direction,
            "confidence": round(float(confidence), 2),
            "prob_up": round(final_prob, 2),
            "score": score,
            "feature_vector": feature_vector
        }
