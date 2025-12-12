#!/usr/bin/env python3
"""Publicador/Editor de notícias."""

import socket
import threading
import json

# Configurações
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
ENCODING = "utf-8"


class NewsPublisher:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.connected = False
        self.news_published = 0

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True

            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            return True
        except ConnectionRefusedError:
            print(f"✗ Erro: Servidor não está rodando em {self.host}:{self.port}")
            return False
        except Exception as e:
            print(f"✗ Erro ao conectar: {e}")
            return False

    def disconnect(self):
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print(f"\nTotal de notícias publicadas: {self.news_published}")
        print("Desconectado do servidor")

    def _receive_messages(self):
        buffer = ""
        try:
            while self.running and self.connected:
                data = self.socket.recv(BUFFER_SIZE).decode(ENCODING)
                if not data:
                    print("\nServidor desconectou")
                    self.connected = False
                    break

                buffer += data
                messages = buffer.split('\n')
                buffer = messages[-1]

                for raw_msg in messages[:-1]:
                    if raw_msg.strip():
                        self._handle_message(raw_msg)
        except:
            self.connected = False

    def _handle_message(self, raw_message):
        msg = json.loads(raw_message.strip())
        msg_type = msg.get("type")
        data = msg.get("data", {})

        if msg_type == "SUCESSO":
            print(f"✓ {data.get('message', '')}")
        elif msg_type == "ERRO":
            print(f"✗ {data.get('message', '')}")
        elif msg_type == "CATEGORIAS":
            print("\nCategorias disponíveis:")
            for cat in sorted(data.get("categories", [])):
                print(f"  • {cat}")
        elif msg_type == "HISTORICO_LISTA":
            news_list = data.get("news", [])
            if news_list:
                print(f"\nHistórico ({len(news_list)} notícias):")
                for i, news in enumerate(news_list, 1):
                    print(f"  {i}. [{news['category'].upper()}] {news['title']}")
            else:
                print("Nenhuma notícia no histórico")

    def _send_message(self, msg_type, data=None):
        if self.connected and self.socket:
            message = {"type": msg_type, "data": data or {}}
            self.socket.sendall((json.dumps(message) + "\n").encode(ENCODING))

    def publish_news(self, title, lead, category):
        self._send_message("PUBLICAR", {
            "title": title,
            "lead": lead,
            "category": category
        })
        self.news_published += 1

    def list_categories(self):
        self._send_message("LISTAR")

    def request_history(self, limit=10):
        self._send_message("HISTORICO", {"limit": limit})

    def run(self):
        if not self.connect():
            return

        print("✓ Conectado ao servidor\n")
        print("Comandos: PUBLICAR, LISTAR, HISTORICO, SAIR")
        print("Exemplo: PUBLICAR\n")

        try:
            while self.connected:
                try:
                    command = input('> ').strip()
                    if not command:
                        continue

                    cmd = command.upper()

                    if cmd == "PUBLICAR":
                        title = input("Título: ").strip()
                        if not title:
                            print("✗ Título não pode ser vazio")
                            continue

                        lead = input("Lead: ").strip()
                        if not lead:
                            print("✗ Lead não pode ser vazio")
                            continue

                        category = input("Categoria: ").strip().lower()
                        if not category:
                            print("✗ Categoria não pode ser vazia")
                            continue

                        self.publish_news(title, lead, category)

                    elif cmd == "LISTAR":
                        self.list_categories()

                    elif cmd == "HISTORICO":
                        self.request_history()

                    elif cmd == "SAIR":
                        break

                    else:
                        print("Comando desconhecido. Use: PUBLICAR, LISTAR, HISTORICO, SAIR")

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\nUse SAIR para desconectar")
                    continue

        finally:
            self.disconnect()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Publicador de Notícias PUB/SUB")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host do servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta do servidor")
    args = parser.parse_args()

    publisher = NewsPublisher(args.host, args.port)
    publisher.run()


if __name__ == "__main__":
    main()
