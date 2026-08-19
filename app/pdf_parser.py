import os
import pandas as pd
import numpy as np
import joblib
import json

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import shap
except ImportError:
    shap = None
    print("WARNING: shap not installed. SHAP-based explainability will be unavailable for PDF flow.")

MODEL_DIR = r'd:\VECTOR\model'
MODEL_PATH = os.path.join(MODEL_DIR, 'pdf_risk_model.pkl')
FEATURE_COLS_PATH = os.path.join(MODEL_DIR, 'pdf_feature_columns.json')

# Human-readable display names for PDF risk model features
PDF_FEATURE_DISPLAY_NAMES = {
    'total_deposit': 'Total Deposits',
    'total_withdrawal': 'Total Withdrawals',
    'high_val_withdrawals': 'High-Value Withdrawal Count',
    'balance_volatility': 'Balance Volatility',
    'avg_withdrawal': 'Average Withdrawal Amount',
    'w_to_d_ratio': 'Withdrawal/Deposit Ratio',
}


def _format_pdf_feature_name(raw_name):
    """Convert a raw feature column name to a human-readable label."""
    if raw_name in PDF_FEATURE_DISPLAY_NAMES:
        return PDF_FEATURE_DISPLAY_NAMES[raw_name]
    return raw_name.replace('_', ' ').title()


class PDFRiskEngine:
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.explainer = None  # SHAP TreeExplainer
        self.load_model()

    def load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            with open(FEATURE_COLS_PATH, 'r') as f:
                self.feature_columns = json.load(f)
            print("PDF Model loaded successfully.")

            # Initialize SHAP TreeExplainer for the PDF model
            if shap is not None and self.model is not None:
                try:
                    self.explainer = shap.TreeExplainer(self.model)
                    print("SHAP TreeExplainer initialized for PDF model.")
                except Exception as e:
                    print(f"Warning: Could not initialize SHAP explainer for PDF model: {e}")
                    self.explainer = None
        except Exception as e:
            print(f"Error loading PDF model: {e}")
            self.model = None

    def parse_pdf_to_transactions(self, pdf_path):
        """Extracts the transaction table from our synthetic PDF."""
        if pdfplumber is None:
            raise ImportError("pdfplumber is required to parse PDFs. Please run: pip install pdfplumber")
            
        data = []
        cust_id = "UNKNOWN"
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract text to find Customer ID
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        if "Customer ID:" in line:
                            cust_id = line.split("Customer ID:")[1].strip()
                            
                # Extract tables
                table = page.extract_table()
                if table:
                    # First row is usually the header
                    header = table[0]
                    if "Date" in header and "Withdrawal" in header:
                        for row in table[1:]:
                            if len(row) >= 5:
                                date, desc, withdrawal, deposit, balance = row
                                
                                # Clean up formatting (e.g. if they are empty strings)
                                withdrawal = float(withdrawal) if withdrawal and withdrawal.strip() else 0.0
                                deposit = float(deposit) if deposit and deposit.strip() else 0.0
                                balance = float(balance) if balance and balance.strip() else 0.0
                                
                                data.append({
                                    "customer_id": cust_id,
                                    "date": date,
                                    "description": desc,
                                    "withdrawal": withdrawal,
                                    "deposit": deposit,
                                    "balance": balance
                                })
                                
        if not data:
            raise ValueError("No transaction data could be extracted from this PDF.")
            
        return pd.DataFrame(data)

    def extract_features(self, df):
        """Same feature extraction as the training script."""
        total_deposit = df['deposit'].sum()
        total_withdrawal = df['withdrawal'].sum()
        high_val_withdrawals = (df['withdrawal'] > 1000).sum()
        
        balance_volatility = df['balance'].std()
        if pd.isna(balance_volatility):
            balance_volatility = 0
            
        avg_withdrawal = df[df['withdrawal'] > 0]['withdrawal'].mean()
        if pd.isna(avg_withdrawal):
            avg_withdrawal = 0
            
        w_to_d_ratio = total_withdrawal / (total_deposit + 1)
        
        features = {
            'total_deposit': total_deposit,
            'total_withdrawal': total_withdrawal,
            'high_val_withdrawals': high_val_withdrawals,
            'balance_volatility': balance_volatility,
            'avg_withdrawal': avg_withdrawal,
            'w_to_d_ratio': w_to_d_ratio
        }
        
        # Format as dataframe with correct columns
        X = pd.DataFrame([features])
        
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
                
        return X[self.feature_columns]

    def _get_shap_drivers(self, shap_values_row, feature_names, top_n=3):
        """Extract top-N risk-driving features from a single row's SHAP values.
        
        Args:
            shap_values_row: 1-D array of SHAP values for one prediction.
            feature_names: list of feature column names matching the SHAP values.
            top_n: number of top drivers to return.
            
        Returns:
            A human-readable string describing the top contributing features.
        """
        abs_shap = np.abs(shap_values_row)
        top_indices = np.argsort(abs_shap)[::-1][:top_n]

        drivers = []
        for idx in top_indices:
            val = shap_values_row[idx]
            if abs(val) < 1e-6:
                continue  # skip negligible contributions
            feat_name = _format_pdf_feature_name(feature_names[idx])
            direction = "High" if val > 0 else "Low"
            drivers.append(f"{direction} {feat_name} ({val:+.3f})")

        if not drivers:
            drivers.append("Normal transaction activity")

        return ", ".join(drivers)

    def get_risk_drivers(self, features_df):
        """Fallback heuristic method when SHAP is unavailable."""
        drivers = []
        row = features_df.iloc[0]
        
        if row['w_to_d_ratio'] > 1.5:
            drivers.append("High withdrawal to deposit ratio")
        if row['high_val_withdrawals'] > 3:
            drivers.append("Multiple high value withdrawals")
        if row['balance_volatility'] > 2000:
            drivers.append("High balance volatility")
            
        if not drivers:
            drivers.append("Normal transaction activity")
            
        return ", ".join(drivers)

    def predict(self, pdf_path):
        if self.model is None:
            raise ValueError("PDF Model not loaded. Run train_pdf_model.py first.")
            
        # Parse PDF
        df = self.parse_pdf_to_transactions(pdf_path)
        cust_id = df['customer_id'].iloc[0]
        
        # Extract features
        X = self.extract_features(df)
        
        # Predict
        score = self.model.predict_proba(X)[0][1]
        
        # Determine category
        if score >= 0.8: category = "Critical"
        elif score >= 0.6: category = "High"
        elif score >= 0.4: category = "Medium"
        else: category = "Low"
        
        # Get risk drivers using SHAP (preferred) or heuristic fallback
        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(X)
                # For binary classification, shap_values may be a list [class_0, class_1]
                if isinstance(shap_values, list):
                    shap_vals = shap_values[1]  # class 1 (risk)
                else:
                    shap_vals = shap_values
                drivers = self._get_shap_drivers(shap_vals[0], self.feature_columns, top_n=3)
                print("SHAP explainability computed for PDF prediction.")
            except Exception as e:
                print(f"SHAP computation failed for PDF, falling back to heuristic: {e}")
                drivers = self.get_risk_drivers(X)
        else:
            drivers = self.get_risk_drivers(X)
        
        # Return a dataframe with one row, formatted like the CSV results
        result = pd.DataFrame([{
            'customer_id': cust_id,
            'Risk Score': score,
            'Risk Category': category,
            'Top Risk Drivers': drivers
        }])
        
        return result
