import sys
import os

# Set up paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Patch the analytical router with our experimental one
import models.analytical_router as orig_router
import AGY_EXPERIMENTAL_TRACK.experimental_analytical_router as exp_router

# Override the route function globally
orig_router.route = exp_router.route
orig_router.initialize_engines = exp_router.initialize_engines

# Trigger the JIT warmup
exp_router.initialize_engines()

# Now import and run the main app
# We must use runpy to execute Streamlit's main
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", os.path.join(PROJECT_ROOT, "app.py"), "--server.port", "8503"]
    sys.exit(stcli.main())
