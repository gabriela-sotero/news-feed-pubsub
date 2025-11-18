"""
Configurações do sistema PUB/SUB de notícias.
"""

# Configurações de rede
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
ENCODING = "utf-8"

# Categorias disponíveis
DEFAULT_CATEGORIES = [
    "tecnologia",
    "esportes",
    "cultura",
    "política",
    "economia",
    "entretenimento"
]

# Configurações de armazenamento
NEWS_STORAGE_FILE = "data/news.json"
MAX_NEWS_HISTORY = 100  # Máximo de notícias armazenadas
