# Risk Detection Desktop App — Build Instructions (Option A: Real .exe)

This document is the full step-by-step guide to build, test, and package your
solution as a genuine Windows `.exe`, using:

- **Model**: XGBoost, trained on a synthetic dataset representing your 7 behavioral signals
- **GUI**: Python (Tkinter)
- **Input**: CSV upload
- **Output**: A single Windows `.exe` built via PyInstaller

> **Note on assumptions**: I've filled in the 7 behavioral signals and risk
> velocity/acceleration logic based on our earlier conversation. If your actual
> Problem Statement (PS) defines different signals, fields, or scoring logic,
> tell me and I'll regenerate the dataset/model/GUI to match exactly — this is
> the one part that must be accurate for the demo to make sense.

---

## 1. Why It Has To Be Built This Way

- I can write and test the ML model, the GUI logic, and the packaging script
  in my sandbox (Linux).
- I **cannot** produce a Windows `.exe` from a Linux sandbox — PyInstaller
  builds for whatever OS it runs on.
- So: I build everything, you run **one command** on your own Windows machine,
  and PyInstaller produces the real `.exe` there. This takes about 60 seconds
  on your end.

---

## 2. Final Project Structure

```
risk-detector-app/
│
├── data/
│   └── generate_synthetic_data.py     # creates training data (7 signals x 3 months)
│   └── synthetic_transactions.csv     # generated dataset (output of above)
│
├── model/
│   └── train_model.py                 # trains XGBoost model on synthetic data
│   └── risk_model.pkl                 # trained model (output of above)
│   └── feature_columns.json           # feature order/names used by the model
│
├── app/
│   └── gui_app.py                     # Tkinter GUI: CSV upload, scoring, results view
│   └── risk_engine.py                 # core scoring logic (velocity/acceleration calc)
│
├── build/
│   └── build_exe.bat                  # one-command Windows build script
│   └── app.spec                       # PyInstaller spec file
│
├── requirements.txt                   # exact Python deps + versions
├── README.md                          # end-user run instructions
└── INSTRUCTIONS.md                    # this file
```

---

## 3. Step-by-Step Build Process

### Step 1 — Set up the project folder
Create the folder structure above. Keeping data/model/app/build separated
makes it easy to explain your architecture during the review.

### Step 2 — Generate the synthetic dataset
`data/generate_synthetic_data.py` creates monthly records for each of the
7 behavioral signals, across 3 months, for a population of synthetic
customers, with a fraud/risk label baked in based on rule-based thresholds
plus noise (so the model has real signal to learn, not just memorize rules).

Run:
```bash
python data/generate_synthetic_data.py
```
Output: `data/synthetic_transactions.csv`

### Step 3 — Compute Risk Velocity & Acceleration features
From the 3 monthly snapshots per customer, derive:
- **Risk Velocity** = rate of change of each signal month-to-month
- **Risk Acceleration** = rate of change of velocity (i.e., is the change
  itself speeding up)

This feature engineering happens inside `train_model.py` before training,
and again inside `risk_engine.py` at inference time (so training and
prediction use identical logic).

### Step 4 — Train the model
```bash
python model/train_model.py
```
This trains an XGBoost classifier on the engineered features and saves:
- `model/risk_model.pkl`
- `model/feature_columns.json` (so the GUI always feeds features in the
  correct order)

You'll see accuracy/precision/recall printed — expect demo-grade numbers
(this is normal and expected, since it's synthetic data).

### Step 5 — Build and test the GUI logic (without rendering)
`app/gui_app.py` handles:
1. "Upload CSV" button → file dialog
2. Validates the CSV has the expected columns
3. Passes data through `risk_engine.py` to compute features + get model
   predictions
4. Displays a results table: customer ID, risk score, risk category, and
   the specific signals driving the score (for explainability)

I test `risk_engine.py`'s logic directly (no GUI needed for that), and
syntax-check `gui_app.py`, but the actual window rendering can only be
verified on your machine since Tkinter isn't available in this sandbox.

### Step 6 — Package into a Windows .exe
On your Windows laptop:
```bash
cd risk-detector-app
pip install -r requirements.txt
build\build_exe.bat
```
This runs PyInstaller with `app.spec`, bundling the model file and all
dependencies into a single `.exe` inside a `dist/` folder.

### Step 7 — Test before your review
1. Double-click the `.exe` in `dist/`
2. Upload a sample CSV (I'll include one test file)
3. Confirm the results table populates correctly
4. Do this **tonight**, not right before your slot — leaves time to fix
   anything

---

## 4. What You Need To Do Right Now

1. Confirm the **7 behavioral signals** match your actual PS (tell me the
   exact names/definitions if different)
2. Confirm the **CSV format** you expect to demo with (columns, one row per
   customer per month, etc.)
3. Confirm you have a **Windows machine** available tonight to run Step 6

Once confirmed, I'll generate all the actual files (dataset generator,
training script, GUI, risk engine, build script, requirements.txt, README)
in this session.
