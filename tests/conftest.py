"""Configuración común de pytest.

Agrega la raíz del repositorio a `sys.path` para que cada archivo de tests
pueda hacer `from src...` sin repetir la misma línea.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
