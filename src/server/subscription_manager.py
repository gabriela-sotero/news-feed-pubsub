"""
Gerenciador de assinaturas de clientes.
Mantém o registro de quais clientes estão inscritos em quais categorias.
"""

from typing import Dict, Set, List
from threading import Lock
import socket


class SubscriptionManager:
    """Gerencia as assinaturas dos clientes por categoria"""

    def __init__(self, available_categories: List[str]):
        self.available_categories = set(cat.lower() for cat in available_categories)
        # Mapa: categoria -> set de conexões de clientes
        self.subscriptions: Dict[str, Set[socket.socket]] = {
            cat: set() for cat in self.available_categories
        }
        # Mapa: socket -> set de categorias inscritas
        self.client_subscriptions: Dict[socket.socket, Set[str]] = {}
        self.lock = Lock()

    def subscribe(self, client_socket: socket.socket, category: str) -> tuple[bool, str]:
        """
        Inscreve um cliente em uma categoria.

        Args:
            client_socket: Socket do cliente
            category: Categoria para inscrição

        Returns:
            Tupla (sucesso, mensagem)
        """
        category = category.lower()

        if category not in self.available_categories:
            return False, f"Categoria '{category}' não existe"

        with self.lock:
            # Adiciona cliente ao mapa de assinaturas da categoria
            self.subscriptions[category].add(client_socket)

            # Adiciona categoria ao mapa de assinaturas do cliente
            if client_socket not in self.client_subscriptions:
                self.client_subscriptions[client_socket] = set()

            if category in self.client_subscriptions[client_socket]:
                return False, f"Já inscrito em '{category}'"

            self.client_subscriptions[client_socket].add(category)

        return True, f"Inscrito em '{category}' com sucesso"

    def unsubscribe(self, client_socket: socket.socket, category: str) -> tuple[bool, str]:
        """
        Remove inscrição de um cliente em uma categoria.

        Args:
            client_socket: Socket do cliente
            category: Categoria para remover

        Returns:
            Tupla (sucesso, mensagem)
        """
        category = category.lower()

        with self.lock:
            if client_socket not in self.client_subscriptions:
                return False, "Cliente não tem assinaturas"

            if category not in self.client_subscriptions[client_socket]:
                return False, f"Não está inscrito em '{category}'"

            # Remove cliente da categoria
            self.subscriptions[category].discard(client_socket)

            # Remove categoria do cliente
            self.client_subscriptions[client_socket].discard(category)

        return True, f"Removido de '{category}' com sucesso"

    def get_subscribers(self, category: str) -> Set[socket.socket]:
        """
        Retorna todos os clientes inscritos em uma categoria.

        Args:
            category: Categoria a consultar

        Returns:
            Set de sockets de clientes inscritos
        """
        category = category.lower()
        with self.lock:
            return self.subscriptions.get(category, set()).copy()

    def get_client_subscriptions(self, client_socket: socket.socket) -> Set[str]:
        """
        Retorna todas as categorias em que um cliente está inscrito.

        Args:
            client_socket: Socket do cliente

        Returns:
            Set de categorias
        """
        with self.lock:
            return self.client_subscriptions.get(client_socket, set()).copy()

    def remove_client(self, client_socket: socket.socket):
        """
        Remove todas as assinaturas de um cliente (ao desconectar).

        Args:
            client_socket: Socket do cliente
        """
        with self.lock:
            if client_socket in self.client_subscriptions:
                # Remove de todas as categorias
                for category in self.client_subscriptions[client_socket]:
                    self.subscriptions[category].discard(client_socket)

                # Remove do mapa de clientes
                del self.client_subscriptions[client_socket]

    def get_available_categories(self) -> List[str]:
        """Retorna lista de categorias disponíveis"""
        return sorted(list(self.available_categories))

    def get_stats(self) -> Dict[str, int]:
        """
        Retorna estatísticas de assinaturas.

        Returns:
            Dicionário com estatísticas por categoria
        """
        with self.lock:
            return {
                cat: len(subs) for cat, subs in self.subscriptions.items()
            }
