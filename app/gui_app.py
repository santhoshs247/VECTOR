import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import tkinter as tk
import pandas as pd
import os
import sys
import threading
import time
import json
import subprocess
from datetime import datetime, timedelta

# Ensure parent directory is in sys.path so 'app.risk_engine' works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.risk_engine import RiskEngine
except ImportError:
    from risk_engine import RiskEngine

try:
    from app.pdf_parser import PDFRiskEngine
except ImportError:
    try:
        from pdf_parser import PDFRiskEngine
    except ImportError:
        PDFRiskEngine = None

# ─────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULT_DIR = os.path.join(BASE_DIR, 'RESULT')
AUDIT_FILE = os.path.join(RESULT_DIR, 'audit_history.json')
MODEL_DIR = os.path.join(BASE_DIR, 'model')
TRAIN_SCRIPT = os.path.join(MODEL_DIR, 'train_model.py')

# ─────────────────────────────────────────────────────────
# CustomTkinter global config
# ─────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ═════════════════════════════════════════════════════════
# Feature 7: Tooltip helper class
# ═════════════════════════════════════════════════════════
class ToolTip:
    """Floating tooltip that appears after a hover delay."""

    def __init__(self, widget, delay=400):
        self.widget = widget
        self.delay = delay
        self.tip_window = None
        self._after_id = None
        self._text = ""

    def show(self, text, x, y):
        self._text = text
        self._cancel()
        self._after_id = self.widget.after(self.delay, lambda: self._display(x, y))

    def _display(self, x, y):
        if self.tip_window or not self._text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x + 16}+{y + 10}")
        tw.configure(bg="#1c2128")

        frame = tk.Frame(tw, bg="#1c2128", bd=1, relief="solid",
                         highlightbackground="#30363d", highlightthickness=1)
        frame.pack()

        label = tk.Label(
            frame, text=self._text,
            font=('Segoe UI', 9),
            fg="#e6edf3", bg="#1c2128",
            padx=10, pady=6,
            wraplength=360, justify='left'
        )
        label.pack()

    def hide(self):
        self._cancel()
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def _cancel(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None


# ═════════════════════════════════════════════════════════
# Main Application
# ═════════════════════════════════════════════════════════
class RiskApp(ctk.CTk):
    # ── color palette ──
    COLORS = {
        "bg_primary":    "#0d1117",
        "bg_secondary":  "#161b22",
        "bg_tertiary":   "#21262d",
        "accent_blue":   "#2f81f7",
        "accent_hover":  "#388bfd",
        "accent_purple": "#bc8cff",
        "text_primary":  "#e6edf3",
        "text_muted":    "#8b949e",
        "critical_bg":   "#4a1f28",
        "critical_fg":   "#ff7b72",
        "high_bg":       "#4a2b1f",
        "high_fg":       "#ffa657",
        "medium_bg":     "#4a431f",
        "medium_fg":     "#e3b341",
        "low_bg":        "#1b382b",
        "low_fg":        "#56d364",
        "border":        "#30363d",
        "hover_row":     "#292e36",
    }

    def __init__(self):
        super().__init__()
        self.title("VECTOR \u2014 Risk & Fraud Detection System")
        self.geometry("1180x720")
        self.minsize(1000, 650)
        self.configure(fg_color=self.COLORS["bg_primary"])

        # ── state ──
        self.engine = RiskEngine()
        self.pdf_engine = PDFRiskEngine() if PDFRiskEngine else None
        self.current_data = None
        self.current_filename = "No file loaded"
        self.active_page = "dashboard"
        self._hover_item = None
        self._tooltip = None

        # ── dashboard tab state ──
        self.active_dash_tab = "table"
        self.dash_tab_content = None

        # ── filter state ──
        self.filter_category = "All"
        self.filter_score_min = 0.0
        self.filter_score_max = 1.0
        self.filter_search = ""
        self.filter_sort = "Row #"

        # ── history filter state ──
        self.hist_time_range = "All Time"
        self.hist_sort_desc = True  # newest first

        # ── build UI ──
        self._setup_styles()
        self._build_header()
        self._build_main_area()
        self._build_status_bar()
        self._show_page("dashboard")

    # ─────────────────────────────────────────────────────
    # ttk Treeview styles
    # ─────────────────────────────────────────────────────
    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(
            "Treeview",
            background=self.COLORS["bg_primary"],
            foreground=self.COLORS["text_primary"],
            fieldbackground=self.COLORS["bg_primary"],
            rowheight=34, borderwidth=0,
            font=('Segoe UI', 10)
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.COLORS["bg_secondary"],
            foreground=self.COLORS["text_primary"],
            font=('Segoe UI', 10, 'bold'),
            borderwidth=0, relief='flat'
        )
        self.style.map(
            "Treeview",
            background=[('selected', self.COLORS["accent_blue"])],
            foreground=[('selected', '#ffffff')]
        )
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    # ─────────────────────────────────────────────────────
    # HEADER BAR
    # ─────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.COLORS["bg_secondary"], height=64,
                              corner_radius=0, border_width=1, border_color=self.COLORS["border"])
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", padx=20, pady=8)
        ctk.CTkLabel(brand, text="\U0001f6e1\ufe0f  VECTOR  |  Risk & Fraud Detection",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(brand, text="Real-time Behavioral Analytics & XGBoost ML Scoring Engine",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w")

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right", padx=20, pady=12)

        self.export_btn = ctk.CTkButton(
            btn_box, text="\U0001f4e5  Export Results",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=self.COLORS["bg_tertiary"], hover_color="#30363d",
            text_color=self.COLORS["text_primary"],
            corner_radius=8, height=36, width=160,
            command=self.export_results
        )
        self.export_btn.pack(side="right", padx=6)

        self.upload_btn = ctk.CTkButton(
            btn_box, text="\U0001f4c2  Upload Data (CSV/PDF)",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=self.COLORS["accent_blue"], hover_color=self.COLORS["accent_hover"],
            text_color="#ffffff",
            corner_radius=8, height=36, width=200,
            command=self.upload_data
        )
        self.upload_btn.pack(side="right", padx=6)

    # ─────────────────────────────────────────────────────
    # MAIN AREA
    # ─────────────────────────────────────────────────────
    def _build_main_area(self):
        self.main = ctk.CTkFrame(self, fg_color=self.COLORS["bg_primary"], corner_radius=0)
        self.main.pack(side="top", fill="both", expand=True)
        self._build_sidebar()
        self.workspace = ctk.CTkFrame(self.main, fg_color=self.COLORS["bg_primary"], corner_radius=0)
        self.workspace.pack(side="left", fill="both", expand=True, padx=16, pady=16)

    # ─────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self.main, fg_color=self.COLORS["bg_secondary"], width=210,
                               corner_radius=0, border_width=1, border_color=self.COLORS["border"])
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="NAVIGATION",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", padx=18, pady=(18, 8))

        self.nav_buttons = {}
        for label, key in [("\U0001f4ca  Dashboard", "dashboard"),
                           ("\U0001f4dc  Audit History", "history"),
                           ("\u2699\ufe0f  Model Settings", "settings")]:
            btn = ctk.CTkButton(
                sidebar, text=label,
                font=ctk.CTkFont("Segoe UI", 12),
                fg_color="transparent", hover_color=self.COLORS["bg_tertiary"],
                text_color=self.COLORS["text_muted"],
                anchor="w", height=38, corner_radius=6,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        ctk.CTkFrame(sidebar, fg_color=self.COLORS["border"], height=1).pack(fill="x", padx=14, pady=16)

        status_card = ctk.CTkFrame(sidebar, fg_color=self.COLORS["bg_tertiary"], corner_radius=10)
        status_card.pack(side="bottom", fill="x", padx=12, pady=16)
        ctk.CTkLabel(status_card, text="ENGINE STATUS",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", padx=12, pady=(10, 2))

        if self.engine.model is not None:
            status_text, status_color = "\U0001f7e2  XGBoost Model Loaded", self.COLORS["low_fg"]
        else:
            status_text, status_color = "\U0001f534  Model File Missing", self.COLORS["critical_fg"]

        ctk.CTkLabel(status_card, text=status_text,
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=status_color).pack(anchor="w", padx=12, pady=(0, 2))
        feat_count = len(self.engine.feature_columns) if self.engine.feature_columns else 0
        ctk.CTkLabel(status_card, text=f"Features: {feat_count} signals",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", padx=12, pady=(0, 10))

    # ─────────────────────────────────────────────────────
    # STATUS BAR
    # ─────────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, fg_color=self.COLORS["bg_secondary"], height=30,
                           corner_radius=0, border_width=1, border_color=self.COLORS["border"])
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        self.status_lbl = ctk.CTkLabel(bar, text="System Ready. Upload CSV dataset to analyze.",
                                       font=ctk.CTkFont("Segoe UI", 9),
                                       text_color=self.COLORS["text_muted"])
        self.status_lbl.pack(side="left", padx=16)
        self.file_info_lbl = ctk.CTkLabel(bar, text="No Dataset",
                                           font=ctk.CTkFont("Segoe UI", 9),
                                           text_color=self.COLORS["text_muted"])
        self.file_info_lbl.pack(side="right", padx=16)

    # ─────────────────────────────────────────────────────
    # PAGE NAVIGATION
    # ─────────────────────────────────────────────────────
    def _show_page(self, page_key):
        self.active_page = page_key
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=self.COLORS["accent_blue"], text_color="#ffffff",
                              font=ctk.CTkFont("Segoe UI", 12, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=self.COLORS["text_muted"],
                              font=ctk.CTkFont("Segoe UI", 12))
        for widget in self.workspace.winfo_children():
            widget.destroy()
        if page_key == "dashboard":
            self._build_dashboard_page()
        elif page_key == "history":
            self._build_history_page()
        elif page_key == "settings":
            self._build_settings_page()

    # ═════════════════════════════════════════════════════
    #  PAGE: DASHBOARD
    # ═════════════════════════════════════════════════════
    def _build_dashboard_page(self):
        self._build_stats_cards()
        self._build_dash_tabs()
        self.dash_tab_content = ctk.CTkFrame(self.workspace, fg_color=self.COLORS["bg_primary"], corner_radius=0)
        self.dash_tab_content.pack(fill="both", expand=True)
        self._show_dash_tab(self.active_dash_tab)

    # ─────────────────────────────────────────────────────
    #  STATS CARDS
    # ─────────────────────────────────────────────────────
    def _build_stats_cards(self):
        stats_row = ctk.CTkFrame(self.workspace, fg_color="transparent")
        stats_row.pack(fill="x")
        self.card_labels = {}
        cards = [
            ("TOTAL RECORDS",    "total",    self.COLORS["accent_blue"]),
            ("CRITICAL RISK",    "critical", self.COLORS["critical_fg"]),
            ("HIGH RISK",        "high",     self.COLORS["high_fg"]),
            ("LOW / MEDIUM RISK","low",      self.COLORS["low_fg"]),
        ]
        for title, key, accent in cards:
            card = ctk.CTkFrame(stats_row, fg_color=self.COLORS["bg_secondary"], corner_radius=10,
                                border_width=1, border_color=self.COLORS["border"])
            card.pack(side="left", fill="both", expand=True, padx=4)
            ctk.CTkFrame(card, fg_color=accent, height=4, corner_radius=0).pack(fill="x", side="top")
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=10)
            ctk.CTkLabel(inner, text=title, font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=self.COLORS["text_muted"]).pack(anchor="w")
            val = self._compute_stat(key) if self.current_data is not None else "0"
            val_lbl = ctk.CTkLabel(inner, text=val, font=ctk.CTkFont("Segoe UI", 22, "bold"),
                                   text_color=self.COLORS["text_primary"])
            val_lbl.pack(anchor="w", pady=(2, 0))
            self.card_labels[key] = val_lbl

    def _compute_stat(self, key):
        if self.current_data is None:
            return "0"
        df = self.current_data
        if key == "total":   return str(len(df))
        elif key == "critical": return str(int((df['Risk Category'] == 'Critical').sum()))
        elif key == "high":  return str(int((df['Risk Category'] == 'High').sum()))
        elif key == "low":   return str(int(((df['Risk Category'] == 'Low') | (df['Risk Category'] == 'Medium')).sum()))
        return "0"

    def _animate_stats(self):
        if self.current_data is None:
            return
        targets = {key: int(self._compute_stat(key)) for key in self.card_labels}
        steps, duration_ms = 30, 600
        interval = duration_ms // steps
        def _step(step_i):
            if step_i > steps:
                for key, lbl in self.card_labels.items():
                    lbl.configure(text=f"{targets[key]:,}")
                return
            t = 1 - (1 - step_i / steps) ** 3
            for key, lbl in self.card_labels.items():
                lbl.configure(text=f"{int(targets[key] * t):,}")
            self.after(interval, _step, step_i + 1)
        _step(0)

    # ─────────────────────────────────────────────────────
    #  DASHBOARD TAB BAR
    # ─────────────────────────────────────────────────────
    def _build_dash_tabs(self):
        tab_bar = ctk.CTkFrame(self.workspace, fg_color=self.COLORS["bg_secondary"],
                               corner_radius=10, border_width=1, border_color=self.COLORS["border"], height=44)
        tab_bar.pack(fill="x", pady=(10, 0))
        tab_bar.pack_propagate(False)
        self._dash_tab_btns = {}
        for label, key in [("\U0001f4cb  Results Table", "table"),
                           ("\U0001f4ca  Risk Breakdown", "breakdown"),
                           ("\U0001f3c6  Top 10 High Risk", "top10")]:
            btn = ctk.CTkButton(tab_bar, text=label, font=ctk.CTkFont("Segoe UI", 11, "bold"),
                fg_color="transparent", hover_color=self.COLORS["bg_tertiary"],
                text_color=self.COLORS["text_muted"], corner_radius=8, height=32,
                command=lambda k=key: self._show_dash_tab(k))
            btn.pack(side="left", padx=(6, 0), pady=6)
            self._dash_tab_btns[key] = btn
        self._update_tab_btn_states()

    def _update_tab_btn_states(self):
        for key, btn in self._dash_tab_btns.items():
            if key == self.active_dash_tab:
                btn.configure(fg_color=self.COLORS["accent_blue"], text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=self.COLORS["text_muted"])

    def _show_dash_tab(self, tab_key):
        self.active_dash_tab = tab_key
        if hasattr(self, '_dash_tab_btns'):
            self._update_tab_btn_states()
        if self.dash_tab_content is None:
            return
        for w in self.dash_tab_content.winfo_children():
            w.destroy()
        if tab_key == "table":
            self._build_tab_table(self.dash_tab_content)
        elif tab_key == "breakdown":
            self._build_tab_breakdown(self.dash_tab_content)
        elif tab_key == "top10":
            self._build_tab_top10(self.dash_tab_content)

    # ─────────────────────────────────────────────────────
    #  TAB 1: RESULTS TABLE
    # ─────────────────────────────────────────────────────
    def _build_tab_table(self, parent):
        if self.current_data is None:
            self._show_empty_state_in(parent)
            return
        self._build_filter_bar(parent)
        self.content_frame = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_primary"], corner_radius=0)
        self.content_frame.pack(fill="both", expand=True, pady=(6, 0))
        self._show_table_view()

    def _build_filter_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_secondary"],
                           corner_radius=8, border_width=1, border_color=self.COLORS["border"], height=48)
        bar.pack(fill="x", pady=(8, 0))
        bar.pack_propagate(False)
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=6)
        ctk.CTkLabel(inner, text="Category:", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self._flt_cat_var = ctk.StringVar(value=self.filter_category)
        ctk.CTkOptionMenu(inner, variable=self._flt_cat_var,
                          values=["All", "\U0001f534 Critical", "\U0001f7e0 High", "\U0001f7e1 Medium", "\U0001f7e2 Low"],
                          font=ctk.CTkFont("Segoe UI", 10),
                          fg_color=self.COLORS["bg_tertiary"], button_color=self.COLORS["bg_tertiary"],
                          button_hover_color="#30363d", dropdown_fg_color=self.COLORS["bg_secondary"],
                          text_color=self.COLORS["text_primary"], width=120, height=28,
                          command=self._on_filter_change).pack(side="left", padx=(0, 14))
        ctk.CTkLabel(inner, text="Score Min:", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self._flt_min_lbl = ctk.CTkLabel(inner, text=f"{self.filter_score_min:.2f}",
                                          font=ctk.CTkFont("Segoe UI", 9),
                                          text_color=self.COLORS["accent_blue"], width=32)
        self._flt_min_lbl.pack(side="left")
        self._flt_min_slider = ctk.CTkSlider(inner, from_=0.0, to=1.0, number_of_steps=100,
                                              width=90, height=16, fg_color=self.COLORS["bg_tertiary"],
                                              progress_color=self.COLORS["accent_blue"],
                                              button_color=self.COLORS["accent_blue"],
                                              button_hover_color=self.COLORS["accent_hover"],
                                              command=self._on_min_slider)
        self._flt_min_slider.set(self.filter_score_min)
        self._flt_min_slider.pack(side="left", padx=(2, 12))
        ctk.CTkLabel(inner, text="Max:", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self._flt_max_lbl = ctk.CTkLabel(inner, text=f"{self.filter_score_max:.2f}",
                                          font=ctk.CTkFont("Segoe UI", 9),
                                          text_color=self.COLORS["accent_blue"], width=32)
        self._flt_max_lbl.pack(side="left")
        self._flt_max_slider = ctk.CTkSlider(inner, from_=0.0, to=1.0, number_of_steps=100,
                                              width=90, height=16, fg_color=self.COLORS["bg_tertiary"],
                                              progress_color=self.COLORS["accent_blue"],
                                              button_color=self.COLORS["accent_blue"],
                                              button_hover_color=self.COLORS["accent_hover"],
                                              command=self._on_max_slider)
        self._flt_max_slider.set(self.filter_score_max)
        self._flt_max_slider.pack(side="left", padx=(2, 14))
        ctk.CTkLabel(inner, text="Search ID:", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self._flt_search_var = ctk.StringVar(value=self.filter_search)
        ctk.CTkEntry(inner, textvariable=self._flt_search_var, placeholder_text="CUST-...",
                     font=ctk.CTkFont("Segoe UI", 10), fg_color=self.COLORS["bg_tertiary"],
                     border_color=self.COLORS["border"], text_color=self.COLORS["text_primary"],
                     width=110, height=28).pack(side="left", padx=(0, 14))
        self._flt_search_var.trace_add("write", lambda *a: self._on_filter_change())
        ctk.CTkLabel(inner, text="Sort:", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self._flt_sort_var = ctk.StringVar(value=self.filter_sort)
        ctk.CTkOptionMenu(inner, variable=self._flt_sort_var,
                          values=["Row #", "Score \u2193", "Score \u2191", "Category"],
                          font=ctk.CTkFont("Segoe UI", 10),
                          fg_color=self.COLORS["bg_tertiary"], button_color=self.COLORS["bg_tertiary"],
                          button_hover_color="#30363d", dropdown_fg_color=self.COLORS["bg_secondary"],
                          text_color=self.COLORS["text_primary"], width=110, height=28,
                          command=self._on_filter_change).pack(side="left", padx=(0, 10))
        ctk.CTkButton(inner, text="\u21ba Reset", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                      fg_color=self.COLORS["bg_tertiary"], hover_color="#30363d",
                      text_color=self.COLORS["text_muted"], corner_radius=6, height=28, width=68,
                      command=self._reset_filters).pack(side="left")
        self._flt_count_lbl = ctk.CTkLabel(inner, text="", font=ctk.CTkFont("Segoe UI", 9),
                                            text_color=self.COLORS["text_muted"])
        self._flt_count_lbl.pack(side="right", padx=(0, 4))

    def _on_min_slider(self, value):
        self.filter_score_min = round(value, 2)
        if self.filter_score_min > self.filter_score_max:
            self.filter_score_max = self.filter_score_min
            if hasattr(self, '_flt_max_slider'): self._flt_max_slider.set(self.filter_score_max)
        if hasattr(self, '_flt_min_lbl'): self._flt_min_lbl.configure(text=f"{self.filter_score_min:.2f}")
        if hasattr(self, '_flt_max_lbl'): self._flt_max_lbl.configure(text=f"{self.filter_score_max:.2f}")
        self._apply_filters()

    def _on_max_slider(self, value):
        self.filter_score_max = round(value, 2)
        if self.filter_score_max < self.filter_score_min:
            self.filter_score_min = self.filter_score_max
            if hasattr(self, '_flt_min_slider'): self._flt_min_slider.set(self.filter_score_min)
        if hasattr(self, '_flt_min_lbl'): self._flt_min_lbl.configure(text=f"{self.filter_score_min:.2f}")
        if hasattr(self, '_flt_max_lbl'): self._flt_max_lbl.configure(text=f"{self.filter_score_max:.2f}")
        self._apply_filters()

    def _on_filter_change(self, *_):
        if hasattr(self, '_flt_cat_var'): self.filter_category = self._flt_cat_var.get()
        if hasattr(self, '_flt_sort_var'): self.filter_sort = self._flt_sort_var.get()
        if hasattr(self, '_flt_search_var'): self.filter_search = self._flt_search_var.get().strip().lower()
        self._apply_filters()

    def _get_filtered_data(self):
        if self.current_data is None: return None
        df = self.current_data.copy()
        cat_map = {"\U0001f534 Critical": "Critical", "\U0001f7e0 High": "High", "\U0001f7e1 Medium": "Medium", "\U0001f7e2 Low": "Low"}
        if self.filter_category != "All":
            df = df[df['Risk Category'] == cat_map.get(self.filter_category, self.filter_category)]
        df = df[(df['Risk Score'] >= self.filter_score_min) & (df['Risk Score'] <= self.filter_score_max)]
        if self.filter_search and 'customer_id' in df.columns:
            df = df[df['customer_id'].astype(str).str.lower().str.contains(self.filter_search, na=False)]
        sort_map = {"Score \u2193": ("Risk Score", False), "Score \u2191": ("Risk Score", True), "Category": ("Risk Category", True)}
        if self.filter_sort in sort_map:
            col, asc = sort_map[self.filter_sort]
            df = df.sort_values(col, ascending=asc)
        return df

    def _apply_filters(self):
        if not hasattr(self, 'tree') or self.tree is None: return
        filtered = self._get_filtered_data()
        if filtered is None: return
        self._populate_table_with(filtered)
        total = len(self.current_data) if self.current_data is not None else 0
        shown = len(filtered)
        if hasattr(self, '_flt_count_lbl'):
            if shown < total: self._flt_count_lbl.configure(text=f"Showing {shown:,} of {total:,}")
            else: self._flt_count_lbl.configure(text=f"{total:,} records")

    def _reset_filters(self):
        self.filter_category = "All"
        self.filter_score_min = 0.0
        self.filter_score_max = 1.0
        self.filter_search = ""
        self.filter_sort = "Row #"
        if hasattr(self, '_flt_cat_var'):    self._flt_cat_var.set("All")
        if hasattr(self, '_flt_sort_var'):   self._flt_sort_var.set("Row #")
        if hasattr(self, '_flt_search_var'): self._flt_search_var.set("")
        if hasattr(self, '_flt_min_slider'): self._flt_min_slider.set(0.0)
        if hasattr(self, '_flt_max_slider'): self._flt_max_slider.set(1.0)
        if hasattr(self, '_flt_min_lbl'):    self._flt_min_lbl.configure(text="0.00")
        if hasattr(self, '_flt_max_lbl'):    self._flt_max_lbl.configure(text="1.00")
        self._apply_filters()

    # ─────────────────────────────────────────────────────
    #  TAB 2: RISK BREAKDOWN
    # ─────────────────────────────────────────────────────
    def _build_tab_breakdown(self, parent):
        if self.current_data is None:
            self._show_empty_state_in(parent)
            return
        df = self.current_data
        total = len(df)
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=self.COLORS["bg_tertiary"])
        scroll.pack(fill="both", expand=True, pady=(8, 0))
        ctk.CTkLabel(scroll, text="\U0001f4ca  Risk Distribution Summary", font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(scroll, text=f"Based on {total:,} analyzed records", font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 16))
        for display, cat, color, bg in [
            ("\U0001f534 Critical", "Critical", self.COLORS["critical_fg"], self.COLORS["critical_bg"]),
            ("\U0001f7e0 High",     "High",     self.COLORS["high_fg"],     self.COLORS["high_bg"]),
            ("\U0001f7e1 Medium",   "Medium",   self.COLORS["medium_fg"],   self.COLORS["medium_bg"]),
            ("\U0001f7e2 Low",      "Low",      self.COLORS["low_fg"],      self.COLORS["low_bg"]),
        ]:
            count = int((df['Risk Category'] == cat).sum())
            pct = (count / total) if total > 0 else 0
            card = ctk.CTkFrame(scroll, fg_color=self.COLORS["bg_secondary"], corner_radius=10,
                                border_width=1, border_color=self.COLORS["border"])
            card.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=20, pady=14)
            top_row = ctk.CTkFrame(inner, fg_color="transparent")
            top_row.pack(fill="x")
            ctk.CTkLabel(top_row, text=display, font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=color).pack(side="left")
            ctk.CTkLabel(top_row, text=f"{count:,} records", font=ctk.CTkFont("Segoe UI", 11),
                         text_color=self.COLORS["text_primary"]).pack(side="left", padx=(14, 0))
            ctk.CTkLabel(top_row, text=f"{pct:.1%}", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=color).pack(side="right")
            prog = ctk.CTkProgressBar(inner, height=12, corner_radius=6, fg_color=self.COLORS["bg_tertiary"], progress_color=color)
            prog.pack(fill="x", pady=(8, 0))
            prog.set(pct)
        if total > 0:
            stats_card = ctk.CTkFrame(scroll, fg_color=self.COLORS["bg_secondary"], corner_radius=10,
                                      border_width=1, border_color=self.COLORS["border"])
            stats_card.pack(fill="x", pady=(12, 4))
            si = ctk.CTkFrame(stats_card, fg_color="transparent")
            si.pack(fill="x", padx=20, pady=14)
            ctk.CTkLabel(si, text="SCORE STATISTICS", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 10))
            stat_row = ctk.CTkFrame(si, fg_color="transparent")
            stat_row.pack(fill="x")
            for label, val in [("Average Score", f"{df['Risk Score'].mean():.4f}"),
                                ("Highest Score", f"{df['Risk Score'].max():.4f}"),
                                ("Lowest Score",  f"{df['Risk Score'].min():.4f}")]:
                pill = ctk.CTkFrame(stat_row, fg_color=self.COLORS["bg_tertiary"], corner_radius=8)
                pill.pack(side="left", padx=(0, 10))
                ctk.CTkLabel(pill, text=label, font=ctk.CTkFont("Segoe UI", 8, "bold"),
                             text_color=self.COLORS["text_muted"]).pack(padx=14, pady=(8, 2))
                ctk.CTkLabel(pill, text=val, font=ctk.CTkFont("Segoe UI", 14, "bold"),
                             text_color=self.COLORS["accent_blue"]).pack(padx=14, pady=(0, 8))

    # ─────────────────────────────────────────────────────
    #  TAB 3: TOP 10 HIGH RISK
    # ─────────────────────────────────────────────────────
    def _build_tab_top10(self, parent):
        if self.current_data is None:
            self._show_empty_state_in(parent)
            return
        top10 = self.current_data.copy().nlargest(10, 'Risk Score').reset_index(drop=True)
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", pady=(8, 6))
        ctk.CTkLabel(hdr, text="\U0001f3c6  Top 10 Highest Risk Records", font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(side="left")
        ctk.CTkLabel(hdr, text="Sorted by Risk Score (highest first)", font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(10, 0))
        container = tk.Frame(parent, bg=self.COLORS["bg_primary"])
        container.pack(fill="both", expand=True)
        cols = ("Rank", "Customer ID", "Risk Score", "Risk Category", "Top Risk Drivers")
        top_tree = ttk.Treeview(container, columns=cols, show="headings", selectmode="browse")
        for col, w, anchor in [("Rank",60,"center"),("Customer ID",160,"w"),
                                ("Risk Score",160,"center"),("Risk Category",140,"center"),
                                ("Top Risk Drivers",400,"w")]:
            top_tree.heading(col, text=col if col != "Risk Score" else "Risk Probability")
            top_tree.column(col, width=w, anchor=anchor)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=top_tree.yview)
        top_tree.configure(yscrollcommand=v_scroll.set)
        top_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        for cat, bg, fg in [('Critical', self.COLORS["critical_bg"], self.COLORS["critical_fg"]),
                             ('High', self.COLORS["high_bg"], self.COLORS["high_fg"]),
                             ('Medium', self.COLORS["medium_bg"], self.COLORS["medium_fg"]),
                             ('Low', self.COLORS["low_bg"], self.COLORS["low_fg"])]:
            top_tree.tag_configure(cat, background=bg, foreground=fg)
        medal = ["\U0001f947", "\U0001f948", "\U0001f949"]
        cat_display_map = {'Critical':'\U0001f534 Critical','High':'\U0001f7e0 High','Medium':'\U0001f7e1 Medium','Low':'\U0001f7e2 Low'}
        for i, row in top10.iterrows():
            rank = i + 1
            score_val = row['Risk Score']
            bar_len = int(score_val * 10)
            score_str = f"{score_val:.4f}  {chr(9608)*bar_len}{chr(9617)*(10-bar_len)}"
            top_tree.insert("", "end",
                            values=(medal[i] if i < 3 else f"#{rank}",
                                    row.get('customer_id', f"CUST-{rank:05d}"),
                                    score_str,
                                    cat_display_map.get(row['Risk Category'], row['Risk Category']),
                                    row['Top Risk Drivers']),
                            tags=(row['Risk Category'],))

    # ─────────────────────────────────────────────────────
    #  EMPTY STATE
    # ─────────────────────────────────────────────────────
    def _show_empty_state_in(self, parent):
        box = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_secondary"], corner_radius=12,
                           border_width=1, border_color=self.COLORS["border"])
        box.pack(fill="both", expand=True, pady=(8, 0))
        center = ctk.CTkFrame(box, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(center, text="\U0001f4c2", font=ctk.CTkFont(size=52)).pack()
        ctk.CTkLabel(center, text="No CSV Dataset Loaded", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(pady=(12, 4))
        ctk.CTkLabel(center, text="Upload customer behavioral CSV data to run XGBoost risk prediction scoring.",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=self.COLORS["text_muted"]).pack(pady=(0, 18))
        ctk.CTkButton(center, text="Select Data File", font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=self.COLORS["accent_blue"], hover_color=self.COLORS["accent_hover"],
                      corner_radius=8, height=42, width=200, command=self.upload_data).pack()

    # ─────────────────────────────────────────────────────
    #  DATA TABLE (Tab 1)
    # ─────────────────────────────────────────────────────
    def _show_table_view(self):
        for w in self.content_frame.winfo_children(): w.destroy()
        container = tk.Frame(self.content_frame, bg=self.COLORS["bg_primary"])
        container.pack(fill="both", expand=True)
        columns = ("Row", "Customer ID", "Risk Score", "Risk Category", "Top Risk Drivers")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("Row", text="#")
        self.tree.heading("Customer ID", text="Customer ID")
        self.tree.heading("Risk Score", text="Risk Probability")
        self.tree.heading("Risk Category", text="Risk Category")
        self.tree.heading("Top Risk Drivers", text="Top Contributing Risk Drivers")
        self.tree.column("Row", width=50, anchor="center")
        self.tree.column("Customer ID", width=160, anchor="w")
        self.tree.column("Risk Score", width=150, anchor="center")
        self.tree.column("Risk Category", width=140, anchor="center")
        self.tree.column("Top Risk Drivers", width=400, anchor="w")
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure('Critical', background=self.COLORS["critical_bg"], foreground=self.COLORS["critical_fg"])
        self.tree.tag_configure('High', background=self.COLORS["high_bg"], foreground=self.COLORS["high_fg"])
        self.tree.tag_configure('Medium', background=self.COLORS["medium_bg"], foreground=self.COLORS["medium_fg"])
        self.tree.tag_configure('Low', background=self.COLORS["low_bg"], foreground=self.COLORS["low_fg"])
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<Double-1>", self._on_row_double_click)
        self._tooltip = ToolTip(self.tree)
        self._apply_filters()
        if self.current_data is not None and hasattr(self, '_flt_count_lbl'):
            self._flt_count_lbl.configure(text=f"{len(self.current_data):,} records")

    def _populate_table_with(self, df):
        if not hasattr(self, 'tree') or self.tree is None: return
        for item in self.tree.get_children(): self.tree.delete(item)
        cat_display_map = {'Critical':'\U0001f534 Critical','High':'\U0001f7e0 High','Medium':'\U0001f7e1 Medium','Low':'\U0001f7e2 Low'}
        for display_idx, (index, row) in enumerate(df.iterrows(), start=1):
            cust_id = row.get('customer_id', f"CUST-{index+1:05d}")
            score_val = row['Risk Score']
            bar_len = int(score_val * 10)
            score_str = f"{score_val:.4f}  {chr(9608)*bar_len}{chr(9617)*(10-bar_len)}"
            category = row['Risk Category']
            self.tree.insert("", "end", values=(display_idx, cust_id, score_str,
                             cat_display_map.get(category, category), row['Top Risk Drivers']), tags=(category,))

    def _on_tree_motion(self, event):
        item = self.tree.identify_row(event.y)
        if item != self._hover_item:
            if self._hover_item:
                tags = self.tree.item(self._hover_item, 'tags')
                if tags: self.tree.item(self._hover_item, tags=tags)
            self._hover_item = item
        col = self.tree.identify_column(event.x)
        if col == '#5' and item:
            values = self.tree.item(item, 'values')
            if values and len(values) >= 5: self._tooltip.show(values[4], event.x_root, event.y_root)
            else: self._tooltip.hide()
        else:
            if self._tooltip: self._tooltip.hide()

    def _on_tree_leave(self, _event):
        self._hover_item = None
        if self._tooltip: self._tooltip.hide()

    def _on_row_double_click(self, event):
        selected = self.tree.selection()
        if not selected or self.current_data is None: return
        vals = self.tree.item(selected[0], "values")
        row_idx = int(vals[0]) - 1
        if 0 <= row_idx < len(self.current_data):
            self._open_detail_modal(self.current_data.iloc[row_idx])

    def _open_detail_modal(self, record):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Risk Detail \u2014 {record.get('customer_id', 'Customer')}")
        modal.geometry("560x440")
        modal.configure(fg_color=self.COLORS["bg_secondary"])
        modal.transient(self)
        modal.grab_set()
        modal.after(10, modal.lift)
        hdr = ctk.CTkFrame(modal, fg_color=self.COLORS["bg_tertiary"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"Customer Risk Profile: {record.get('customer_id', 'N/A')}",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(anchor="w", padx=20, pady=14)
        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)
        category = record.get('Risk Category', 'N/A')
        score = record.get('Risk Score', 0.0)
        cat_color = {"Critical": self.COLORS["critical_fg"], "High": self.COLORS["high_fg"],
                     "Medium": self.COLORS["medium_fg"], "Low": self.COLORS["low_fg"]
                     }.get(category, self.COLORS["text_primary"])
        for lbl_text, val_text in [("Risk Score Probability:", f"{score:.6f}"),
                                   ("Risk Severity Rating:", category),
                                   ("Top Behavioral Drivers:", record.get('Top Risk Drivers', 'N/A'))]:
            row_f = ctk.CTkFrame(body, fg_color="transparent")
            row_f.pack(fill="x", pady=8)
            ctk.CTkLabel(row_f, text=lbl_text, font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=self.COLORS["text_muted"], width=180, anchor="w").pack(side="left")
            color = cat_color if lbl_text.startswith("Risk Severity") else self.COLORS["text_primary"]
            ctk.CTkLabel(row_f, text=val_text, font=ctk.CTkFont("Segoe UI", 11), text_color=color,
                         wraplength=300, justify="left", anchor="w").pack(side="left", fill="x", expand=True)
        bar_frame = ctk.CTkFrame(body, fg_color="transparent")
        bar_frame.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(bar_frame, text="Score Gauge:", font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w")
        prog = ctk.CTkProgressBar(bar_frame, width=300, height=14, corner_radius=6,
                                  fg_color=self.COLORS["bg_tertiary"], progress_color=cat_color)
        prog.pack(anchor="w", pady=(6, 0))
        prog.set(score)
        ctk.CTkButton(modal, text="Close Inspector", font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      fg_color=self.COLORS["accent_blue"], hover_color=self.COLORS["accent_hover"],
                      corner_radius=8, height=36, width=160, command=modal.destroy).pack(pady=18)

    # ═════════════════════════════════════════════════════
    #  Feature 4: LOADING OVERLAY
    # ═════════════════════════════════════════════════════
    def _show_loading_overlay(self, record_count=0):
        self.overlay = ctk.CTkFrame(self.workspace, fg_color=("rgba(0,0,0,0.5)", "#0d1117"))
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        center = ctk.CTkFrame(self.overlay, fg_color=self.COLORS["bg_secondary"],
                              corner_radius=16, border_width=1, border_color=self.COLORS["border"])
        center.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(center, fg_color="transparent")
        inner.pack(padx=40, pady=30)
        ctk.CTkLabel(inner, text="\u26a1", font=ctk.CTkFont(size=36)).pack()
        msg = f"Analyzing {record_count:,} records..." if record_count else "Processing dataset..."
        ctk.CTkLabel(inner, text=msg, font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(pady=(10, 4))
        ctk.CTkLabel(inner, text="Running XGBoost ML inference engine...",
                     font=ctk.CTkFont("Segoe UI", 10), text_color=self.COLORS["text_muted"]).pack(pady=(0, 14))
        self.loading_bar = ctk.CTkProgressBar(inner, width=280, height=10, corner_radius=5,
                                              fg_color=self.COLORS["bg_tertiary"],
                                              progress_color=self.COLORS["accent_blue"], mode="indeterminate")
        self.loading_bar.pack()
        self.loading_bar.start()

    def _hide_loading_overlay(self):
        if hasattr(self, 'overlay') and self.overlay:
            if hasattr(self, 'loading_bar'): self.loading_bar.stop()
            self.overlay.destroy()
            self.overlay = None

    # ═════════════════════════════════════════════════════
    #  CSV & PDF UPLOAD & PROCESSING
    # ═════════════════════════════════════════════════════
    def upload_data(self):
        file_path = filedialog.askopenfilename(
            title="Select Customer Data (CSV or PDF)",
            filetypes=(("Supported Files", "*.csv *.pdf"), ("CSV Files", "*.csv"),
                       ("PDF Statements", "*.pdf"), ("All Files", "*.*")))
        if not file_path: return
        is_pdf = file_path.lower().endswith('.pdf')
        if is_pdf:
            if self.pdf_engine is None or self.pdf_engine.model is None:
                messagebox.showerror("Model Error", "PDF model not loaded.\nPlease run model/train_pdf_model.py first.")
                return
        else:
            if self.engine.model is None:
                messagebox.showerror("Model Error", "Risk model file (risk_model.pkl) not found.\nPlease run model/train_model.py first.")
                return
        self.current_filename = os.path.basename(file_path)
        self.status_lbl.configure(text=f"\u26a1 Loading '{self.current_filename}'...")
        self.upload_btn.configure(state="disabled")
        if self.active_page != "dashboard": self._show_page("dashboard")
        self._show_loading_overlay()
        if is_pdf:
            threading.Thread(target=self._process_pdf_thread, args=(file_path,), daemon=True).start()
        else:
            threading.Thread(target=self._process_csv_thread, args=(file_path,), daemon=True).start()

    def _process_pdf_thread(self, file_path):
        start_time = time.time()
        try:
            scored_df = self.pdf_engine.predict(file_path)
            elapsed = time.time() - start_time
            self.after(0, lambda: self._update_overlay_count(1))
            self.after(0, self._on_processing_complete, scored_df, elapsed)
        except Exception as e:
            self.after(0, self._on_processing_error, str(e))

    def _process_csv_thread(self, file_path):
        start_time = time.time()
        try:
            df = pd.read_csv(file_path, nrows=1000)
            if 'customer_id' not in df.columns:
                df['customer_id'] = [f"CUST-{str(i+1).zfill(5)}" for i in range(len(df))]
            self.after(0, lambda: self._update_overlay_count(len(df)))
            scored_df = self.engine.predict(df)
            elapsed = time.time() - start_time
            self.after(0, self._on_processing_complete, scored_df, elapsed)
        except Exception as e:
            self.after(0, self._on_processing_error, str(e))

    def _update_overlay_count(self, count):
        pass

    def _on_processing_complete(self, scored_df, elapsed):
        self.current_data = scored_df
        self.upload_btn.configure(state="normal")
        self._hide_loading_overlay()
        self._show_page("dashboard")
        self._animate_stats()
        total = len(self.current_data)
        self.status_lbl.configure(text=f"\u2705 Analysis complete: Scored {total:,} records in {elapsed:.2f}s")
        self.file_info_lbl.configure(text=f"Loaded: {self.current_filename} ({total:,} records)")
        self._save_audit_entry(elapsed)

    def _on_processing_error(self, err_msg):
        self.upload_btn.configure(state="normal")
        self._hide_loading_overlay()
        self.status_lbl.configure(text="\u274c Error processing file.")
        messagebox.showerror("Processing Error", f"Failed to process CSV file:\n{err_msg}")

    # ═════════════════════════════════════════════════════
    #  EXPORT RESULTS
    # ═════════════════════════════════════════════════════
    def export_results(self):
        if self.current_data is None:
            messagebox.showinfo("Export Info", "No analyzed data available to export. Upload a dataset first.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
            title="Save Scored Results CSV As", initialfile=f"Risk_Results_{self.current_filename}")
        if file_path:
            try:
                self.current_data.to_csv(file_path, index=False)
                messagebox.showinfo("Export Success", f"Results exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save file:\n{str(e)}")

    # ═════════════════════════════════════════════════════
    #  Feature 2: AUDIT HISTORY
    # ═════════════════════════════════════════════════════
    def _load_audit_history(self):
        if os.path.exists(AUDIT_FILE):
            try:
                with open(AUDIT_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_audit_entry(self, elapsed):
        os.makedirs(RESULT_DIR, exist_ok=True)
        history = self._load_audit_history()
        df = self.current_data
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": self.current_filename,
            "total": int(len(df)),
            "critical": int((df['Risk Category'] == 'Critical').sum()),
            "high": int((df['Risk Category'] == 'High').sum()),
            "medium": int((df['Risk Category'] == 'Medium').sum()),
            "low": int((df['Risk Category'] == 'Low').sum()),
            "elapsed_seconds": round(elapsed, 2)
        }
        history.insert(0, entry)
        with open(AUDIT_FILE, 'w') as f:
            json.dump(history, f, indent=2)

    # ═════════════════════════════════════════════════════
    #  PAGE: AUDIT HISTORY
    # ═════════════════════════════════════════════════════
    def _build_history_page(self):
        hdr = ctk.CTkFrame(self.workspace, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(hdr, text="\U0001f4dc  Audit History", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(side="left")
        ctk.CTkLabel(hdr, text="Past analysis sessions", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(12, 0))
        filter_bar = ctk.CTkFrame(self.workspace, fg_color=self.COLORS["bg_secondary"],
                                  corner_radius=8, border_width=1, border_color=self.COLORS["border"], height=48)
        filter_bar.pack(fill="x", pady=(0, 8))
        filter_bar.pack_propagate(False)
        flt = ctk.CTkFrame(filter_bar, fg_color="transparent")
        flt.pack(fill="both", expand=True, padx=12, pady=8)
        ctk.CTkLabel(flt, text="Time Range:", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(0, 6))
        self._hist_range_var = ctk.StringVar(value=self.hist_time_range)
        ctk.CTkOptionMenu(flt, variable=self._hist_range_var,
                          values=["All Time", "Today", "Last 7 Days", "Last 30 Days"],
                          font=ctk.CTkFont("Segoe UI", 10),
                          fg_color=self.COLORS["bg_tertiary"], button_color=self.COLORS["bg_tertiary"],
                          button_hover_color="#30363d", dropdown_fg_color=self.COLORS["bg_secondary"],
                          text_color=self.COLORS["text_primary"], width=140, height=28,
                          command=self._on_hist_filter_change).pack(side="left", padx=(0, 14))
        self._hist_sort_btn = ctk.CTkButton(
            flt, text="\U0001f550 Newest First" if self.hist_sort_desc else "\U0001f550 Oldest First",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
            fg_color=self.COLORS["bg_tertiary"], hover_color="#30363d",
            text_color=self.COLORS["text_primary"], corner_radius=6, height=28, width=130,
            command=self._toggle_hist_sort)
        self._hist_sort_btn.pack(side="left", padx=(0, 10))
        ctk.CTkButton(flt, text="\U0001f5d1  Clear History", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                      fg_color="#4a1f28", hover_color="#6b2c38", text_color=self.COLORS["critical_fg"],
                      corner_radius=6, height=28, width=130, command=self._clear_history).pack(side="right")
        self._hist_count_lbl = ctk.CTkLabel(flt, text="", font=ctk.CTkFont("Segoe UI", 9),
                                             text_color=self.COLORS["text_muted"])
        self._hist_count_lbl.pack(side="right", padx=(0, 12))
        self._hist_list_container = ctk.CTkFrame(self.workspace, fg_color="transparent", corner_radius=0)
        self._hist_list_container.pack(fill="both", expand=True)
        self._render_history_list()

    def _on_hist_filter_change(self, *_):
        if hasattr(self, '_hist_range_var'): self.hist_time_range = self._hist_range_var.get()
        self._render_history_list()

    def _toggle_hist_sort(self):
        self.hist_sort_desc = not self.hist_sort_desc
        if hasattr(self, '_hist_sort_btn'):
            self._hist_sort_btn.configure(text="\U0001f550 Newest First" if self.hist_sort_desc else "\U0001f550 Oldest First")
        self._render_history_list()

    def _filter_history(self, history):
        range_days = {"Today": 1, "Last 7 Days": 7, "Last 30 Days": 30}
        days = range_days.get(self.hist_time_range)
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for entry in history:
                try:
                    ts = datetime.strptime(entry.get('timestamp', ''), "%Y-%m-%d %H:%M:%S")
                    if ts >= cutoff: filtered.append(entry)
                except ValueError:
                    filtered.append(entry)
            history = filtered
        if not self.hist_sort_desc: history = list(reversed(history))
        return history

    def _render_history_list(self):
        if not hasattr(self, '_hist_list_container'): return
        for w in self._hist_list_container.winfo_children(): w.destroy()
        all_history = self._load_audit_history()
        history = self._filter_history(all_history)
        if hasattr(self, '_hist_count_lbl'):
            total, shown = len(all_history), len(history)
            self._hist_count_lbl.configure(text=f"{shown} of {total} entries" if shown < total else f"{total} entries")
        if not history:
            empty = ctk.CTkFrame(self._hist_list_container, fg_color=self.COLORS["bg_secondary"],
                                 corner_radius=12, border_width=1, border_color=self.COLORS["border"])
            empty.pack(fill="both", expand=True)
            center = ctk.CTkFrame(empty, fg_color="transparent")
            center.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(center, text="\U0001f4cb", font=ctk.CTkFont(size=44)).pack()
            ctk.CTkLabel(center, text="No matching audit records", font=ctk.CTkFont("Segoe UI", 16, "bold"),
                         text_color=self.COLORS["text_primary"]).pack(pady=(10, 4))
            ctk.CTkLabel(center, text=("Upload and analyze a CSV file to create your first audit entry."
                         if not all_history else "Try changing the time range filter."),
                         font=ctk.CTkFont("Segoe UI", 10), text_color=self.COLORS["text_muted"]).pack()
            return
        scroll = ctk.CTkScrollableFrame(self._hist_list_container, fg_color="transparent",
                                        scrollbar_button_color=self.COLORS["bg_tertiary"])
        scroll.pack(fill="both", expand=True)
        for entry in history:
            card = ctk.CTkFrame(scroll, fg_color=self.COLORS["bg_secondary"], corner_radius=10,
                                border_width=1, border_color=self.COLORS["border"])
            card.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)
            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(left, text=f"\U0001f4c4  {entry.get('filename', 'Unknown')}",
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=self.COLORS["text_primary"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"\U0001f550 {entry.get('timestamp', '')}   \u00b7   \u23f1 {entry.get('elapsed_seconds', 0)}s",
                         font=ctk.CTkFont("Segoe UI", 9), text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(2, 0))
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")
            for val, color, label in [
                (f"{entry.get('total', 0)}", self.COLORS["accent_blue"], "Total"),
                (f"{entry.get('critical', 0)}", self.COLORS["critical_fg"], "Crit"),
                (f"{entry.get('high', 0)}", self.COLORS["high_fg"], "High"),
                (f"{entry.get('low', 0)}", self.COLORS["low_fg"], "Low"),
            ]:
                pill = ctk.CTkFrame(right, fg_color=self.COLORS["bg_tertiary"], corner_radius=6)
                pill.pack(side="left", padx=3)
                ctk.CTkLabel(pill, text=f"{label}: {val}", font=ctk.CTkFont("Segoe UI", 9, "bold"),
                             text_color=color).pack(padx=8, pady=4)

    def _clear_history(self):
        history = self._load_audit_history()
        if not history:
            messagebox.showinfo("Clear History", "Audit history is already empty.")
            return
        if not messagebox.askyesno("Clear Audit History",
                                   f"This will permanently delete all {len(history)} audit entries.\n\nAre you sure?",
                                   icon="warning"):
            return
        try:
            if os.path.exists(AUDIT_FILE): os.remove(AUDIT_FILE)
            self.status_lbl.configure(text="\U0001f5d1\ufe0f Audit history cleared.")
            self._render_history_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear history:\n{str(e)}")

    # ═════════════════════════════════════════════════════
    #  Feature 3: MODEL SETTINGS PAGE
    # ═════════════════════════════════════════════════════
    def _build_settings_page(self):
        hdr = ctk.CTkFrame(self.workspace, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(hdr, text="\u2699\ufe0f  Model Settings", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(side="left")
        cols = ctk.CTkFrame(self.workspace, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        left_card = ctk.CTkFrame(cols, fg_color=self.COLORS["bg_secondary"], corner_radius=12,
                                 border_width=1, border_color=self.COLORS["border"])
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        li = ctk.CTkFrame(left_card, fg_color="transparent")
        li.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(li, text="MODEL INFORMATION", font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 12))
        model_path = os.path.join(MODEL_DIR, 'risk_model.pkl')
        model_modified = ""
        if os.path.exists(model_path):
            model_modified = datetime.fromtimestamp(os.path.getmtime(model_path)).strftime("%Y-%m-%d %H:%M:%S")
        for lbl, val in [("Model File:", "risk_model.pkl"),
                         ("Status:", "\u2705 Loaded" if self.engine.model else "\u274c Not Loaded"),
                         ("Last Trained:", model_modified or "N/A"),
                         ("Feature Count:", f"{len(self.engine.feature_columns) if self.engine.feature_columns else 0} signals"),
                         ("Algorithm:", "XGBoost Classifier")]:
            row = ctk.CTkFrame(li, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=lbl, font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=self.COLORS["text_muted"], width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont("Segoe UI", 11),
                         text_color=self.COLORS["text_primary"], anchor="w").pack(side="left")
        ctk.CTkButton(li, text="\U0001f504  Retrain Model", font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      fg_color=self.COLORS["accent_blue"], hover_color=self.COLORS["accent_hover"],
                      corner_radius=8, height=38, width=180, command=self._retrain_model).pack(anchor="w", pady=(20, 0))
        right_card = ctk.CTkFrame(cols, fg_color=self.COLORS["bg_secondary"], corner_radius=12,
                                  border_width=1, border_color=self.COLORS["border"])
        right_card.pack(side="right", fill="both", expand=True, padx=(6, 0))
        ri = ctk.CTkFrame(right_card, fg_color="transparent")
        ri.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(ri, text="RISK THRESHOLDS", font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(ri, text="Adjust the probability boundaries for risk classification.",
                     font=ctk.CTkFont("Segoe UI", 9), text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 16))
        self.threshold_vars = {}
        for label, key, color in [("Critical \u2265", "critical", self.COLORS["critical_fg"]),
                                   ("High \u2265", "high", self.COLORS["high_fg"]),
                                   ("Medium \u2265", "medium", self.COLORS["medium_fg"])]:
            row = ctk.CTkFrame(ri, fg_color="transparent")
            row.pack(fill="x", pady=8)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=color, width=100, anchor="w").pack(side="left")
            var = ctk.DoubleVar(value=self.engine.thresholds[key])
            self.threshold_vars[key] = var
            slider = ctk.CTkSlider(row, from_=0.0, to=1.0, number_of_steps=100, variable=var, width=180,
                                   fg_color=self.COLORS["bg_tertiary"], progress_color=color,
                                   button_color=color, button_hover_color=color)
            slider.pack(side="left", padx=(8, 8))
            val_lbl = ctk.CTkLabel(row, text=f"{var.get():.2f}", font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                   text_color=self.COLORS["text_primary"], width=50)
            val_lbl.pack(side="left")
            slider.configure(command=lambda v, lbl=val_lbl: lbl.configure(text=f"{v:.2f}"))
        ctk.CTkButton(ri, text="\u2705  Apply Thresholds", font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      fg_color="#238636", hover_color="#2ea043", corner_radius=8, height=38, width=180,
                      command=self._apply_thresholds).pack(anchor="w", pady=(24, 0))
        ctk.CTkButton(ri, text="\u21ba  Reset to Defaults", font=ctk.CTkFont("Segoe UI", 10),
                      fg_color=self.COLORS["bg_tertiary"], hover_color="#30363d",
                      text_color=self.COLORS["text_muted"], corner_radius=8, height=32, width=160,
                      command=self._reset_thresholds).pack(anchor="w", pady=(8, 0))

    def _apply_thresholds(self):
        self.engine.set_thresholds(
            critical=self.threshold_vars['critical'].get(),
            high=self.threshold_vars['high'].get(),
            medium=self.threshold_vars['medium'].get())
        messagebox.showinfo("Thresholds Updated",
                            f"Risk thresholds updated:\n"
                            f"  Critical \u2265 {self.engine.thresholds['critical']:.2f}\n"
                            f"  High \u2265 {self.engine.thresholds['high']:.2f}\n"
                            f"  Medium \u2265 {self.engine.thresholds['medium']:.2f}\n\n"
                            "Re-upload a CSV to see the new classification.")

    def _reset_thresholds(self):
        for key, default in RiskEngine.DEFAULT_THRESHOLDS.items():
            self.threshold_vars[key].set(default)
        self.engine.set_thresholds(**RiskEngine.DEFAULT_THRESHOLDS)
        self._show_page("settings")

    def _retrain_model(self):
        if not os.path.exists(TRAIN_SCRIPT):
            messagebox.showerror("File Not Found", f"Training script not found:\n{TRAIN_SCRIPT}")
            return
        if not messagebox.askyesno("Retrain Model",
                                   "This will retrain the XGBoost model using DATA/Base.csv.\n"
                                   "This may take a few minutes.\n\nProceed?"):
            return
        self.status_lbl.configure(text="\U0001f504 Retraining model \u2014 this may take a few minutes...")
        def _train():
            try:
                result = subprocess.run([sys.executable, TRAIN_SCRIPT], capture_output=True, text=True, cwd=BASE_DIR)
                if result.returncode == 0: self.after(0, self._on_retrain_success)
                else: self.after(0, self._on_retrain_error, result.stderr)
            except Exception as e:
                self.after(0, self._on_retrain_error, str(e))
        threading.Thread(target=_train, daemon=True).start()

    def _on_retrain_success(self):
        self.engine.load_model()
        self.status_lbl.configure(text="\u2705 Model retrained and reloaded successfully!")
        messagebox.showinfo("Retrain Complete", "XGBoost model retrained and reloaded.\nYou can now re-analyze your data.")
        self._show_page("settings")

    def _on_retrain_error(self, error_text):
        self.status_lbl.configure(text="\u274c Model retraining failed.")
        messagebox.showerror("Retrain Failed", f"Error during retraining:\n{error_text[:500]}")


# ═════════════════════════════════════════════════════════
# Entry Point
# ═════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = RiskApp()
    app.mainloop()
