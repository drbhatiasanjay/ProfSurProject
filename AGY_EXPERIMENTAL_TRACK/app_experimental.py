import sys
import os
from pathlib import Path
import streamlit as st

# Setup paths to import from root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# Patch st.Page to use absolute paths since we're running from a subdirectory
orig_page = st.Page
def patched_page(page, *args, **kwargs):
    if isinstance(page, str) and not os.path.isabs(page):
        # app.py is executed from this wrapper, but its page paths belong to
        # the repository root. Pass a resolved Path so Streamlit cannot
        # reinterpret `pages/0_overview.py` relative to this experiment folder.
        page = (Path(PROJECT_ROOT) / page).resolve()
    return orig_page(page, *args, **kwargs)
st.Page = patched_page

# Import the original router and our experimental one
import models.analytical_router as orig_router
import AGY_EXPERIMENTAL_TRACK.experimental_analytical_router as exp_router

# 🚨 GLOBAL MONKEYPATCH 🚨
# Override the route function so that all pages inside app.py use our experimental cache
orig_router.route = exp_router.route
orig_router.initialize_engines = exp_router.initialize_engines

# Trigger the JIT warmup once per session
if "engines_initialized" not in st.session_state:
    exp_router.initialize_engines()
    st.session_state.engines_initialized = True

# Execute the original app.py within this patched context
app_path = os.path.join(PROJECT_ROOT, "app.py")

with open(app_path, "r", encoding="utf8") as f:
    app_code = f.read()

# We need to simulate the __file__ variable so app.py can find its CSS and assets
exec_globals = globals().copy()
exec_globals["__file__"] = app_path

exec(app_code, exec_globals)
