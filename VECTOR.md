# VECTOR: Risk Detection Desktop Application

## Project Overview
**VECTOR** is a comprehensive Windows desktop application designed to analyze customer behavioral data for detecting fraud and assessing risk. The application ingests customer transaction data, computes complex risk metrics, scores the data using a trained machine learning model, and presents the results through an intuitive graphical user interface (GUI).

---

## Models Used in the Project
The core intelligence of the application is powered by Machine Learning:
- **XGBoost (Extreme Gradient Boosting)**: The primary classification model used to predict risk and fraud. It is highly efficient and capable of handling non-linear relationships in behavioral data.
- **Scikit-Learn**: Used for model training utilities, data preprocessing, and evaluation metrics (Accuracy, Precision, Recall).
- **Joblib**: Used for saving and loading the trained model efficiently (`risk_model.pkl`).

---

## Key Features
1. **Desktop GUI**: A user-friendly interface built using Python's Tkinter / CustomTkinter. It allows users to interact with the ML model without touching any code.
2. **CSV Data Upload**: Users can easily upload datasets (e.g., `Base.csv`, `Variant I.csv`) directly into the app for batch risk scoring.
3. **Explainable AI**: The results table not only provides a Risk Score and Risk Category (Low / Medium / High) but also highlights the **key signals driving the risk score** for explainability.
4. **Data Export**: Scored data and risk assessments can be exported to a new CSV file for reporting and further analysis.
5. **Standalone Executable**: The entire application, including the Python runtime and ML models, can be packaged into a single, portable Windows `.exe` file using PyInstaller. No Python installation is required for the end user.
6. **Advanced Feature Engineering**: The system calculates dynamic metrics over time, such as:
   - **Risk Velocity**: The rate of change of behavioral signals month-to-month.
   - **Risk Acceleration**: The rate of change of the risk velocity (identifying if the risk behavior is speeding up).

---

## UI Components Used
The Graphical User Interface (GUI) is built using **CustomTkinter** (a modern, dark-themed wrapper for Tkinter) alongside standard **Tkinter** and **ttk** components.

### 1. CustomTkinter Components (`ctk.`)
- **`CTk`**: The main application window (`RiskApp`).
- **`CTkFrame`**: Containers used to structure the layout (Headers, Sidebar, Dashboard cards, and overlays).
- **`CTkButton`**: Interactive buttons for navigation, uploading files, and exporting data.
- **`CTkLabel`**: Text elements for displaying titles, metrics, and statuses.
- **`CTkProgressBar`**: Used for the animated loading overlay and the visual "Score Gauge" in the detail modal.
- **`CTkToplevel`**: The pop-up modal inspector window shown when viewing a customer's detailed risk profile.
- **`CTkFont`**: Applies custom typography (e.g., "Segoe UI") throughout the app.

### 2. Standard Tkinter / TTK Components (`tk.` & `ttk.`)
- **`ttk.Treeview`**: Forms the core data table on the dashboard, displaying customer IDs, scores, and risk categories in columns.
- **`ttk.Scrollbar`**: Provides horizontal and vertical scrolling for the data table.
- **`ttk.Style`**: Applies a dark theme ("clam") to the Treeview to match the CustomTkinter aesthetic.
- **`tk.Toplevel`, `tk.Frame`, `tk.Label`**: Leveraged specifically to implement a custom, floating `ToolTip` that appears on hover over the "Top Risk Drivers" column.

---

## Processes and Steps Involved

The project follows a structured end-to-end machine learning and software engineering pipeline:

### 1. Data Preparation & Generation
The first step involves gathering customer behavioral data. The system expects records across multiple months (e.g., 3-month snapshots) for various behavioral signals (7 key signals). 
- **Process**: Synthetic data generation or real data extraction resulting in CSV files stored in the `DATA/` directory.

### 2. Feature Engineering (Risk Engine)
Raw data is transformed into meaningful inputs for the ML model.
- **Process**: The system computes "Risk Velocity" and "Risk Acceleration" from the monthly snapshots. This gives the model insight into the trajectory of a customer's behavior, rather than just static snapshots.

### 3. Model Training
The ML model must be trained on historical data before it can make predictions.
- **Process**: Running `python model/train_model.py`.
- **Action**: This script reads the base data, performs feature engineering, trains the XGBoost classifier, and saves the artifacts (`risk_model.pkl` and `feature_columns.json`) to the `model/` directory.

### 4. Application Execution & Inference
Running the user interface for real-time or batch prediction.
- **Process**: Running `python app/gui_app.py`.
- **Action**: The GUI launches, loads the pre-trained XGBoost model and feature configurations. The user uploads a CSV, and the `risk_engine.py` processes the data identical to the training phase, runs it through the model, and displays the risk categories on the screen.

### 5. Application Packaging (Deployment)
Transforming the Python project into a distributable software product.
- **Process**: Running `build\build_exe.bat`.
- **Action**: PyInstaller bundles the GUI code, the ML engine, the XGBoost library, and the trained model weights into a standalone `RiskDetector.exe` in the `dist/` folder. This executable can be shared and run on any Windows machine.
