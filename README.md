# Risk Detection Desktop App

A Windows desktop application for analyzing customer behavioral data to detect fraud/risk using an XGBoost ML model.

## Prerequisites
- Python 3.9+ installed on your system
- Windows OS (to build the `.exe`)

## 1. Setup

First, install all required dependencies:

```bash
pip install -r requirements.txt
```

## 2. Train the Model

Before building the application, you must train the model using your CSV dataset. 

```bash
python model/train_model.py
```
This will read data from `data/Base.csv`, train the XGBoost classifier, and output:
- `model/risk_model.pkl`
- `model/feature_columns.json`

## 3. Run the App (Development)

To test the application locally without building the `.exe`:

```bash
python app/gui_app.py
```

## 4. Build the Executable

To package the application into a single `.exe` file that you can share:

```bash
build\build_exe.bat
```

This script will run PyInstaller and bundle everything (including the trained model) into `dist/RiskDetector.exe`.

## 5. Usage

1. Open `RiskDetector.exe`.
2. Click **Upload CSV Data**.
3. Select your dataset (e.g., `Variant I.csv`).
4. The application will analyze the data, score the risk of each customer, and display the results in the table.
5. Click **Export Results** to save the scored data.
