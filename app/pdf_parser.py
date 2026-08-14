import os
import pandas as pd
import joblib
import json

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

MODEL_DIR = r'd:\VECTOR\model'
MODEL_PATH = os.path.join(MODEL_DIR, 'pdf_risk_model.pkl')
FEATURE_COLS_PATH = os.path.join(MODEL_DIR, 'pdf_feature_columns.json')

class PDFRiskEngine:
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.load_model()

    def load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            with open(FEATURE_COLS_PATH, 'r') as f:
                self.feature_columns = json.load(f)
            print("PDF Model loaded successfully.")
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

    def get_risk_drivers(self, features_df):
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
        
        drivers = self.get_risk_drivers(X)
        
        # Return a dataframe with one row, formatted like the CSV results
        result = pd.DataFrame([{
            'customer_id': cust_id,
            'Risk Score': score,
            'Risk Category': category,
            'Top Risk Drivers': drivers
        }])
        
        return result
