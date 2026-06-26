"""
main.py
-------
Entry point for the UFC 3-340-02 Fragmentation Calculator.

Run with:
    python main.py

Requirements:
    pip install numpy matplotlib
    (tkinter is included with standard Python distributions)

FOR EDUCATIONAL PURPOSES ONLY.
This software implements simplified fragmentation models from UFC 3-340-02
and is NOT intended for engineering design, safety assessment, or any
real-world application.
"""

import sys

# ── Dependency check ───────────────────────────────────────────────────────
def _check_dependencies():
    missing = []
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter  (install Python with Tk support)")

    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"  • {pkg}")
        if "numpy" in missing or "matplotlib" in missing:
            print("\nInstall them with:")
            print("  pip install numpy matplotlib")
        sys.exit(1)


def main():
    _check_dependencies()

    from gui import FragCalcApp

    app = FragCalcApp()

    # Centre the window on screen
    app.update_idletasks()
    w, h = 980, 680
    sw = app.winfo_screenwidth()
    sh = app.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    app.geometry(f"{w}x{h}+{x}+{y}")

    app.mainloop()


if __name__ == "__main__":
    main()
