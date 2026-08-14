import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
import os

DATA_PATH = r'd:\VECTOR\DATA\Bank_Transactions.csv'
MODEL_DIR = r'd:\VECTOR\model'
MODEL_PATH = os.path.join(MODEL_DIR, 'pdf_risk_model.pkl')
FEATURE_COLS_PATH = os.path.join(MODEL_DIR, 'pdf_feature_columns.json')

def extract_features_from_transactions(df):
    """Aggregates raw transactions into customer-level features."""
    
    # Group by customer_id
    grouped = df.groupby('customer_id')
    
    features = []
    labels = []
    
    for name, group in grouped:
        # Features
        total_deposit = group['deposit'].sum()
        total_withdrawal = group['withdrawal'].sum()
        
        # High value transactions (e.g. > $1000 withdrawal)
        high_val_withdrawals = (group['withdrawal'] > 1000).sum()
        
        # Balance volatility (std dev of balance)
        balance_volatility = group['balance'].std()
        if pd.isna(balance_volatility):
            balance_volatility = 0
            
        # Velocity of spend (average withdrawal amount per transaction)
        avg_withdrawal = group[group['withdrawal'] > 0]['withdrawal'].mean()
        if pd.isna(avg_withdrawal):
            avg_withdrawal = 0
            
        # Withdrawal to deposit ratio
        w_to_d_ratio = total_withdrawal / (total_deposit + 1)
        
        features.append({
            'total_deposit': total_deposit,
            'total_withdrawal': total_withdrawal,
            'high_val_withdrawals': high_val_withdrawals,
            'balance_volatility': balance_volatility,
            'avg_withdrawal': avg_withdrawal,
            'w_to_d_ratio': w_to_d_ratio
        })
        
        # The label is the same for all rows for a given customer in this synthetic dataset
        labels.append(group['is_risk'].iloc[0])
        
    X = pd.DataFrame(features)
    y = pd.Series(labels)
    
    return X, y, list(X.columns)

def train_model():
    if not os.path.exists(DATA_PATH):
        print(f"Error: Training data not found at {DATA_PATH}. Run generate_pdf_data.py first.")
        return
        
    print("Loading transaction data...")
    df = pd.read_csv(DATA_PATH)
    
    print("Engineering features...")
    X, y, feature_columns = extract_features_from_transactions(df)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training XGBoost PDF Risk Model...")
    
    neg_cases = (y_train == 0).sum()
    pos_cases = (y_train == 1).sum()
    scale_pos_weight = neg_cases / max(1, pos_cases)
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    # Save the model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    with open(FEATURE_COLS_PATH, 'w') as f:
        json.dump(feature_columns, f)
        
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
