"""Put the repo root on sys.path so tests can `import src.engine...` without installation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
