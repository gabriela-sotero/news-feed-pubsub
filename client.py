#!/usr/bin/env python3
"""Cliente TCP para o sistema PUB/SUB de notícias."""

import socket
import threading
import json
import sys

# Configurações
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
ENCODING = "utf-8"


class NewsClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.connected = False
        self.subscriptions = set()

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True

            print(f"✓ Conectado ao servidor {self.host}:{self.port}\n")

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
        print("\nDesconectado do servidor")

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

        if msg_type == "NOTICIA":
            print(f"\n📰 [{data.get('category', '').upper()}] {data.get('title', '')}")
            print(f"   {data.get('lead', '')}\n")
            print("> ", end="", flush=True)

        elif msg_type == "SUCESSO":
            print(f"✓ {data.get('message', '')}")

        elif msg_type == "ERRO":
            print(f"✗ {data.get('message', '')}")

        elif msg_type == "CATEGORIAS":
            print("\nCategorias disponíveis:")
            for cat in sorted(data.get("categories", [])):
                status = "✓" if cat in self.subscriptions else "○"
                print(f"  {status} {cat}")

        elif msg_type == "HISTORICO_LISTA":
            news_list = data.get("news", [])
            if news_list:
                print(f"\nHistórico ({len(news_list)} notícias):")
                for news in news_list:
                    print(f"  [{news['category'].upper()}] {news['title']}")
            else:
                print("Nenhuma notícia no histórico")

    def _send_message(self, msg_type, data=None):
        if self.connected and self.socket:
            message = {"type": msg_type, "data": data or {}}
            self.socket.sendall((json.dumps(message) + "\n").encode(ENCODING))

    def subscribe(self, category):
        self._send_message("INSCREVER", {"category": category})
        self.subscriptions.add(category)

    def unsubscribe(self, category):
        self._send_message("REMOVER", {"category": category})
        self.subscriptions.discard(category)

    def list_categories(self):
        self._send_message("LISTAR")

    def request_history(self, category=None, limit=10):
        data = {"limit": limit}
        if category:
            data["category"] = category
        self._send_message("HISTORICO", data)

    def run(self):
        if not self.connect():
            return

        print("Comandos: INSCREVER <cat>, REMOVER <cat>, LISTAR, HISTORICO, SAIR")
        print("Exemplo: INSCREVER tecnologia\n")

        try:
            while self.connected:
                try:
                    command = input('> ').strip()
                    if not command:
                        continue

                    parts = command.split(maxsplit=1)
                    cmd = parts[0].upper()

                    if cmd == "INSCREVER":
                        if len(parts) > 1:
                            self.subscribe(parts[1].lower())
                        else:
                            print("Uso: INSCREVER <categoria>")

                    elif cmd == "REMOVER":
                        if len(parts) > 1:
                            self.unsubscribe(parts[1].lower())
                        else:
                            print("Uso: REMOVER <categoria>")

                    elif cmd == "LISTAR":
                        self.list_categories()

                    elif cmd == "HISTORICO":
                        self.request_history()

                    elif cmd == "SAIR":
                        break

                    else:
                        print("Comando desconhecido. Use: INSCREVER, REMOVER, LISTAR, HISTORICO, SAIR")

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\nUse SAIR para desconectar")
                    continue

        finally:
            self.disconnect()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cliente de Notícias PUB/SUB")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host do servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta do servidor")
    args = parser.parse_args()

    client = NewsClient(args.host, args.port)
    client.run()


if __name__ == "__main__":
    main()
