import os
import sys
import importlib.util

# Compatibility shim to allow both a top-level module at app/api.py
# and imports that expect a package submodule app.api.routes.
#
# Some test harnesses (and app.main) import `from app.api.routes import ...`.
# If a file app/api.py exists, Python treats `app.api` as a module and will
# not treat the directory app/api/ as a package. To remain backward
# compatible and avoid renaming files, this module dynamically loads the
# file located at app/api/routes.py (if present) and injects it into
# sys.modules as 'app.api.routes' so that `import app.api.routes` works.

_here = os.path.dirname(__file__)
_routes_path = os.path.join(_here, "api", "routes.py")

if os.path.exists(_routes_path):
    spec = importlib.util.spec_from_file_location("app.api.routes", _routes_path)
    routes_mod = importlib.util.module_from_spec(spec)
    # Insert into sys.modules before executing to allow relative imports inside the module
    sys.modules["app.api.routes"] = routes_mod
    try:
        spec.loader.exec_module(routes_mod)
    except Exception:
        # If executing the routes module fails, remove the injected module to avoid partial state
        sys.modules.pop("app.api.routes", None)
        raise

    # Mirror commonly-used attributes at module level for compatibility.
    # This allows code that does `import app.api` and accesses app.api.router
    # or app.api.RESULT_STORE to still function.
    for attr in ("router", "RESULT_STORE", "QueryRequest", "QueryResponse", "ResumeResponse", "StatusResponse"):
        if hasattr(routes_mod, attr):
            globals()[attr] = getattr(routes_mod, attr)

else:
    # If the routes file isn't present, provide minimal fallbacks so imports fail in a clear way.
    # This prevents obscure import errors and makes debugging easier.
    raise ImportError(f"Expected routes module at '{_routes_path}' not found. Ensure 'app/api/routes.py' exists.")
