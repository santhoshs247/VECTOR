# ⚡ EXECUTE — Full Run Guide (From Scratch)

**Project**: Risk Detection Desktop App  
**Model**: XGBoost ML · **GUI**: Tkinter · **Output**: Windows `.exe`

This guide takes you from a fresh machine all the way to a working desktop app showing risk analysis results on screen.

---

## ✅ CHECKLIST AT A GLANCE

```
[ ] Step 1 — Check / Install Python
[ ] Step 2 — Open PowerShell in the project folder
[ ] Step 3 — Install all required libraries
[ ] Step 4 — Train the ML model
[ ] Step 5 — Run the GUI app (see output on screen)
[ ] Step 6 — Load CSV data and view results
[ ] Step 7 — (Optional) Build the standalone .exe
```

---

## STEP 1 — Install Python (if not already installed)

1. Go to: **https://www.python.org/downloads/**
2. Download **Python 3.9 or higher** (e.g., Python 3.11 recommended)
3. Run the installer — **IMPORTANT**: on the first screen, tick  
   ✅ **"Add Python to PATH"** before clicking Install
4. After install, verify it worked — open PowerShell and run:

```powershell
python --version
```

You should see something like: `Python 3.11.x`  
If you see an error, Python is not in PATH — reinstall with the checkbox ticked.

---

## STEP 2 — Open PowerShell in the Project Folder

1. Open **Windows PowerShell** (search it in the Start Menu)
2. Navigate to the VECTOR project folder:

```powershell
cd d:\VECTOR
```

> All commands from this point forward should be run from `d:\VECTOR`.

---

## STEP 3 — Install All Required Libraries

Run this single command to install every dependency the project needs:

```powershell
pip install -r requirements.txt
```

This installs:

| Library | Purpose |
|---|---|
| `xgboost` | Machine learning model (risk scoring) |
| `scikit-learn` | Model training utilities |
| `pandas` | Reading and processing CSV data |
| `numpy` | Numerical computations |
| `joblib` | Saving/loading the trained model |
| `pyinstaller` | Packaging the app into a `.exe` |

Takes about **1–3 minutes** depending on your internet speed.  
When done, you will see: `Successfully installed ...`

> **If you get a pip error**, try: `python -m pip install -r requirements.txt`

---

## STEP 4 — Train the ML Model

This step reads `DATA\Base.csv`, trains the XGBoost risk classifier, and saves the trained model to `model\risk_model.pkl`.

```powershell
python model\train_model.py
```

**What you will see printed on screen:**

```
Training XGBoost model...
Accuracy:  0.XX
Precision: 0.XX
Recall:    0.XX
Model saved to model/risk_model.pkl
Feature columns saved to model/feature_columns.json
```

Takes about **30–60 seconds**.  
When done, two files will exist:
- `model\risk_model.pkl` — the trained model
- `model\feature_columns.json` — the feature list used by the model

> **Note**: If you already see these files in the `model\` folder, the model is already trained. You can skip this step and go to Step 5.

---

## STEP 5 — Launch the GUI App (See Results on Screen)

This opens the desktop application window directly. No `.exe` needed — it runs straight from Python.

```powershell
python app\gui_app.py
```

A **desktop window** will open — this is your Risk Detection App.

---

## STEP 6 — Load Your CSV Data and View Results

Once the app window is open:

1. Click the **"Upload CSV Data"** button
2. In the file browser that opens, navigate to `d:\VECTOR\DATA\`
3. Select one of these CSV files:
   - `Base.csv` — the primary dataset
   - `Variant I.csv`, `Variant II.csv`, etc. — alternative test sets
4. Click **Open**
5. The app will process the data and display a **results table** with:
   - Customer ID
   - Risk Score
   - Risk Category (Low / Medium / High)
   - Key signals driving the risk score
6. Click **"Export Results"** to save the scored output as a new CSV file.

---

## STEP 7 — (Optional) Build a Standalone .exe

If you want a single clickable `.exe` file you can run anywhere (without Python installed):

```powershell
.\build\build_exe.bat
```

Takes about **1–3 minutes**.  
When done, the `.exe` will be at:

```
d:\VECTOR\dist\RiskDetector.exe
```

Double-click `RiskDetector.exe` to launch — no Python needed on that machine.

---

## QUICK ONE-SHOT COMMANDS

Train and launch the app in one go:

```powershell
cd d:\VECTOR; python model\train_model.py; python app\gui_app.py
```

Train, build the .exe, and launch:

```powershell
cd d:\VECTOR; python model\train_model.py; .\build\build_exe.bat; python app\gui_app.py
```

---

## Project Structure Reference

```
d:\VECTOR\
|
|-- DATA\
|   |-- Base.csv              <- Primary dataset (upload this in the app)
|   |-- Variant I.csv
|   |-- Variant II.csv
|   |-- Variant III.csv
|   |-- Variant IV.csv
|   +-- Variant V.csv
|
|-- model\
|   |-- train_model.py        <- Step 4: Run this to train
|   |-- risk_model.pkl        <- Auto-generated after training
|   +-- feature_columns.json  <- Auto-generated after training
|
|-- app\
|   |-- gui_app.py            <- Step 5: Run this to open the app
|   +-- risk_engine.py        <- Core scoring logic (runs automatically)
|
|-- build\
|   +-- build_exe.bat         <- Step 7: Run this to create .exe
|
|-- dist\
|   +-- RiskDetector.exe      <- Final .exe (created after Step 7)
|
|-- requirements.txt          <- All Python libraries needed
|-- EXECUTE.md                <- This file
+-- README.md                 <- Short summary
```

---

## Common Issues and Fixes

| Problem | Fix |
|---|---|
| `python` not recognized | Reinstall Python with "Add to PATH" ticked |
| `pip` not recognized | Use `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError` | Re-run Step 3 to install libraries |
| `FileNotFoundError: Base.csv` | Make sure you are in `d:\VECTOR` and `DATA\Base.csv` exists |
| `risk_model.pkl not found` | Run Step 4 (train the model) first |
| GUI window does not open | Try `python -m tkinter` — if it errors, reinstall Python |
| `.exe` build fails | Make sure `pip install pyinstaller` worked in Step 3 |

---

## All Commands — Quick Reference

```powershell
# Go to project folder
cd d:\VECTOR

# Install libraries
pip install -r requirements.txt

# Train the model
python model\train_model.py

# Launch the app
python app\gui_app.py

# (Optional) Build .exe
.\build\build_exe.bat
```
