"""
Vercel Serverless Function entry point.

This module imports the FastAPI app from api.main and exposes it
as a Vercel-compatible handler. Vercel automatically detects the
`app` variable and uses it to handle incoming requests.
"""

import os
import sys

# Ensure the project root is in the Python path so that
# imports like `from database.connection import ...` work correctly
# when running in Vercel's serverless environment.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.main import app

# Vercel expects an `app` variable (ASGI) or a `handler` function.
# FastAPI is ASGI-compatible, so exporting `app` is sufficient.
# The import above already makes `app` available at module level.
