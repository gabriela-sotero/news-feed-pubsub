"""
Gerenciador de armazenamento de notícias.
Responsável por persistir e recuperar notícias do sistema.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from threading import Lock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import NEWS_STORAGE_FILE, MAX_NEWS_HISTORY


class NewsStorage:
    """Gerencia o armazenamento de notícias em memória e arquivo"""

    def __init__(self, storage_file: str = NEWS_STORAGE_FILE):
        self.storage_file = storage_file
        self.news_list: List[Dict[str, Any]] = []
        self.lock = Lock()
        self._load_from_file()

    def _load_from_file(self):
        """Carrega notícias do arquivo JSON se existir"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.news_list = json.load(f)
                print(f"[Storage] {len(self.news_list)} notícias carregadas do arquivo")
            except Exception as e:
                print(f"[Storage] Erro ao carregar arquivo: {e}")
                self.news_list = []
        else:
            # Cria diretório se não existir
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)

    def _save_to_file(self):
        """Salva notícias no arquivo JSON"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.news_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Storage] Erro ao salvar arquivo: {e}")

    def add_news(self, title: str, summary: str, category: str) -> Dict[str, Any]:
        """
        Adiciona uma nova notícia ao armazenamento.

        Args:
            title: Título da notícia
            summary: Resumo da notícia
            category: Categoria da notícia

        Returns:
            Dicionário com os dados da notícia adicionada
        """
        with self.lock:
            news = {
                "id": len(self.news_list) + 1,
                "title": title,
                "summary": summary,
                "category": category.lower(),
                "timestamp": datetime.now().isoformat()
            }

            self.news_list.append(news)

            # Limita o tamanho do histórico
            if len(self.news_list) > MAX_NEWS_HISTORY:
                self.news_list = self.news_list[-MAX_NEWS_HISTORY:]

            self._save_to_file()
            return news

    def get_news_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera notícias de uma categoria específica.

        Args:
            category: Categoria a buscar
            limit: Número máximo de notícias a retornar

        Returns:
            Lista de notícias da categoria
        """
        with self.lock:
            filtered = [n for n in self.news_list if n["category"] == category.lower()]
            return filtered[-limit:]

    def get_all_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Recupera todas as notícias.

        Args:
            limit: Número máximo de notícias a retornar

        Returns:
            Lista de notícias
        """
        with self.lock:
            return self.news_list[-limit:]

    def get_news_count(self) -> int:
        """Retorna o número total de notícias armazenadas"""
        with self.lock:
            return len(self.news_list)
