"""
GÖK SYSTEMS TECH — GökAI Autonomous Multi-Agent Software Engineering Platform
Independent, self-healing AI software factory.
"""

import sys
from pathlib import Path

# Automatically ensure gokai package root is discoverable in sys.path
_PKG_ROOT = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _PKG_ROOT.parent

if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

__version__ = "1.0.0-alpha"
