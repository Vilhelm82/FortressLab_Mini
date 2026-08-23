import sys
from pathlib import Path

# src layout: make the package importable without installing
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
