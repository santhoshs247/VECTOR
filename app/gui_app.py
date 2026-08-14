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
from datetime import datetime

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
        self.title("VECTOR — Risk & Fraud Detection System")
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

        # ── build UI ──
        self._setup_styles()
        self._build_header()
        self._build_main_area()
        self._build_status_bar()
        self._show_page("dashboard")

    # ─────────────────────────────────────────────────────
    # ttk Treeview styles (can't use CTk for treeview)
    # ─────────────────────────────────────────────────────
    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(
            "Treeview",
            background=self.COLORS["bg_primary"],
            foreground=self.COLORS["text_primary"],
            fieldbackground=self.COLORS["bg_primary"],
            rowheight=34,
            borderwidth=0,
            font=('Segoe UI', 10)
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.COLORS["bg_secondary"],
            foreground=self.COLORS["text_primary"],
            font=('Segoe UI', 10, 'bold'),
            borderwidth=0,
            relief='flat'
        )
        self.style.map(
            "Treeview",
            background=[('selected', self.COLORS["accent_blue"])],
            foreground=[('selected', '#ffffff')]
        )
        # Remove treeview borders
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    # ─────────────────────────────────────────────────────
    # HEADER BAR
    # ─────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.COLORS["bg_secondary"], height=64, corner_radius=0,
                              border_width=1, border_color=self.COLORS["border"])
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        # ── branding ──
        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", padx=20, pady=8)

        ctk.CTkLabel(brand, text="🛡️  VECTOR  |  Risk & Fraud Detection",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(anchor="w")

        ctk.CTkLabel(brand, text="Real-time Behavioral Analytics & XGBoost ML Scoring Engine",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w")

        # ── action buttons ──
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right", padx=20, pady=12)

        self.export_btn = ctk.CTkButton(
            btn_box, text="📥  Export Results",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=self.COLORS["bg_tertiary"],
            hover_color="#30363d",
            text_color=self.COLORS["text_primary"],
            corner_radius=8, height=36, width=160,
            command=self.export_results
        )
        self.export_btn.pack(side="right", padx=6)

        self.upload_btn = ctk.CTkButton(
            btn_box, text="📂  Upload Data (CSV/PDF)",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=self.COLORS["accent_blue"],
            hover_color=self.COLORS["accent_hover"],
            text_color="#ffffff",
            corner_radius=8, height=36, width=200,
            command=self.upload_data
        )
        self.upload_btn.pack(side="right", padx=6)

    # ─────────────────────────────────────────────────────
    # MAIN AREA  (sidebar + workspace)
    # ─────────────────────────────────────────────────────
    def _build_main_area(self):
        self.main = ctk.CTkFrame(self, fg_color=self.COLORS["bg_primary"], corner_radius=0)
        self.main.pack(side="top", fill="both", expand=True)

        self._build_sidebar()

        # Workspace container — pages swap in here
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
        for label, key in [("📊  Dashboard", "dashboard"),
                           ("📜  Audit History", "history"),
                           ("⚙️  Model Settings", "settings")]:
            btn = ctk.CTkButton(
                sidebar, text=label,
                font=ctk.CTkFont("Segoe UI", 12),
                fg_color="transparent",
                hover_color=self.COLORS["bg_tertiary"],
                text_color=self.COLORS["text_muted"],
                anchor="w", height=38, corner_radius=6,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        # Divider
        ctk.CTkFrame(sidebar, fg_color=self.COLORS["border"], height=1).pack(fill="x", padx=14, pady=16)

        # ── model status card (bottom) ──
        status_card = ctk.CTkFrame(sidebar, fg_color=self.COLORS["bg_tertiary"], corner_radius=10)
        status_card.pack(side="bottom", fill="x", padx=12, pady=16)

        ctk.CTkLabel(status_card, text="ENGINE STATUS",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", padx=12, pady=(10, 2))

        if self.engine.model is not None:
            status_text = "🟢  XGBoost Model Loaded"
            status_color = self.COLORS["low_fg"]
        else:
            status_text = "🔴  Model File Missing"
            status_color = self.COLORS["critical_fg"]

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
        bar = ctk.CTkFrame(self, fg_color=self.COLORS["bg_secondary"], height=30, corner_radius=0,
                           border_width=1, border_color=self.COLORS["border"])
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

        # Update nav button highlights
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=self.COLORS["accent_blue"],
                              text_color="#ffffff",
                              font=ctk.CTkFont("Segoe UI", 12, "bold"))
            else:
                btn.configure(fg_color="transparent",
                              text_color=self.COLORS["text_muted"],
                              font=ctk.CTkFont("Segoe UI", 12))

        # Clear workspace
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
        # Stats row
        self._build_stats_cards()

        # Content area (empty state or table)
        self.content_frame = ctk.CTkFrame(self.workspace, fg_color=self.COLORS["bg_primary"], corner_radius=0)
        self.content_frame.pack(fill="both", expand=True, pady=(10, 0))

        if self.current_data is not None:
            self._show_table_view()
        else:
            self._show_empty_state()

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

            # Accent top bar (use a thin frame)
            bar = ctk.CTkFrame(card, fg_color=accent, height=4, corner_radius=0)
            bar.pack(fill="x", side="top")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=10)

            ctk.CTkLabel(inner, text=title,
                         font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=self.COLORS["text_muted"]).pack(anchor="w")

            val = "0"
            if self.current_data is not None:
                val = self._compute_stat(key)

            val_lbl = ctk.CTkLabel(inner, text=val,
                                   font=ctk.CTkFont("Segoe UI", 22, "bold"),
                                   text_color=self.COLORS["text_primary"])
            val_lbl.pack(anchor="w", pady=(2, 0))
            self.card_labels[key] = val_lbl

    def _compute_stat(self, key):
        if self.current_data is None:
            return "0"
        df = self.current_data
        if key == "total":
            return str(len(df))
        elif key == "critical":
            return str(int((df['Risk Category'] == 'Critical').sum()))
        elif key == "high":
            return str(int((df['Risk Category'] == 'High').sum()))
        elif key == "low":
            return str(int(((df['Risk Category'] == 'Low') | (df['Risk Category'] == 'Medium')).sum()))
        return "0"

    # ── Feature 6: animated count-up ──
    def _animate_stats(self):
        """Animate stat card numbers from 0 to their final values with ease-out."""
        if self.current_data is None:
            return

        targets = {}
        for key in self.card_labels:
            targets[key] = int(self._compute_stat(key))

        duration_ms = 600
        steps = 30
        interval = duration_ms // steps

        def _step(step_i):
            if step_i > steps:
                # Final exact values
                for key, lbl in self.card_labels.items():
                    lbl.configure(text=f"{targets[key]:,}")
                return

            # Ease-out: t = 1 - (1 - p)^3
            p = step_i / steps
            t = 1 - (1 - p) ** 3

            for key, lbl in self.card_labels.items():
                current = int(targets[key] * t)
                lbl.configure(text=f"{current:,}")

            self.after(interval, _step, step_i + 1)

        _step(0)

    # ── empty state ──
    def _show_empty_state(self):
        box = ctk.CTkFrame(self.content_frame, fg_color=self.COLORS["bg_secondary"],
                           corner_radius=12, border_width=1, border_color=self.COLORS["border"])
        box.pack(fill="both", expand=True)

        center = ctk.CTkFrame(box, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="📂", font=ctk.CTkFont(size=52)).pack()
        ctk.CTkLabel(center, text="No CSV Dataset Loaded",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(pady=(12, 4))
        ctk.CTkLabel(center, text="Upload customer behavioral CSV data to run XGBoost risk prediction scoring.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=self.COLORS["text_muted"]).pack(pady=(0, 18))

        ctk.CTkButton(center, text="Select Data File",
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=self.COLORS["accent_blue"],
                      hover_color=self.COLORS["accent_hover"],
                      corner_radius=8, height=42, width=200,
                      command=self.upload_data).pack()

    # ── data table ──
    def _show_table_view(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

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

        # Row color tags
        self.tree.tag_configure('Critical', background=self.COLORS["critical_bg"], foreground=self.COLORS["critical_fg"])
        self.tree.tag_configure('High', background=self.COLORS["high_bg"], foreground=self.COLORS["high_fg"])
        self.tree.tag_configure('Medium', background=self.COLORS["medium_bg"], foreground=self.COLORS["medium_fg"])
        self.tree.tag_configure('Low', background=self.COLORS["low_bg"], foreground=self.COLORS["low_fg"])

        # Feature 5: hover highlight on rows
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)

        # Double-click inspector
        self.tree.bind("<Double-1>", self._on_row_double_click)

        # Feature 7: tooltip
        self._tooltip = ToolTip(self.tree)
        self.tree.bind("<Motion>", self._on_tree_motion)  # already bound, handled in same func
        self.tree.bind("<Leave>", self._on_tree_leave)

        # Populate data
        self._populate_table()

    def _populate_table(self):
        if self.current_data is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, row in self.current_data.iterrows():
            cust_id = row.get('customer_id', f"CUST-{index+1:05d}")
            score_val = row['Risk Score']
            bar_len = int(score_val * 10)
            score_str = f"{score_val:.4f}  {'█' * bar_len}{'░' * (10 - bar_len)}"
            category = row['Risk Category']
            drivers = row['Top Risk Drivers']

            cat_display = {
                'Critical': '🔴 Critical',
                'High':     '🟠 High',
                'Medium':   '🟡 Medium',
                'Low':      '🟢 Low'
            }.get(category, category)

            self.tree.insert("", "end", values=(index + 1, cust_id, score_str, cat_display, drivers), tags=(category,))

    # ── Feature 5: hover effects on treeview rows ──
    def _on_tree_motion(self, event):
        item = self.tree.identify_row(event.y)
        if item != self._hover_item:
            # Restore previous
            if self._hover_item:
                tags = self.tree.item(self._hover_item, 'tags')
                if tags:
                    self.tree.item(self._hover_item, tags=tags)
            self._hover_item = item

        # Feature 7: tooltip on Risk Drivers column
        col = self.tree.identify_column(event.x)
        if col == '#5' and item:  # 5th column = Top Risk Drivers
            values = self.tree.item(item, 'values')
            if values and len(values) >= 5:
                driver_text = values[4]
                self._tooltip.show(driver_text, event.x_root, event.y_root)
            else:
                self._tooltip.hide()
        else:
            if self._tooltip:
                self._tooltip.hide()

    def _on_tree_leave(self, _event):
        self._hover_item = None
        if self._tooltip:
            self._tooltip.hide()

    # ── row detail modal ──
    def _on_row_double_click(self, event):
        selected = self.tree.selection()
        if not selected or self.current_data is None:
            return
        vals = self.tree.item(selected[0], "values")
        row_idx = int(vals[0]) - 1
        if 0 <= row_idx < len(self.current_data):
            self._open_detail_modal(self.current_data.iloc[row_idx])

    def _open_detail_modal(self, record):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Risk Detail — {record.get('customer_id', 'Customer')}")
        modal.geometry("560x440")
        modal.configure(fg_color=self.COLORS["bg_secondary"])
        modal.transient(self)
        modal.grab_set()
        modal.after(10, modal.lift)

        # Header
        hdr = ctk.CTkFrame(modal, fg_color=self.COLORS["bg_tertiary"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"Customer Risk Profile: {record.get('customer_id', 'N/A')}",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(anchor="w", padx=20, pady=14)

        # Body
        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        category = record.get('Risk Category', 'N/A')
        score = record.get('Risk Score', 0.0)
        drivers = record.get('Top Risk Drivers', 'N/A')

        cat_color = {
            'Critical': self.COLORS["critical_fg"],
            'High':     self.COLORS["high_fg"],
            'Medium':   self.COLORS["medium_fg"],
            'Low':      self.COLORS["low_fg"]
        }.get(category, self.COLORS["text_primary"])

        items = [
            ("Risk Score Probability:", f"{score:.6f}"),
            ("Risk Severity Rating:", category),
            ("Top Behavioral Drivers:", drivers),
        ]

        for lbl_text, val_text in items:
            row_f = ctk.CTkFrame(body, fg_color="transparent")
            row_f.pack(fill="x", pady=8)

            ctk.CTkLabel(row_f, text=lbl_text,
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=self.COLORS["text_muted"],
                         width=180, anchor="w").pack(side="left")

            color = cat_color if lbl_text.startswith("Risk Severity") else self.COLORS["text_primary"]
            ctk.CTkLabel(row_f, text=val_text,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=color,
                         wraplength=300, justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        # Score visual bar
        bar_frame = ctk.CTkFrame(body, fg_color="transparent")
        bar_frame.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(bar_frame, text="Score Gauge:",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w")
        prog = ctk.CTkProgressBar(bar_frame, width=300, height=14, corner_radius=6,
                                  fg_color=self.COLORS["bg_tertiary"],
                                  progress_color=cat_color)
        prog.pack(anchor="w", pady=(6, 0))
        prog.set(score)

        # Close button
        ctk.CTkButton(modal, text="Close Inspector",
                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      fg_color=self.COLORS["accent_blue"],
                      hover_color=self.COLORS["accent_hover"],
                      corner_radius=8, height=36, width=160,
                      command=modal.destroy).pack(pady=18)

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

        ctk.CTkLabel(inner, text="⚡", font=ctk.CTkFont(size=36)).pack()

        msg = f"Analyzing {record_count:,} records..." if record_count else "Processing dataset..."
        ctk.CTkLabel(inner, text=msg,
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(pady=(10, 4))

        ctk.CTkLabel(inner, text="Running XGBoost ML inference engine...",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=self.COLORS["text_muted"]).pack(pady=(0, 14))

        self.loading_bar = ctk.CTkProgressBar(inner, width=280, height=10, corner_radius=5,
                                              fg_color=self.COLORS["bg_tertiary"],
                                              progress_color=self.COLORS["accent_blue"],
                                              mode="indeterminate")
        self.loading_bar.pack()
        self.loading_bar.start()

    def _hide_loading_overlay(self):
        if hasattr(self, 'overlay') and self.overlay:
            if hasattr(self, 'loading_bar'):
                self.loading_bar.stop()
            self.overlay.destroy()
            self.overlay = None

    # ═════════════════════════════════════════════════════
    #  CSV & PDF UPLOAD & PROCESSING
    # ═════════════════════════════════════════════════════
    def upload_data(self):
        file_path = filedialog.askopenfilename(
            title="Select Customer Data (CSV or PDF)",
            filetypes=(("Supported Files", "*.csv *.pdf"), ("CSV Files", "*.csv"), ("PDF Statements", "*.pdf"), ("All Files", "*.*"))
        )
        if not file_path:
            return

        is_pdf = file_path.lower().endswith('.pdf')
        
        if is_pdf:
            if self.pdf_engine is None or self.pdf_engine.model is None:
                messagebox.showerror("Model Error", "PDF model not loaded.\nPlease run model/train_pdf_model.py first.")
                return
        else:
            if self.engine.model is None:
                messagebox.showerror("Model Error",
                                     "Risk model file (risk_model.pkl) not found.\nPlease run model/train_model.py first.")
                return

        self.current_filename = os.path.basename(file_path)
        self.status_lbl.configure(text=f"⚡ Loading '{self.current_filename}'...")
        self.upload_btn.configure(state="disabled")

        # Ensure we're on dashboard
        if self.active_page != "dashboard":
            self._show_page("dashboard")

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
            
            # Since PDF is usually 1 customer, update overlay manually
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

            # Update overlay with count
            self.after(0, lambda: self._update_overlay_count(len(df)))

            scored_df = self.engine.predict(df)
            elapsed = time.time() - start_time
            self.after(0, self._on_processing_complete, scored_df, elapsed)
        except Exception as e:
            self.after(0, self._on_processing_error, str(e))

    def _update_overlay_count(self, count):
        """Update loading overlay message with actual record count."""
        pass  # overlay already shows initial message; count was pre-set

    def _on_processing_complete(self, scored_df, elapsed):
        self.current_data = scored_df
        self.upload_btn.configure(state="normal")
        self._hide_loading_overlay()

        # Rebuild dashboard with data
        self._show_page("dashboard")

        # Feature 6: animate the stats
        self._animate_stats()

        total = len(self.current_data)
        self.status_lbl.configure(text=f"✅ Analysis complete: Scored {total:,} records in {elapsed:.2f}s")
        self.file_info_lbl.configure(text=f"Loaded: {self.current_filename} ({total:,} records)")

        # Feature 2: save to audit history
        self._save_audit_entry(elapsed)

    def _on_processing_error(self, err_msg):
        self.upload_btn.configure(state="normal")
        self._hide_loading_overlay()
        self.status_lbl.configure(text="❌ Error processing file.")
        messagebox.showerror("Processing Error", f"Failed to process CSV file:\n{err_msg}")

    # ═════════════════════════════════════════════════════
    #  EXPORT RESULTS
    # ═════════════════════════════════════════════════════
    def export_results(self):
        if self.current_data is None:
            messagebox.showinfo("Export Info", "No analyzed data available to export. Upload a dataset first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save Scored Results CSV As",
            initialfile=f"Risk_Results_{self.current_filename}"
        )
        if file_path:
            try:
                self.current_data.to_csv(file_path, index=False)
                messagebox.showinfo("Export Success", f"Results exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save file:\n{str(e)}")

    # ═════════════════════════════════════════════════════
    #  Feature 2: AUDIT HISTORY PAGE
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
        """Append current session to audit history JSON."""
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
        history.insert(0, entry)  # newest first

        with open(AUDIT_FILE, 'w') as f:
            json.dump(history, f, indent=2)

    def _build_history_page(self):
        """Build the Audit History page showing all previous analysis sessions."""
        # Page header
        hdr = ctk.CTkFrame(self.workspace, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(hdr, text="📜  Audit History",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(side="left")

        ctk.CTkLabel(hdr, text="Past analysis sessions — click a row for summary",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=self.COLORS["text_muted"]).pack(side="left", padx=(12, 0))

        history = self._load_audit_history()

        if not history:
            empty = ctk.CTkFrame(self.workspace, fg_color=self.COLORS["bg_secondary"],
                                 corner_radius=12, border_width=1, border_color=self.COLORS["border"])
            empty.pack(fill="both", expand=True)
            center = ctk.CTkFrame(empty, fg_color="transparent")
            center.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(center, text="📋", font=ctk.CTkFont(size=44)).pack()
            ctk.CTkLabel(center, text="No audit records yet",
                         font=ctk.CTkFont("Segoe UI", 16, "bold"),
                         text_color=self.COLORS["text_primary"]).pack(pady=(10, 4))
            ctk.CTkLabel(center, text="Upload and analyze a CSV file from the Dashboard to create your first audit entry.",
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=self.COLORS["text_muted"]).pack()
            return

        # Scrollable list of audit entries
        scroll = ctk.CTkScrollableFrame(self.workspace, fg_color="transparent",
                                        scrollbar_button_color=self.COLORS["bg_tertiary"])
        scroll.pack(fill="both", expand=True)

        for i, entry in enumerate(history):
            card = ctk.CTkFrame(scroll, fg_color=self.COLORS["bg_secondary"], corner_radius=10,
                                border_width=1, border_color=self.COLORS["border"])
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            # Left — file info
            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(left, text=f"📄  {entry.get('filename', 'Unknown')}",
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=self.COLORS["text_primary"]).pack(anchor="w")

            ctk.CTkLabel(left, text=f"🕐 {entry.get('timestamp', '')}   ·   ⏱ {entry.get('elapsed_seconds', 0)}s",
                         font=ctk.CTkFont("Segoe UI", 9),
                         text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(2, 0))

            # Right — stats pills
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            pills = [
                (f"{entry.get('total', 0)}", self.COLORS["accent_blue"], "Total"),
                (f"{entry.get('critical', 0)}", self.COLORS["critical_fg"], "Crit"),
                (f"{entry.get('high', 0)}", self.COLORS["high_fg"], "High"),
                (f"{entry.get('low', 0)}", self.COLORS["low_fg"], "Low"),
            ]

            for val, color, label in pills:
                pill = ctk.CTkFrame(right, fg_color=self.COLORS["bg_tertiary"], corner_radius=6)
                pill.pack(side="left", padx=3)
                ctk.CTkLabel(pill, text=f"{label}: {val}",
                             font=ctk.CTkFont("Segoe UI", 9, "bold"),
                             text_color=color).pack(padx=8, pady=4)

    # ═════════════════════════════════════════════════════
    #  Feature 3: MODEL SETTINGS PAGE
    # ═════════════════════════════════════════════════════
    def _build_settings_page(self):
        # Page header
        hdr = ctk.CTkFrame(self.workspace, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(hdr, text="⚙️  Model Settings",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.COLORS["text_primary"]).pack(side="left")

        # Two-column layout
        cols = ctk.CTkFrame(self.workspace, fg_color="transparent")
        cols.pack(fill="both", expand=True)

        # ── LEFT COLUMN: Model Info ──
        left_card = ctk.CTkFrame(cols, fg_color=self.COLORS["bg_secondary"], corner_radius=12,
                                 border_width=1, border_color=self.COLORS["border"])
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        left_inner = ctk.CTkFrame(left_card, fg_color="transparent")
        left_inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(left_inner, text="MODEL INFORMATION",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 12))

        model_path = os.path.join(MODEL_DIR, 'risk_model.pkl')
        model_exists = os.path.exists(model_path)
        model_modified = ""
        if model_exists:
            ts = os.path.getmtime(model_path)
            model_modified = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

        info_items = [
            ("Model File:", "risk_model.pkl"),
            ("Status:", "✅ Loaded" if self.engine.model else "❌ Not Loaded"),
            ("Last Trained:", model_modified if model_modified else "N/A"),
            ("Feature Count:", f"{len(self.engine.feature_columns) if self.engine.feature_columns else 0} signals"),
            ("Algorithm:", "XGBoost Classifier"),
        ]

        for lbl, val in info_items:
            row = ctk.CTkFrame(left_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=lbl,
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=self.COLORS["text_muted"],
                         width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=self.COLORS["text_primary"],
                         anchor="w").pack(side="left")

        # Retrain button
        ctk.CTkButton(left_inner, text="🔄  Retrain Model",
                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      fg_color=self.COLORS["accent_blue"],
                      hover_color=self.COLORS["accent_hover"],
                      corner_radius=8, height=38, width=180,
                      command=self._retrain_model).pack(anchor="w", pady=(20, 0))

        # ── RIGHT COLUMN: Threshold Config ──
        right_card = ctk.CTkFrame(cols, fg_color=self.COLORS["bg_secondary"], corner_radius=12,
                                  border_width=1, border_color=self.COLORS["border"])
        right_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        right_inner = ctk.CTkFrame(right_card, fg_color="transparent")
        right_inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(right_inner, text="RISK THRESHOLDS",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(right_inner, text="Adjust the probability boundaries for risk classification.",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self.COLORS["text_muted"]).pack(anchor="w", pady=(0, 16))

        self.threshold_vars = {}
        thresholds = [
            ("Critical ≥", "critical", self.COLORS["critical_fg"]),
            ("High ≥",     "high",     self.COLORS["high_fg"]),
            ("Medium ≥",   "medium",   self.COLORS["medium_fg"]),
        ]

        for label, key, color in thresholds:
            row = ctk.CTkFrame(right_inner, fg_color="transparent")
            row.pack(fill="x", pady=8)

            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=color, width=100, anchor="w").pack(side="left")

            var = ctk.DoubleVar(value=self.engine.thresholds[key])
            self.threshold_vars[key] = var

            slider = ctk.CTkSlider(row, from_=0.0, to=1.0, number_of_steps=100,
                                   variable=var, width=180,
                                   fg_color=self.COLORS["bg_tertiary"],
                                   progress_color=color,
                                   button_color=color,
                                   button_hover_color=color)
            slider.pack(side="left", padx=(8, 8))

            val_lbl = ctk.CTkLabel(row, text=f"{var.get():.2f}",
                                   font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                   text_color=self.COLORS["text_primary"], width=50)
            val_lbl.pack(side="left")

            # Update label when slider changes
            def _on_change(value, lbl=val_lbl, k=key):
                lbl.configure(text=f"{value:.2f}")
            slider.configure(command=_on_change)

        # Apply button
        ctk.CTkButton(right_inner, text="✅  Apply Thresholds",
                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      fg_color="#238636",
                      hover_color="#2ea043",
                      corner_radius=8, height=38, width=180,
                      command=self._apply_thresholds).pack(anchor="w", pady=(24, 0))

        # Reset button
        ctk.CTkButton(right_inner, text="↺  Reset to Defaults",
                      font=ctk.CTkFont("Segoe UI", 10),
                      fg_color=self.COLORS["bg_tertiary"],
                      hover_color="#30363d",
                      text_color=self.COLORS["text_muted"],
                      corner_radius=8, height=32, width=160,
                      command=self._reset_thresholds).pack(anchor="w", pady=(8, 0))

    def _apply_thresholds(self):
        """Apply the slider threshold values to the risk engine."""
        self.engine.set_thresholds(
            critical=self.threshold_vars['critical'].get(),
            high=self.threshold_vars['high'].get(),
            medium=self.threshold_vars['medium'].get()
        )
        messagebox.showinfo("Thresholds Updated",
                            f"Risk thresholds updated:\n"
                            f"  Critical ≥ {self.engine.thresholds['critical']:.2f}\n"
                            f"  High ≥ {self.engine.thresholds['high']:.2f}\n"
                            f"  Medium ≥ {self.engine.thresholds['medium']:.2f}\n\n"
                            "Re-upload a CSV to see the new classification.")

    def _reset_thresholds(self):
        """Reset thresholds to default values."""
        for key, default in RiskEngine.DEFAULT_THRESHOLDS.items():
            self.threshold_vars[key].set(default)
        self.engine.set_thresholds(**RiskEngine.DEFAULT_THRESHOLDS)
        # Refresh the page to update slider labels
        self._show_page("settings")

    def _retrain_model(self):
        """Launch model retraining in a subprocess."""
        if not os.path.exists(TRAIN_SCRIPT):
            messagebox.showerror("File Not Found", f"Training script not found:\n{TRAIN_SCRIPT}")
            return

        confirm = messagebox.askyesno("Retrain Model",
                                      "This will retrain the XGBoost model using DATA/Base.csv.\n"
                                      "This may take a few minutes.\n\nProceed?")
        if not confirm:
            return

        self.status_lbl.configure(text="🔄 Retraining model — this may take a few minutes...")

        def _train():
            try:
                python_exe = sys.executable
                result = subprocess.run(
                    [python_exe, TRAIN_SCRIPT],
                    capture_output=True, text=True, cwd=BASE_DIR
                )
                if result.returncode == 0:
                    self.after(0, self._on_retrain_success)
                else:
                    self.after(0, self._on_retrain_error, result.stderr)
            except Exception as e:
                self.after(0, self._on_retrain_error, str(e))

        threading.Thread(target=_train, daemon=True).start()

    def _on_retrain_success(self):
        self.engine.load_model()
        self.status_lbl.configure(text="✅ Model retrained and reloaded successfully!")
        messagebox.showinfo("Retrain Complete", "XGBoost model retrained and reloaded.\nYou can now re-analyze your data.")
        self._show_page("settings")  # Refresh settings page

    def _on_retrain_error(self, error_text):
        self.status_lbl.configure(text="❌ Model retraining failed.")
        messagebox.showerror("Retrain Failed", f"Error during retraining:\n{error_text[:500]}")


# ═════════════════════════════════════════════════════════
# Entry Point
# ═════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = RiskApp()
    app.mainloop()
