# 🎨 UI Design Plan — Risk Detection Desktop App

**Project**: VECTOR Risk Detection System  
**Stack**: Python · Tkinter (CustomTkinter upgrade) · XGBoost ML  
**Goal**: Replace the basic Tkinter interface with a modern, premium dark-theme desktop UI  

![VECTOR Risk Detection UI Mockup](C:/Users/ADMIN/.gemini/antigravity-ide/brain/4686a6e5-1325-4287-97e1-7d59ba427ee2/ui_mockup_sample_1786592217084.png)

---

## 📌 Overview

The current app (`app/gui_app.py`) uses plain `ttk` Tkinter widgets with manual color theming.
This plan upgrades the entire UI to a polished, professional-grade interface using
**CustomTkinter** — a modern UI library built on Tkinter that supports rounded corners,
smooth widgets, and proper dark mode natively.

---

## 🗂️ File Structure After UI Upgrade

```
d:\VECTOR\
│
├── app\
│   ├── gui_app.py          ← REPLACE (main UI redesign here)
│   ├── risk_engine.py      ← NO CHANGE (backend logic stays the same)
│   └── assets\             ← NEW FOLDER
│       └── icons\          ← Button icons (upload, export, etc.)
│
├── requirements.txt        ← UPDATE (add customtkinter)
└── UI_PLAN.md              ← This file
```

---

## 🎨 Design System

### Color Palette (Dark Theme)

| Token           | Hex       | Usage                          |
|-----------------|-----------|--------------------------------|
| `bg_primary`    | `#0d1117` | Main window background         |
| `bg_secondary`  | `#161b22` | Card / panel backgrounds       |
| `bg_tertiary`   | `#21262d` | Table rows, hover states       |
| `accent_blue`   | `#58a6ff` | Buttons, highlights, links     |
| `accent_purple` | `#bc8cff` | Secondary accents              |
| `text_primary`  | `#e6edf3` | Main text                      |
| `text_muted`    | `#8b949e` | Subtitles, labels              |
| `critical`      | `#f85149` | Critical risk rows/badges      |
| `high`          | `#fb8f44` | High risk rows/badges          |
| `medium`        | `#e3b341` | Medium risk rows/badges        |
| `low`           | `#3fb950` | Low risk rows/badges           |
| `border`        | `#30363d` | Card borders, dividers         |

### Typography

| Role            | Font                | Size  | Weight |
|-----------------|---------------------|-------|--------|
| App Title       | Segoe UI / Inter    | 20px  | Bold   |
| Section Header  | Segoe UI            | 13px  | Bold   |
| Body / Table    | Segoe UI            | 11px  | Normal |
| Badge / Label   | Segoe UI            | 10px  | Bold   |
| Stats Number    | Segoe UI            | 24px  | Bold   |

---

## 🖼️ Screen Layout

### Full Window Layout (1100 × 700 px)

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER BAR                                                 │
│  🛡️ VECTOR Risk Detection      [Upload CSV]  [Export]        │
├──────────────┬──────────────────────────────────────────────┤
│              │  STATS CARDS ROW                             │
│  SIDEBAR     │  [ Total ] [ Critical ] [ High ] [ Low ]     │
│              ├──────────────────────────────────────────────┤
│  • Dashboard │                                              │
│  • History   │  DATA TABLE (main content area)              │
│  • Settings  │  Row | Cust ID | Score | Category | Drivers  │
│              │  ─────────────────────────────────────────── │
│  ─────────── │  (color-coded rows, scrollable)              │
│  Model Status│                                              │
│  ✅ Loaded   │                                              │
│              ├──────────────────────────────────────────────┤
│              │  STATUS BAR — file name, row count, time     │
└──────────────┴──────────────────────────────────────────────┘
```

---

## 🧩 UI Components (Detailed)

### 1. Header Bar
- App logo (shield icon) + title "**VECTOR Risk Detection**" on the left
- **Upload CSV** button (blue, rounded, with upload icon)
- **Export Results** button (outlined style, with download icon)

### 2. Sidebar Navigation
- **Dashboard** — current view (results table)
- **History** — previously loaded files (future feature, greyed out)
- **Settings** — model path config (future feature, greyed out)
- Divider below nav items
- **Model Status** indicator:
  - ✅ Green dot + "Model Loaded" when `risk_model.pkl` is found
  - ❌ Red dot + "Model Missing" with a "Train Model" button

### 3. Stats Cards Row (4 cards)
Each card shows a large bold number + small label with a colored left border:

| Card          | Color  | Value Source                          |
|---------------|--------|---------------------------------------|
| Total Records | Blue   | `len(df)`                             |
| Critical Risk | Red    | Count of `Risk Category == Critical`  |
| High Risk     | Orange | Count of `Risk Category == High`      |
| Low Risk      | Green  | Count of `Risk Category == Low`       |

### 4. Data Table
- Columns: `#` · `Customer ID` · `Risk Score` · `Risk Category` · `Top Risk Drivers`
- Row color-coding per risk level (subtle background tints)
- **Risk Category** shown as a colored badge/pill (not plain text)
- **Risk Score** shown as a mini progress bar + number (e.g., `▓▓▓▓░ 0.8312`)
- Alternating row shading for readability
- Horizontal + vertical scrollbars
- Click a row → show a **Detail Popup** with the full signal breakdown

### 5. Progress / Loading Overlay
- When CSV is being processed: centered loading spinner
- Text: "Analyzing X records..."
- Non-freezing — uses Python threading so the UI stays responsive

### 6. Status Bar (Bottom)
- Left: File name of loaded CSV
- Center: Total rows processed + time taken
- Right: App version / build info

### 7. Empty State
- When no CSV is loaded: centered placeholder with:
  - Large upload cloud icon
  - Text: "Upload a CSV file to begin risk analysis"
  - A large "Upload CSV" call-to-action button

---

## ⚙️ Technical Implementation Plan

### Phase 1 — Setup
- [ ] Add `customtkinter>=5.2.0` to `requirements.txt`

### Phase 2 — Rewrite `app/gui_app.py`
- [ ] 2.1 Initialize CustomTkinter app with dark theme
- [ ] 2.2 Build Header Bar (logo, title, Upload/Export buttons)
- [ ] 2.3 Build Sidebar (nav items + Model Status widget)
- [ ] 2.4 Build Stats Cards row (4 animated cards)
- [ ] 2.5 Build Data Table (scrollable, color-coded rows)
- [ ] 2.6 Build Risk Category badge renderer
- [ ] 2.7 Build Loading Overlay (threaded — no UI freeze)
- [ ] 2.8 Build Empty State placeholder
- [ ] 2.9 Build Status Bar
- [ ] 2.10 Rewire all logic (upload_csv, export_results, populate_table, update_stats)

### Phase 3 — Polish
- [ ] 3.1 Hover effects on buttons and table rows
- [ ] 3.2 Animate stats card numbers on data load (count-up effect)
- [ ] 3.3 Smooth transition between empty state and data table
- [ ] 3.4 Tooltips on Risk Drivers column (hover to see full text)

### Phase 4 — Build & Test
- [ ] 4.1 Test: `python app/gui_app.py` — confirm window opens
- [ ] 4.2 Upload `DATA/Base.csv` — confirm table populates with correct colors
- [ ] 4.3 Test Export Results — confirm CSV saves correctly
- [ ] 4.4 Rebuild `.exe` via `build/build_exe.bat`
- [ ] 4.5 Test the standalone `.exe` (double-click, no terminal)

---

## 📦 Dependency Change

### Add to `requirements.txt`:
```
customtkinter>=5.2.0
```

> **Why CustomTkinter?**  
> Built directly on top of Tkinter — no new system dependencies.  
> Supports dark mode natively, provides modern rounded widgets (buttons, frames, scrollbars),  
> and is PyInstaller-compatible — the `.exe` build works without any spec changes.

---

## 🔄 Workflow: From Plan to Working .exe

```
Step 1 → pip install -r requirements.txt        (adds customtkinter)
Step 2 → Edit app/gui_app.py                    (UI rewrite per plan above)
Step 3 → python app/gui_app.py                  (test live — no .exe needed)
Step 4 → Upload DATA/Base.csv in the app        (verify table, colors, stats)
Step 5 → build\build_exe.bat                    (repackage into .exe)
Step 6 → dist\RiskDetector.exe                  (test the final standalone .exe)
```

---

## ✅ Success Criteria

| Criteria                             | Pass Condition                                        |
|--------------------------------------|-------------------------------------------------------|
| App launches without errors          | Window opens within 3 seconds                         |
| Dark theme is consistent             | All widgets match the color palette                   |
| CSV loads without UI freeze          | Spinner shown; table fills after processing           |
| Stats cards update correctly         | Numbers match actual data counts                      |
| Row colors match risk categories     | Critical=red, High=orange, Medium=yellow, Low=green   |
| Export works                         | CSV saved with correct columns                        |
| `.exe` runs without Python installed | Double-click launches the app independently           |

---

## 🚀 Next Steps

1. **Review this plan** — check the layout and component list
2. **Say "execute"** — the actual code will be written to `app/gui_app.py`
3. Follow the 6-step workflow above to test and build the final `.exe`

---

*Plan created: 2026-08-13 | Project: VECTOR Risk Detection Desktop App*
