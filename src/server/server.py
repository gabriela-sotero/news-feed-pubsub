"""
Servidor TCP para o sistema PUB/SUB de notícias.
Gerencia múltiplas conexões de clientes e distribui notícias conforme assinaturas.
"""

import socket
import threading
from typing import Dict, Set
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import Message, MessageType
from common.config import DEFAULT_HOST, DEFAULT_PORT, BUFFER_SIZE, ENCODING, DEFAULT_CATEGORIES
from server.subscription_manager import SubscriptionManager
from server.news_storage import NewsStorage


class NewsServer:
    """Servidor de notícias usando modelo PUB/SUB com TCP"""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False

        # Gerenciadores
        self.subscription_manager = SubscriptionManager(DEFAULT_CATEGORIES)
        self.news_storage = NewsStorage()

        # Clientes conectados
        self.clients: Set[socket.socket] = set()
        self.clients_lock = threading.Lock()

        # Estatísticas
        self.total_clients_served = 0
        self.news_published = 0

    def start(self):
        """Inicia o servidor"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"[Servidor] Iniciado em {self.host}:{self.port}")
            print(f"[Servidor] Categorias disponíveis: {', '.join(DEFAULT_CATEGORIES)}")
            print(f"[Servidor] {self.news_storage.get_news_count()} notícias no histórico")
            print("[Servidor] Aguardando conexões...\n")

            # Thread para aceitar conexões
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()

            # Mantém o servidor rodando
            accept_thread.join()

        except KeyboardInterrupt:
            print("\n[Servidor] Encerrando...")
            self.stop()
        except Exception as e:
            print(f"[Servidor] Erro: {e}")
            self.stop()

    def stop(self):
        """Para o servidor e desconecta todos os clientes"""
        self.running = False

        with self.clients_lock:
            for client in self.clients.copy():
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()

        if self.server_socket:
            self.server_socket.close()

        print("[Servidor] Servidor encerrado")

    def _accept_connections(self):
        """Thread principal que aceita novas conexões"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[Servidor] Nova conexão de {address}")

                with self.clients_lock:
                    self.clients.add(client_socket)
                    self.total_clients_served += 1

                # Cria thread para gerenciar este cliente
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                if self.running:
                    print(f"[Servidor] Erro ao aceitar conexão: {e}")

    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """
        Gerencia a comunicação com um cliente específico.

        Args:
            client_socket: Socket do cliente
            address: Endereço do cliente
        """
        client_id = f"{address[0]}:{address[1]}"

        try:
            # Envia mensagem de boas-vindas
            welcome_msg = Message.success(
                f"Conectado ao servidor de notícias! Categorias: {', '.join(DEFAULT_CATEGORIES)}"
            )
            self._send_to_client(client_socket, welcome_msg)

            # Buffer para mensagens incompletas
            buffer = ""

            while self.running:
                data = client_socket.recv(BUFFER_SIZE).decode(ENCODING)

                if not data:
                    break

                buffer += data
                messages = buffer.split('\n')
                buffer = messages[-1]  # Última mensagem pode estar incompleta

                for raw_msg in messages[:-1]:
                    if raw_msg.strip():
                        self._process_message(client_socket, client_id, raw_msg)

        except ConnectionResetError:
            print(f"[Cliente {client_id}] Conexão perdida")
        except Exception as e:
            print(f"[Cliente {client_id}] Erro: {e}")
        finally:
            self._disconnect_client(client_socket, client_id)

    def _process_message(self, client_socket: socket.socket, client_id: str, raw_message: str):
        """
        Processa uma mensagem recebida de um cliente.

        Args:
            client_socket: Socket do cliente
            client_id: ID do cliente
            raw_message: Mensagem bruta recebida
        """
        msg = Message.parse(raw_message)
        msg_type = msg.get("type")
        data = msg.get("data", {})

        if msg_type == MessageType.SUBSCRIBE:
            category = data.get("category", "").lower()
            success, message = self.subscription_manager.subscribe(client_socket, category)
            print(f"[Cliente {client_id}] INSCREVER {category}: {message}")

            if success:
                response = Message.success(message)
            else:
                response = Message.error(message)

            self._send_to_client(client_socket, response)

        elif msg_type == MessageType.UNSUBSCRIBE:
            category = data.get("category", "").lower()
            success, message = self.subscription_manager.unsubscribe(client_socket, category)
            print(f"[Cliente {client_id}] REMOVER {category}: {message}")

            if success:
                response = Message.success(message)
            else:
                response = Message.error(message)

            self._send_to_client(client_socket, response)

        elif msg_type == MessageType.LIST_CATEGORIES:
            categories = self.subscription_manager.get_available_categories()
            subscriptions = self.subscription_manager.get_client_subscriptions(client_socket)

            response = Message.categories_list(categories)
            self._send_to_client(client_socket, response)

            # Envia informação sobre assinaturas apenas se houver assinaturas
            if subscriptions:
                info = Message.success(f"Suas assinaturas: {', '.join(sorted(subscriptions))}")
                self._send_to_client(client_socket, info)

        elif msg_type == MessageType.PUBLISH:
            # Recebe notícia de um editor
            title = data.get("title", "")
            summary = data.get("summary", "")
            category = data.get("category", "").lower()

            if category in self.subscription_manager.get_available_categories():
                # Armazena a notícia
                news = self.news_storage.add_news(title, summary, category)
                self.news_published += 1

                print(f"[Editor {client_id}] Nova notícia publicada em '{category}': {title}")

                # Distribui para todos os inscritos
                self._broadcast_news(title, summary, category)

                response = Message.success(f"Notícia publicada com sucesso (ID: {news['id']})")
            else:
                response = Message.error(f"Categoria '{category}' inválida")

            self._send_to_client(client_socket, response)

        elif msg_type == MessageType.DISCONNECT:
            print(f"[Cliente {client_id}] Solicitou desconexão")
            self._send_to_client(client_socket, Message.success("Desconectado com sucesso"))
            client_socket.close()

        else:
            response = Message.error(f"Comando '{msg_type}' não reconhecido")
            self._send_to_client(client_socket, response)

    def _broadcast_news(self, title: str, summary: str, category: str):
        """
        Transmite uma notícia para todos os clientes inscritos na categoria.

        Args:
            title: Título da notícia
            summary: Resumo da notícia
            category: Categoria da notícia
        """
        subscribers = self.subscription_manager.get_subscribers(category)
        news_msg = Message.news_update(title, summary, category)

        print(f"[Servidor] Distribuindo notícia de '{category}' para {len(subscribers)} cliente(s)")

        # Envia para cada cliente, removendo os que falharam
        failed_clients = []
        for client_socket in subscribers:
            try:
                client_socket.sendall(news_msg.encode(ENCODING))
            except (BrokenPipeError, ConnectionResetError, OSError):
                # Cliente desconectou, marcar para remoção
                failed_clients.append(client_socket)
            except Exception as e:
                print(f"[Servidor] Erro ao enviar para cliente: {e}")
                failed_clients.append(client_socket)

        # Remove clientes que falharam
        for client_socket in failed_clients:
            self.subscription_manager.remove_client(client_socket)
            with self.clients_lock:
                self.clients.discard(client_socket)

    def _send_to_client(self, client_socket: socket.socket, message: str):
        """
        Envia uma mensagem para um cliente específico.

        Args:
            client_socket: Socket do cliente
            message: Mensagem a enviar
        """
        try:
            client_socket.sendall(message.encode(ENCODING))
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            # Cliente desconectou - isso é normal, não precisa logar
            pass
        except Exception as e:
            print(f"[Servidor] Erro inesperado ao enviar mensagem: {e}")

    def _disconnect_client(self, client_socket: socket.socket, client_id: str):
        """
        Desconecta um cliente e remove suas assinaturas.

        Args:
            client_socket: Socket do cliente
            client_id: ID do cliente
        """
        subscriptions = self.subscription_manager.get_client_subscriptions(client_socket)
        if subscriptions:
            print(f"[Cliente {client_id}] Desconectado (estava inscrito em: {', '.join(subscriptions)})")
        else:
            print(f"[Cliente {client_id}] Desconectado")

        self.subscription_manager.remove_client(client_socket)

        with self.clients_lock:
            self.clients.discard(client_socket)

        try:
            client_socket.close()
        except:
            pass


def main():
    """Função principal para executar o servidor"""
    import argparse

    parser = argparse.ArgumentParser(description="Servidor de Notícias PUB/SUB")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host do servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta do servidor")

    args = parser.parse_args()

    server = NewsServer(args.host, args.port)
    server.start()


if __name__ == "__main__":
    main()
