# VECTOR: Risk Detection Desktop Application

## Project Overview
**VECTOR** is a comprehensive Windows desktop application designed to analyze customer behavioral data and financial statements for detecting fraud and assessing risk. The application ingests customer transaction data (CSV) and statement documents (PDF), computes complex risk metrics, scores the data using a trained machine learning model, and presents the results through an intuitive, dark-themed graphical user interface (GUI).

---

## Models Used in the Project
The core intelligence of the application is powered by Machine Learning:
- **XGBoost (Extreme Gradient Boosting)**: The primary classification model used to predict risk and fraud. It is highly efficient and capable of handling non-linear relationships in behavioral data.
- **SHAP (SHapley Additive exPlanations)**: A game-theory-based explainability framework that computes per-prediction feature contributions using Shapley values. Integrated via `shap.TreeExplainer` for fast, exact explanations of XGBoost predictions.
- **Scikit-Learn**: Used for model training utilities, data preprocessing, and evaluation metrics (Accuracy, Precision, Recall).
- **Joblib**: Used for saving and loading trained models efficiently (`risk_model.pkl`, `pdf_risk_model.pkl`).

---

## Key Features
1. **Desktop GUI**: A modern, dark-themed user-friendly interface built using CustomTkinter and Tkinter.
2. **CSV & PDF Data Upload**: Support for uploading customer behavioral datasets (`Base.csv`) and PDF financial statements (`.pdf`) for automated ML risk scoring.
3. **Explainable AI (SHAP)**: The results table provides a Risk Score, Risk Category (Low / Medium / High / Critical), and highlights the **key signals driving the risk score** using **SHAP (SHapley Additive exPlanations)**. `TreeExplainer` identifies top feature drivers with exact Shapley contribution values (e.g., "High 6-Hour Velocity (+0.32)").
4. **Dashboard Analytical Views (Tabs)**:
   - **📋 Results Table**: Interactive data grid with live filter toolbar and double-click customer risk profile detail inspector modal.
   - **📊 Risk Breakdown**: Visual summary displaying category counts, percentages with styled progress bars, and aggregate score statistics (mean, highest, lowest).
   - **🏆 Top 10 High Risk**: Highlighting the highest-risk records ranked with medal icons (🥇 🥈 🥉) and probability gauge bars.
5. **Interactive Filter & Search Toolbar**:
   - **Category Filter**: Filter by `Critical`, `High`, `Medium`, or `Low`.
   - **Score Range Sliders**: Dual sliders to set Minimum and Maximum probability score boundaries (`0.00` to `1.00`).
   - **Search Input**: Live substring search for Customer IDs (e.g. `CUST-00042`).
   - **Sort Dropdown**: Sort grid by `Row #`, `Score ↓`, `Score ↑`, or `Category`.
   - **Reset & Count**: Reset all filters instantly and view live active record counts.
6. **Audit History & Logging**:
   - Time-range filter (`All Time`, `Today`, `Last 7 Days`, `Last 30 Days`).
   - Chronological sorting toggle (`Newest First` / `Oldest First`).
   - Session tracking saved to `RESULT/audit_history.json` with execution time, filename, total records, and risk counts.
   - Safe clear history feature with confirmation dialog.
7. **Model Settings & Custom Thresholds**:
   - View loaded model metadata (file, status, feature count, last trained date).
   - Adjust probability boundaries dynamically (`Critical ≥`, `High ≥`, `Medium ≥`) with live threshold application.
   - Retrain model directly from the UI via asynchronous subprocess execution.
8. **Data Export**: Export analyzed results and risk predictions to CSV files.
9. **Standalone Executable**: Packageable into a single, portable Windows `.exe` file using PyInstaller.

---

## UI Components Used
The Graphical User Interface (GUI) is built using **CustomTkinter** alongside standard **Tkinter** and **ttk** components.

### 1. CustomTkinter Components (`ctk.`)
- **`CTk`**: The main application window (`RiskApp`).
- **`CTkFrame`**: Structured layout containers for Headers, Sidebar, Dashboard cards, Tab content, and Overlays.
- **`CTkButton`**: Interactive buttons for navigation, file upload, export, reset, retrain, and clearing history.
- **`CTkLabel`**: Typography elements for metrics, statuses, headers, and badge indicators.
- **`CTkOptionMenu`**: Dropdowns for Category filtering, Sort selection, and Audit History time ranges.
- **`CTkSlider`**: Sliders for score range filtering (Min/Max) and setting risk probability thresholds.
- **`CTkEntry`**: Live search input box for filtering Customer IDs.
- **`CTkProgressBar`**: Used for animated loading overlay, Risk Breakdown category percentages, and the detail modal score gauge.
- **`CTkScrollableFrame`**: Scrollable containers for the Risk Breakdown stats tab and Audit History session list.
- **`CTkToplevel`**: Pop-up inspector modal for inspecting individual customer risk profiles.
- **`CTkFont`**: Standardized modern typography system using Segoe UI.

### 2. Standard Tkinter / TTK Components (`tk.` & `ttk.`)
- **`ttk.Treeview`**: Primary tabular grid component for displaying customer risk records and top 10 rankings.
- **`ttk.Scrollbar`**: Vertical and horizontal scrollbars for treeview grids.
- **`ttk.Style`**: Customized dark theme ("clam") matching the application background.
- **`tk.Toplevel`, `tk.Frame`, `tk.Label`**: Floating hover `ToolTip` component for risk drivers.

---

## Processes and Steps Involved

### 1. Data Preparation & Generation
- Gathering customer behavioral datasets in `DATA/` directory or PDF statements.

### 2. Feature Engineering (Risk Engine)
- Calculation of dynamic metrics, Risk Velocity, and Acceleration over time.

### 3. Model Training
- Running `python model/train_model.py` or `python model/train_pdf_model.py`.
- Generates `risk_model.pkl`, `pdf_risk_model.pkl`, and `feature_columns.json`.

### 4. Application Execution & Inference
- Running `python app/gui_app.py`.
- Launches desktop application, initializes XGBoost models and SHAP TreeExplainer, and scores uploaded data in real time.

### 5. Application Packaging (Deployment)
- Running `build\build_exe.bat`.
- Bundles code and dependencies into `dist/RiskDetector.exe`.
