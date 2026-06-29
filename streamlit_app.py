"""Streamlit Cloud entry point — runs app.py unchanged."""

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).parent / "app.py"), run_name="__main__")