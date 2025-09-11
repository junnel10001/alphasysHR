import importlib
import sys

def test_frontend_imports():
    """
    Verify that the Streamlit frontend can be imported without errors.
    This ensures that all required modules are available and the file
    syntax is correct.
    """
    try:
        # Import the frontend app module
        frontend = importlib.import_module("frontend.app")
    except Exception as e:
        assert False, f"Importing frontend.app failed: {e}"

    # Verify that the expected attributes exist
    assert hasattr(frontend, "login"), "login function missing in frontend.app"
    assert hasattr(frontend, "backend_url"), "backend_url variable missing in frontend.app"