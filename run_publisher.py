#!/usr/bin/env python3
"""Script para iniciar o publicador de notícias"""

import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from client.publisher import main

if __name__ == "__main__":
    main()
