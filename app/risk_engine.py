import pandas as pd
import joblib
import json
import os

MODEL_DIR = r'd:\VECTOR\model'
MODEL_PATH = os.path.join(MODEL_DIR, 'risk_model.pkl')
FEATURE_COLS_PATH = os.path.join(MODEL_DIR, 'feature_columns.json')

class RiskEngine:
    # Default risk thresholds
    DEFAULT_THRESHOLDS = {
        'critical': 0.8,
        'high': 0.6,
        'medium': 0.4
    }

    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        self.load_model()

    def load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            with open(FEATURE_COLS_PATH, 'r') as f:
                self.feature_columns = json.load(f)
            print("Model and feature columns loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

    def set_thresholds(self, critical=None, high=None, medium=None):
        """Update risk classification thresholds at runtime."""
        if critical is not None:
            self.thresholds['critical'] = critical
        if high is not None:
            self.thresholds['high'] = high
        if medium is not None:
            self.thresholds['medium'] = medium

    def preprocess_data(self, df):
        """Applies the same feature engineering as in training."""
        # 1. Handle missing values
        df_processed = df.copy()
        df_processed.fillna(-1, inplace=True)
        
        # 2. Calculate Risk Acceleration
        if all(col in df_processed.columns for col in ['velocity_6h', 'velocity_24h', 'velocity_4w']):
            df_processed['accel_short_term'] = (df_processed['velocity_6h'] - df_processed['velocity_24h']) / (df_processed['velocity_24h'] + 1)
            df_processed['accel_long_term'] = (df_processed['velocity_24h'] - df_processed['velocity_4w']) / (df_processed['velocity_4w'] + 1)
        else:
            df_processed['accel_short_term'] = 0
            df_processed['accel_long_term'] = 0

        # 3. Categorical encoding
        categorical_cols = ['payment_type', 'employment_status', 'housing_status', 'device_os', 'source']
        categorical_cols = [col for col in categorical_cols if col in df_processed.columns]
        
        df_processed = pd.get_dummies(df_processed, columns=categorical_cols, drop_first=True)

        # 4. Ensure all training features are present, fill missing with 0
        for col in self.feature_columns:
            if col not in df_processed.columns:
                df_processed[col] = 0
                
        # 5. Order columns exactly as expected by the model
        return df_processed[self.feature_columns]

    def get_top_risk_drivers(self, row, feature_names):
        """Identify which features are contributing most to the risk score."""
        # For XGBoost, this is complex per-instance, but we can approximate 
        # using global feature importances combined with the local values.
        # A simpler robust approach for demo: sort features by their normalized deviation from mean
        # Since we don't have means saved, we will just return a placeholder or use a simple heuristic
        
        # Simple heuristic: if velocity is high, it's a driver
        drivers = []
        if 'velocity_6h' in row and row['velocity_6h'] > 5000:
            drivers.append("High 6h Velocity")
        if 'device_fraud_count' in row and row['device_fraud_count'] > 0:
            drivers.append("Device Fraud History")
        if 'credit_risk_score' in row and row['credit_risk_score'] < 100:
            drivers.append("Low Credit Score")
            
        if not drivers:
            drivers.append("Multiple minor factors")
            
        return ", ".join(drivers)

    def get_risk_category(self, score):
        if score >= self.thresholds['critical']:
            return "Critical"
        if score >= self.thresholds['high']:
            return "High"
        if score >= self.thresholds['medium']:
            return "Medium"
        return "Low"

    def predict(self, df):
        if self.model is None or self.feature_columns is None:
            raise ValueError("Model not loaded. Please train the model first.")

        # Keep original data for results
        results_df = df.copy()
        
        # Preprocess
        X = self.preprocess_data(df)
        
        # Predict probabilities
        probabilities = self.model.predict_proba(X)[:, 1] # Probability of class 1 (fraud)
        
        results_df['Risk Score'] = probabilities
        results_df['Risk Category'] = results_df['Risk Score'].apply(self.get_risk_category)
        
        # Get risk drivers
        drivers_list = []
        for i, row in X.iterrows():
            drivers_list.append(self.get_top_risk_drivers(row, self.feature_columns))
            
        results_df['Top Risk Drivers'] = drivers_list
        
        return results_df
