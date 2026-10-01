import os
import sys

# Ensure the backend app is importable
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Now import the app modules
