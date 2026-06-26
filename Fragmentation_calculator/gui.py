"""
gui.py
------
Tkinter GUI for the UFC 3-340-02 Fragmentation Calculator.
FOR EDUCATIONAL PURPOSES ONLY.

Layout
------
  ┌─────────────────────────────────────────────────────────────┐
  │  Header                                                     │
  ├──────────────────────┬──────────────────────────────────────┤
  │  Input Panel (left)  │  Results Table (right)               │
  │                      │                                      │
  ├──────────────────────┴──────────────────────────────────────┤
  │  Buttons              │  Status bar                         │
  └─────────────────────────────────────────────────────────────┘
  └─  Plot button opens a Matplotlib window ─┘
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from calculations import run_all_calculations, GURNEY_CONSTANTS
from database import (
    get_explosive_names, get_explosive_info,
    mm_to_m, save_session, kg_to_lbs, joules_to_ft_lbf
)

# ── Colour palette ────────────────────────────────────────────────────────────
BG_DARK   = "#1C2333"   # deep navy — main background
BG_MID    = "#253047"   # slightly lighter panel background
BG_CARD   = "#1E2A40"   # card / table rows
ACCENT    = "#E85D04"   # orange accent — buttons, highlights
ACCENT2   = "#F48C06"   # amber — secondary accent
TEXT_PRI  = "#F0F4FF"   # near-white primary text
TEXT_SEC  = "#8FA3C0"   # muted blue-grey secondary text
ROW_ALT   = "#223355"   # alternating table row
ENTRY_BG  = "#162030"   # entry field background
BORDER    = "#334466"   # subtle border

FONT_HEAD  = ("Consolas", 20, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_ENTRY = ("Consolas", 10)
FONT_MONO  = ("Consolas", 10)
FONT_SMALL = ("Segoe UI", 8)
FONT_TITLE = ("Segoe UI", 9, "bold")


class FragCalcApp(tk.Tk):
    """Root application window."""

    def __init__(self):
        super().__init__()
        self.title("UFC 3-340-02 Fragmentation Calculator")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.minsize(900, 640)

        # ── ttk style ─────────────────────────────────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame",           background=BG_DARK)
        style.configure("Card.TFrame",      background=BG_MID, relief="flat")
        style.configure("TLabel",           background=BG_DARK, foreground=TEXT_PRI,
                                            font=FONT_LABEL)
        style.configure("Dim.TLabel",       background=BG_MID,  foreground=TEXT_SEC,
                                            font=FONT_SMALL)
        style.configure("Card.TLabel",      background=BG_MID,  foreground=TEXT_PRI,
                                            font=FONT_LABEL)
        style.configure("Head.TLabel",      background=BG_DARK, foreground=TEXT_PRI,
                                            font=FONT_HEAD)
        style.configure("TCombobox",
                        fieldbackground=ENTRY_BG, background=ENTRY_BG,
                        foreground=TEXT_PRI, selectbackground=ACCENT,
                        arrowcolor=ACCENT)
        style.map("TCombobox",
                  fieldbackground=[("readonly", ENTRY_BG)],
                  selectbackground=[("readonly", ACCENT)])

        # Treeview (results table)
        style.configure("Results.Treeview",
                        background=BG_CARD, fieldbackground=BG_CARD,
                        foreground=TEXT_PRI, font=FONT_MONO,
                        rowheight=26, borderwidth=0)
        style.configure("Results.Treeview.Heading",
                        background=BG_MID, foreground=ACCENT2,
                        font=FONT_TITLE, relief="flat")
        style.map("Results.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", TEXT_PRI)])

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = ttk.Frame(self, padding=(20, 12, 20, 8))
        hdr.pack(fill="x")

        ttk.Label(hdr, text="FRAGMENTATION CALCULATOR", style="Head.TLabel").pack(side="left")
        ttk.Label(hdr,
                  text="  UFC 3-340-02  ·  Educational Use Only",
                  style="Dim.TLabel",
                  font=("Segoe UI", 9, "italic")).pack(side="left", pady=(6, 0))

        # Divider
        div = tk.Frame(self, height=2, bg=ACCENT)
        div.pack(fill="x", padx=20)

        # ── Body: two columns ──────────────────────────────────────────────
        body = ttk.Frame(self, padding=(20, 16, 20, 8))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0, minsize=310)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_input_panel(body)
        self._build_results_panel(body)

        # ── Button bar ─────────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=BG_DARK, pady=10)
        btn_bar.pack(fill="x", padx=20)

        self._btn_calc = tk.Button(
            btn_bar, text="⚡  CALCULATE", command=self._on_calculate,
            bg=ACCENT, fg=TEXT_PRI, activebackground=ACCENT2, activeforeground=TEXT_PRI,
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=20, pady=7, cursor="hand2", bd=0
        )
        self._btn_calc.pack(side="left", padx=(0, 10))

        self._btn_clear = tk.Button(
            btn_bar, text="✕  CLEAR", command=self._on_clear,
            bg=BG_MID, fg=TEXT_SEC, activebackground=BORDER, activeforeground=TEXT_PRI,
            font=("Segoe UI", 10), relief="flat",
            padx=16, pady=7, cursor="hand2", bd=0
        )
        self._btn_clear.pack(side="left", padx=(0, 10))

        self._btn_plot = tk.Button(
            btn_bar, text="📊  PLOT DISTRIBUTION", command=self._on_plot,
            bg=BG_MID, fg=ACCENT2, activebackground=BORDER, activeforeground=ACCENT2,
            font=("Segoe UI", 10), relief="flat",
            padx=16, pady=7, cursor="hand2", bd=0, state="disabled"
        )
        self._btn_plot.pack(side="left")

        # Status bar
        self._status_var = tk.StringVar(value="Enter inputs and press Calculate.")
        status = tk.Label(
            self, textvariable=self._status_var,
            bg="#111824", fg=TEXT_SEC,
            font=("Segoe UI", 8), anchor="w", padx=12, pady=4
        )
        status.pack(fill="x", side="bottom")

        # Internal state
        self._last_results: dict | None = None

    def _build_input_panel(self, parent: ttk.Frame):
        """Left panel: all user inputs."""
        panel = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14, 18, 14))
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        ttk.Label(panel, text="INPUTS", style="Card.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        fields = [
            ("Explosive Type",      "combo",  "explosive_type",       None),
            ("Explosive Weight",    "entry",  "charge_weight",        "kg"),
            ("Casing Weight",       "entry",  "casing_weight",        "kg"),
            ("Casing Thickness",    "entry",  "casing_thickness",     "mm"),
            ("Casing Diameter",     "entry",  "casing_diameter",      "mm"),
            ("Distance",            "entry",  "distance",             "m"),
        ]

        self._vars: dict[str, tk.Variable] = {}
        self._entries: dict[str, tk.Widget] = {}

        for i, (label, kind, key, unit) in enumerate(fields, start=1):
            row = i * 2 - 1

            # Label
            lbl = tk.Label(panel, text=label, bg=BG_MID, fg=TEXT_SEC,
                           font=("Segoe UI", 8, "bold"), anchor="w")
            lbl.grid(row=row, column=0, sticky="w", pady=(8, 0))

            if unit:
                tk.Label(panel, text=unit, bg=BG_MID, fg=ACCENT2,
                         font=("Consolas", 8)).grid(row=row, column=1, sticky="e", pady=(8, 0))

            if kind == "combo":
                var = tk.StringVar(value="TNT")
                cb = ttk.Combobox(panel, textvariable=var,
                                  values=get_explosive_names(),
                                  state="readonly", font=FONT_ENTRY, width=24)
                cb.grid(row=row + 1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
                cb.bind("<<ComboboxSelected>>", self._on_explosive_changed)
            else:
                var = tk.StringVar()
                entry = tk.Entry(
                    panel, textvariable=var,
                    bg=ENTRY_BG, fg=TEXT_PRI, insertbackground=ACCENT,
                    font=FONT_ENTRY, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=ACCENT, width=26
                )
                entry.grid(row=row + 1, column=0, columnspan=2, sticky="ew",
                           pady=(2, 0), ipady=4)
                self._entries[key] = entry

            self._vars[key] = var

        # Explosive info box
        self._info_var = tk.StringVar()
        info_box = tk.Label(
            panel, textvariable=self._info_var,
            bg=ENTRY_BG, fg=TEXT_SEC,
            font=("Segoe UI", 8, "italic"),
            wraplength=260, justify="left",
            padx=8, pady=6, anchor="w"
        )
        info_box.grid(row=99, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self._update_info_box()

    def _build_results_panel(self, parent: ttk.Frame):
        """Right panel: results table."""
        panel = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14, 18, 14))
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        ttk.Label(panel, text="RESULTS", style="Card.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 10))

        # Treeview
        cols = ("parameter", "value", "unit")
        tree = ttk.Treeview(
            panel, columns=cols, show="headings",
            style="Results.Treeview", selectmode="none"
        )
        tree.heading("parameter", text="Parameter")
        tree.heading("value",     text="Value")
        tree.heading("unit",      text="Unit")
        tree.column("parameter", width=230, anchor="w")
        tree.column("value",     width=130, anchor="e")
        tree.column("unit",      width=90,  anchor="w")

        # Scrollbar
        vsb = ttk.Scrollbar(panel, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        panel.rowconfigure(1, weight=1)

        # Alternating row colours
        tree.tag_configure("odd",  background=BG_CARD)
        tree.tag_configure("even", background=ROW_ALT)
        tree.tag_configure("section",
                           background=BG_MID, foreground=ACCENT2,
                           font=("Segoe UI", 8, "bold"))

        self._tree = tree
        self._populate_placeholder_rows()

    # ── Event handlers ─────────────────────────────────────────────────────

    def _on_explosive_changed(self, _event=None):
        self._update_info_box()

    def _update_info_box(self):
        name = self._vars["explosive_type"].get()
        try:
            info = get_explosive_info(name)
            txt = (f"ρ = {info['density_kg_m3']} kg/m³  "
                   f"│  VoD = {info['detonation_velocity_m_s']} m/s  "
                   f"│  √2E = {info['gurney_constant_km_s']} km/s\n"
                   f"{info['notes']}")
        except KeyError:
            txt = ""
        self._info_var.set(txt)

    def _on_calculate(self):
        try:
            inputs = self._parse_inputs()
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        try:
            results = run_all_calculations(**inputs)
        except ValueError as exc:
            messagebox.showerror("Calculation Error", str(exc))
            return

        self._last_results = results
        save_session(inputs, results)
        self._display_results(results, inputs)
        self._btn_plot.config(state="normal")
        self._status_var.set(
            f"Calculated  ·  V₀ = {results['initial_velocity_m_s']} m/s  "
            f"·  N_total ≈ {results['n_total']}  "
            f"·  KE = {results['kinetic_energy_J']} J  "
            f"({joules_to_ft_lbf(results['kinetic_energy_J']):.2f} ft·lbf)"
        )

    def _on_clear(self):
        for var in self._vars.values():
            if isinstance(var, tk.StringVar) and var is not self._vars["explosive_type"]:
                var.set("")
        self._vars["explosive_type"].set("TNT")
        self._update_info_box()
        self._populate_placeholder_rows()
        self._last_results = None
        self._btn_plot.config(state="disabled")
        self._status_var.set("Cleared. Enter inputs and press Calculate.")

    def _on_plot(self):
        if self._last_results is None:
            return
        _show_plot(self._last_results)

    # ── Input parsing ──────────────────────────────────────────────────────

    def _parse_inputs(self) -> dict:
        """Validate and return input values in SI units."""
        explosive_type = self._vars["explosive_type"].get()

        def _float(key: str, label: str, positive: bool = True) -> float:
            raw = self._vars[key].get().strip()
            if not raw:
                raise ValueError(f"'{label}' is required.")
            try:
                val = float(raw)
            except ValueError:
                raise ValueError(f"'{label}' must be a number (got: {raw!r}).")
            if positive and val <= 0:
                raise ValueError(f"'{label}' must be greater than 0.")
            return val

        charge_weight  = _float("charge_weight",    "Explosive Weight")
        casing_weight  = _float("casing_weight",    "Casing Weight")
        thickness_mm   = _float("casing_thickness", "Casing Thickness")
        diameter_mm    = _float("casing_diameter",  "Casing Diameter")
        distance       = _float("distance",         "Distance", positive=False)

        if distance < 0:
            raise ValueError("Distance must be ≥ 0.")

        thickness_m = mm_to_m(thickness_mm)
        diameter_m  = mm_to_m(diameter_mm)

        if thickness_m >= diameter_m / 2:
            raise ValueError(
                "Casing Thickness must be less than half the Casing Diameter."
            )

        return dict(
            explosive_type=explosive_type,
            charge_weight_kg=charge_weight,
            casing_weight_kg=casing_weight,
            casing_thickness_m=thickness_m,
            casing_diameter_m=diameter_m,
            distance_m=distance,
        )

    # ── Results display ────────────────────────────────────────────────────

    def _populate_placeholder_rows(self):
        """Show empty rows before the first calculation."""
        self._tree.delete(*self._tree.get_children())
        placeholder_rows = [
            ("— VELOCITY —",                      "",         ""),
            ("Initial Fragment Velocity",          "—",        "m/s"),
            ("Velocity at Distance",               "—",        "m/s"),
            ("— FRAGMENT MASS —",                  "",         ""),
            ("Average Fragment Mass",              "—",        "g"),
            ("Largest Fragment Mass",              "—",        "g"),
            ("Estimated Fragment Count",           "—",        ""),
            ("— ENERGY —",                         "",         ""),
            ("Fragment Kinetic Energy (at dist.)", "—",        "J"),
            ("Fragment KE (ft·lbf)",               "—",        "ft·lbf"),
        ]
        for idx, (p, v, u) in enumerate(placeholder_rows):
            tag = "section" if p.startswith("—") else ("even" if idx % 2 == 0 else "odd")
            self._tree.insert("", "end", values=(p, v, u), tags=(tag,))

    def _display_results(self, r: dict, inputs: dict):
        """Populate the treeview with calculation results."""
        self._tree.delete(*self._tree.get_children())

        rows = [
            ("— VELOCITY —",                      "",                                     ""),
            ("Initial Fragment Velocity (V₀)",    f"{r['initial_velocity_m_s']:,.1f}",    "m/s"),
            ("Velocity at Distance",              f"{r['velocity_at_distance_m_s']:,.1f}", "m/s"),
            ("Velocity Loss",
             f"{r['initial_velocity_m_s'] - r['velocity_at_distance_m_s']:,.1f}",
             "m/s"),

            ("— FRAGMENT MASS (Mott) —",          "",                                     ""),
            ("Average Fragment Mass",             f"{r['m_avg_g']:,.4f}",                 "g"),
            ("Largest Fragment Mass",             f"{r['m_largest_g']:,.4f}",             "g"),
            ("Estimated Fragment Count",          f"{r['n_total']:,}",                    ""),

            ("— ENERGY —",                        "",                                     ""),
            ("Fragment KE at Distance",           f"{r['kinetic_energy_J']:,.3f}",        "J"),
            ("Fragment KE at Distance",
             f"{joules_to_ft_lbf(r['kinetic_energy_J']):,.3f}",
             "ft·lbf"),

            ("— INPUTS USED —",                   "",                                     ""),
            ("Explosive Type",                    inputs['explosive_type'],               ""),
            ("Charge Mass",                       f"{inputs['charge_weight_kg']:.3f}",    "kg"),
            ("Casing Mass",                       f"{inputs['casing_weight_kg']:.3f}",    "kg"),
            ("Casing Thickness",                  f"{inputs['casing_thickness_m']*1000:.2f}", "mm"),
            ("Casing Diameter",                   f"{inputs['casing_diameter_m']*1000:.2f}",  "mm"),
            ("Standoff Distance",                 f"{inputs['distance_m']:.2f}",          "m"),
        ]

        for idx, (p, v, u) in enumerate(rows):
            is_section = p.startswith("—")
            if is_section:
                tag = "section"
            else:
                tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert("", "end", values=(p, v, u), tags=(tag,))


# ── Standalone plot window ─────────────────────────────────────────────────

def _show_plot(results: dict):
    """Open a Matplotlib figure with the Mott fragment distribution."""
    mass_bins   = results["mass_bins"]   # numpy array [kg]
    cum_counts  = results["cumulative_counts"]
    m_avg_g     = results["m_avg_g"]
    m_largest_g = results["m_largest_g"]
    n_total     = results["n_total"]

    mass_bins_g = mass_bins * 1000  # → grams for display

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("#1C2333")

    ax_style = dict(facecolor="#1E2A40")

    # ── Left: Cumulative count curve ──────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor(ax_style["facecolor"])
    ax1.plot(mass_bins_g, cum_counts, color="#E85D04", linewidth=2,
             label="N(m) — cumulative count")
    ax1.axvline(m_avg_g,     color="#F48C06", linestyle="--", linewidth=1.2,
                label=f"Avg mass = {m_avg_g:.3f} g")
    ax1.axvline(m_largest_g, color="#8FA3C0", linestyle=":",  linewidth=1.2,
                label=f"Largest = {m_largest_g:.3f} g")
    ax1.set_xlabel("Fragment Mass (g)", color="#F0F4FF")
    ax1.set_ylabel("N(m) — Fragments with mass ≥ m", color="#F0F4FF")
    ax1.set_title("Mott Fragment Distribution\nN(m) = N_total · exp(-√(m/m_avg))",
                  color="#F0F4FF", fontsize=9)
    ax1.tick_params(colors="#8FA3C0")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#334466")
    ax1.legend(facecolor="#1C2333", labelcolor="#F0F4FF", fontsize=8)

    # ── Right: Fragment count histogram (differential) ────────────────────
    ax2 = axes[1]
    ax2.set_facecolor(ax_style["facecolor"])

    # dN/dm ≈ -d(cum_counts)/dm (number of fragments in each mass bin)
    dm   = mass_bins[1] - mass_bins[0]
    dNdm = -np.gradient(cum_counts, dm)
    dNdm = np.clip(dNdm, 0, None)

    ax2.bar(mass_bins_g, dNdm * dm, width=(mass_bins_g[1] - mass_bins_g[0]),
            color="#E85D04", alpha=0.75, edgecolor="none")
    ax2.axvline(m_avg_g,     color="#F48C06", linestyle="--", linewidth=1.2,
                label=f"Avg mass = {m_avg_g:.3f} g")
    ax2.set_xlabel("Fragment Mass (g)", color="#F0F4FF")
    ax2.set_ylabel("Fragment Count per Bin", color="#F0F4FF")
    ax2.set_title(f"Fragment Mass Histogram\nN_total ≈ {n_total:,} fragments",
                  color="#F0F4FF", fontsize=9)
    ax2.tick_params(colors="#8FA3C0")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#334466")
    ax2.legend(facecolor="#1C2333", labelcolor="#F0F4FF", fontsize=8)

    plt.tight_layout(pad=2.5)

    # Disclaimer watermark
    fig.text(0.5, 0.01,
             "UFC 3-340-02 — Educational Use Only",
             ha="center", fontsize=7, color="#334466")

    plt.show()
