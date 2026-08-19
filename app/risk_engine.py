import pandas as pd
import joblib
import json
import os
import numpy as np

try:
    import shap
except ImportError:
    shap = None
    print("WARNING: shap not installed. SHAP-based explainability will be unavailable. Install with: pip install shap")

MODEL_DIR = r'd:\VECTOR\model'
MODEL_PATH = os.path.join(MODEL_DIR, 'risk_model.pkl')
FEATURE_COLS_PATH = os.path.join(MODEL_DIR, 'feature_columns.json')

# Human-readable display names for raw feature columns.
# Features not listed here fall back to a cleaned-up version of the column name.
FEATURE_DISPLAY_NAMES = {
    'income': 'Income',
    'name_email_similarity': 'Name-Email Similarity',
    'prev_address_months_count': 'Previous Address Duration',
    'current_address_months_count': 'Current Address Duration',
    'customer_age': 'Customer Age',
    'days_since_request': 'Days Since Request',
    'intended_balcon_amount': 'Intended Balance Amount',
    'zip_count_4w': 'ZIP Code Activity (4 weeks)',
    'velocity_6h': '6-Hour Transaction Velocity',
    'velocity_24h': '24-Hour Transaction Velocity',
    'velocity_4w': '4-Week Transaction Velocity',
    'bank_branch_count_8w': 'Bank Branch Count (8 weeks)',
    'date_of_birth_distinct_emails_4w': 'DOB Distinct Emails (4 weeks)',
    'credit_risk_score': 'Credit Risk Score',
    'email_is_free': 'Free Email Provider',
    'phone_home_valid': 'Home Phone Valid',
    'phone_mobile_valid': 'Mobile Phone Valid',
    'bank_months_count': 'Bank Account Age (months)',
    'has_other_cards': 'Has Other Cards',
    'proposed_credit_limit': 'Proposed Credit Limit',
    'foreign_request': 'Foreign Request',
    'session_length_in_minutes': 'Session Length (minutes)',
    'keep_alive_session': 'Keep-Alive Session',
    'device_distinct_emails_8w': 'Device Distinct Emails (8 weeks)',
    'device_fraud_count': 'Device Fraud Count',
    'accel_short_term': 'Short-Term Risk Acceleration',
    'accel_long_term': 'Long-Term Risk Acceleration',
}


def _format_feature_name(raw_name):
    """Convert a raw feature column name to a human-readable label."""
    if raw_name in FEATURE_DISPLAY_NAMES:
        return FEATURE_DISPLAY_NAMES[raw_name]
    # Fallback: clean up one-hot encoded names like 'payment_type_AB' → 'Payment Type: AB'
    parts = raw_name.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isupper() and len(parts[1]) <= 3:
        base = parts[0].replace('_', ' ').title()
        return f"{base}: {parts[1]}"
    return raw_name.replace('_', ' ').title()


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
        self.explainer = None  # SHAP TreeExplainer
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        self.load_model()

    def load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            with open(FEATURE_COLS_PATH, 'r') as f:
                self.feature_columns = json.load(f)
            print("Model and feature columns loaded successfully.")

            # Initialize SHAP TreeExplainer (fast & exact for tree-based models)
            if shap is not None and self.model is not None:
                try:
                    self.explainer = shap.TreeExplainer(self.model)
                    print("SHAP TreeExplainer initialized successfully.")
                except Exception as e:
                    print(f"Warning: Could not initialize SHAP explainer: {e}")
                    self.explainer = None
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

    def _get_shap_drivers(self, shap_values_row, feature_names, top_n=3):
        """Extract top-N risk-driving features from a single row's SHAP values.
        
        Args:
            shap_values_row: 1-D array of SHAP values for one prediction.
            feature_names: list of feature column names matching the SHAP values.
            top_n: number of top drivers to return.
            
        Returns:
            A human-readable string like "High 6-Hour Velocity (+0.32), Low Credit Score (+0.18)".
        """
        abs_shap = np.abs(shap_values_row)
        top_indices = np.argsort(abs_shap)[::-1][:top_n]

        drivers = []
        for idx in top_indices:
            val = shap_values_row[idx]
            if abs(val) < 1e-6:
                continue  # skip negligible contributions
            feat_name = _format_feature_name(feature_names[idx])
            direction = "High" if val > 0 else "Low"
            drivers.append(f"{direction} {feat_name} ({val:+.3f})")

        if not drivers:
            drivers.append("No dominant risk factor")

        return ", ".join(drivers)

    def get_top_risk_drivers(self, row, feature_names):
        """Fallback heuristic method when SHAP is unavailable.
        
        Identify which features are contributing most to the risk score
        using simple threshold-based rules.
        """
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
        
        # Get risk drivers using SHAP (preferred) or heuristic fallback
        if self.explainer is not None:
            try:
                # Compute SHAP values for the entire batch (vectorized, fast)
                shap_values = self.explainer.shap_values(X)

                # For binary classification, shap_values may be a list [class_0, class_1]
                # or a 2-D array. We want the class-1 (fraud) explanations.
                if isinstance(shap_values, list):
                    shap_vals = shap_values[1]  # class 1 (fraud)
                else:
                    shap_vals = shap_values

                drivers_list = []
                for i in range(len(X)):
                    drivers_list.append(
                        self._get_shap_drivers(shap_vals[i], self.feature_columns, top_n=3)
                    )
                print(f"SHAP explainability computed for {len(X)} records.")
            except Exception as e:
                print(f"SHAP computation failed, falling back to heuristic: {e}")
                drivers_list = []
                for i, row in X.iterrows():
                    drivers_list.append(self.get_top_risk_drivers(row, self.feature_columns))
        else:
            # Fallback to heuristic when SHAP is not available
            drivers_list = []
            for i, row in X.iterrows():
                drivers_list.append(self.get_top_risk_drivers(row, self.feature_columns))
            
        results_df['Top Risk Drivers'] = drivers_list
        
        return results_df
