import sys
import os
from pathlib import Path

# Ensure backend package is importable when running pytest from repo root
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Ensure tmp directory exists for test databases
tmp_dir = BACKEND_ROOT.parent / "tmp"
tmp_dir.mkdir(exist_ok=True)

# Set default test database URL if not already set
if "DATABASE_URL" not in os.environ:
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{tmp_dir}/test_mms.db")
