#!/usr/bin/env python3
"""Servidor TCP para o sistema PUB/SUB de notícias."""

import socket
import threading
import json
import os
from datetime import datetime

# Configurações
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
ENCODING = "utf-8"
NEWS_STORAGE_FILE = "data/news.json"
MAX_NEWS_HISTORY = 100

DEFAULT_CATEGORIES = [
    "todas", "tecnologia", "esportes", "cultura", "politica", "economia",
    "entretenimento", "musica", "saude", "ciencia", "educacao", "moda",
    "gastronomia", "viagem", "negocios", "meio-ambiente"
]


class NewsServer:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False

        # Assinaturas: categoria -> set de sockets
        self.subscriptions = {cat: set() for cat in DEFAULT_CATEGORIES}

        # Notícias armazenadas
        self.news_list = []
        self._load_news()

        self.clients = set()
        self.lock = threading.Lock()

    def _load_news(self):
        if os.path.exists(NEWS_STORAGE_FILE):
            try:
                with open(NEWS_STORAGE_FILE, 'r', encoding='utf-8') as f:
                    self.news_list = json.load(f)
                print(f"[Server] {len(self.news_list)} notícias carregadas")
            except:
                self.news_list = []
        else:
            os.makedirs(os.path.dirname(NEWS_STORAGE_FILE), exist_ok=True)

    def _save_news(self):
        try:
            with open(NEWS_STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.news_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Server] Erro ao salvar: {e}")

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"[Server] Iniciado em {self.host}:{self.port}")
            print(f"[Server] {len(self.news_list)} notícias no histórico")
            print(f"[Server] Aguardando conexões...\n")

            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            accept_thread.join()

        except KeyboardInterrupt:
            print("\n[Server] Encerrando...")
            self.stop()
        except Exception as e:
            print(f"[Server] Erro: {e}")
            self.stop()

    def stop(self):
        self.running = False
        with self.lock:
            for client in self.clients.copy():
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        if self.server_socket:
            self.server_socket.close()
        print("[Server] Encerrado")

    def _accept_connections(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[Server] Nova conexão: {address}")

                with self.lock:
                    self.clients.add(client_socket)

                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            except:
                if self.running:
                    print("[Server] Erro ao aceitar conexão")

    def _handle_client(self, client_socket, address):
        client_id = f"{address[0]}:{address[1]}"

        try:
            self._send(client_socket, "SUCESSO", {"message": "Conectado ao servidor"})

            buffer = ""
            while self.running:
                data = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
                if not data:
                    break

                buffer += data
                messages = buffer.split('\n')
                buffer = messages[-1]

                for raw_msg in messages[:-1]:
                    if raw_msg.strip():
                        self._process_message(client_socket, client_id, raw_msg)

        except:
            pass
        finally:
            self._disconnect_client(client_socket, client_id)

    def _process_message(self, client_socket, client_id, raw_message):
        msg = json.loads(raw_message.strip())
        msg_type = msg.get("type")
        data = msg.get("data", {})

        if msg_type == "INSCREVER":
            category = data.get("category", "").lower()

            if category == "todas":
                with self.lock:
                    for cat in DEFAULT_CATEGORIES:
                        if cat != "todas":
                            self.subscriptions[cat].add(client_socket)
                self._send(client_socket, "SUCESSO", {"message": "Inscrito em todas as categorias"})
                print(f"[{client_id}] Inscrito em todas")
            elif category in DEFAULT_CATEGORIES:
                with self.lock:
                    self.subscriptions[category].add(client_socket)
                self._send(client_socket, "SUCESSO", {"message": f"Inscrito em '{category}'"})
                print(f"[{client_id}] Inscrito em {category}")
            else:
                self._send(client_socket, "ERRO", {"message": f"Categoria '{category}' não existe"})

        elif msg_type == "REMOVER":
            category = data.get("category", "").lower()

            if category == "todas":
                with self.lock:
                    for cat in DEFAULT_CATEGORIES:
                        self.subscriptions[cat].discard(client_socket)
                self._send(client_socket, "SUCESSO", {"message": "Removido de todas as categorias"})
                print(f"[{client_id}] Removido de todas")
            elif category in DEFAULT_CATEGORIES:
                with self.lock:
                    self.subscriptions[category].discard(client_socket)
                self._send(client_socket, "SUCESSO", {"message": f"Removido de '{category}'"})
                print(f"[{client_id}] Removido de {category}")
            else:
                self._send(client_socket, "ERRO", {"message": f"Categoria '{category}' não existe"})

        elif msg_type == "LISTAR":
            self._send(client_socket, "CATEGORIAS", {"categories": sorted(DEFAULT_CATEGORIES)})

        elif msg_type == "HISTORICO":
            limit = data.get("limit", 10)
            category = data.get("category")

            if category:
                news = [n for n in self.news_list if n["category"] == category][-limit:]
            else:
                news = self.news_list[-limit:]

            self._send(client_socket, "HISTORICO_LISTA", {"news": news})

        elif msg_type == "PUBLICAR":
            title = data.get("title", "")
            lead = data.get("lead", "")
            category = data.get("category", "").lower()

            if category in DEFAULT_CATEGORIES:
                news = {
                    "id": len(self.news_list) + 1,
                    "title": title,
                    "lead": lead,
                    "category": category,
                    "timestamp": datetime.now().isoformat()
                }

                self.news_list.append(news)

                if len(self.news_list) > MAX_NEWS_HISTORY:
                    self.news_list = self.news_list[-MAX_NEWS_HISTORY:]

                self._save_news()

                print(f"[{client_id}] Publicou em '{category}': {title}")

                # Envia para assinantes
                with self.lock:
                    subscribers = self.subscriptions[category].copy()

                for subscriber in subscribers:
                    try:
                        self._send(subscriber, "NOTICIA", {
                            "title": title,
                            "lead": lead,
                            "category": category
                        })
                    except:
                        pass

                self._send(client_socket, "SUCESSO", {"message": f"Notícia publicada (ID: {news['id']})"})
            else:
                self._send(client_socket, "ERRO", {"message": f"Categoria '{category}' inválida"})

        elif msg_type == "SAIR":
            self._send(client_socket, "SUCESSO", {"message": "Desconectado"})
            client_socket.close()

    def _send(self, client_socket, msg_type, data):
        try:
            message = {"type": msg_type, "data": data}
            client_socket.sendall((json.dumps(message) + "\n").encode(ENCODING))
        except:
            pass

    def _disconnect_client(self, client_socket, client_id):
        print(f"[{client_id}] Desconectado")

        with self.lock:
            for cat in DEFAULT_CATEGORIES:
                self.subscriptions[cat].discard(client_socket)
            self.clients.discard(client_socket)

        try:
            client_socket.close()
        except:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Servidor de Notícias PUB/SUB")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host do servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta do servidor")
    args = parser.parse_args()

    server = NewsServer(args.host, args.port)
    server.start()


if __name__ == "__main__":
    main()
