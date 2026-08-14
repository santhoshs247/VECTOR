import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
import os

# Define constants
DATA_PATH = r'd:\VECTOR\data\Base.csv'
MODEL_DIR = r'd:\VECTOR\model'
MODEL_PATH = os.path.join(MODEL_DIR, 'risk_model.pkl')
FEATURE_COLS_PATH = os.path.join(MODEL_DIR, 'feature_columns.json')

def load_and_preprocess_data(filepath, sample_size=100000):
    """Loads a sample of the data and engineers features."""
    print(f"Loading {sample_size} rows from {filepath}...")
    # Load only a sample for quick training, in production you'd use all or more
    try:
        df = pd.read_csv(filepath, nrows=sample_size)
    except FileNotFoundError:
        print(f"Error: Dataset not found at {filepath}")
        return None, None

    # Handle missing values (simple imputation for this example)
    df.fillna(-1, inplace=True)

    # Feature Engineering
    # 1. Calculate Risk Acceleration (e.g., change in velocity from 4w to 24h to 6h)
    # This is a simplified proxy for acceleration based on available data
    # (v_6h - v_24h) / 18h vs (v_24h - v_4w) / (28*24 - 24)h
    df['accel_short_term'] = (df['velocity_6h'] - df['velocity_24h']) / (df['velocity_24h'] + 1)
    df['accel_long_term'] = (df['velocity_24h'] - df['velocity_4w']) / (df['velocity_4w'] + 1)

    # 2. Encode categorical variables using target encoding or dummy variables
    # For simplicity in this demo, we'll use pandas get_dummies
    categorical_cols = ['payment_type', 'employment_status', 'housing_status', 'device_os', 'source']
    # Keep only categorical columns that exist in the dataframe
    categorical_cols = [col for col in categorical_cols if col in df.columns]
    
    df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

    # Define target and features
    y = df['fraud_bool']
    X = df.drop(['fraud_bool', 'month'], axis=1, errors='ignore') # Drop target and time indicator
    
    # Store the feature column names to ensure consistency during inference
    feature_columns = list(X.columns)
    
    return X, y, feature_columns

def train_model():
    # Ensure model directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Load and prep data
    X, y, feature_columns = load_and_preprocess_data(DATA_PATH)
    
    if X is None:
        return

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("Training XGBoost model...")
    # Calculate scale_pos_weight to handle class imbalance
    neg_cases = (y_train == 0).sum()
    pos_cases = (y_train == 1).sum()
    scale_pos_weight = neg_cases / max(1, pos_cases)

    # Initialize and train model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )

    model.fit(X_train, y_train)

    print("Evaluating model...")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")

    # Save the model
    print(f"Saving model to {MODEL_PATH}...")
    joblib.dump(model, MODEL_PATH)

    # Save feature columns
    print(f"Saving feature columns to {FEATURE_COLS_PATH}...")
    with open(FEATURE_COLS_PATH, 'w') as f:
        json.dump(feature_columns, f)
        
    print("Training complete.")

if __name__ == "__main__":
    train_model()
