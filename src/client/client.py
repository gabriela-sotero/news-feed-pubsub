"""
Cliente TCP para o sistema PUB/SUB de notícias.
Conecta ao servidor, gerencia assinaturas e recebe notícias em tempo real.
"""

import socket
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import Message, MessageType
from common.config import DEFAULT_HOST, DEFAULT_PORT, BUFFER_SIZE, ENCODING


class NewsClient:
    """Cliente de notícias com suporte a assinaturas"""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.connected = False

    def connect(self) -> bool:
        """
        Conecta ao servidor de notícias.

        Returns:
            True se conectou com sucesso, False caso contrário
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True

            print(f"[Cliente] Conectado ao servidor {self.host}:{self.port}\n")

            # Inicia thread para receber mensagens
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            return True

        except ConnectionRefusedError:
            print(f"[Cliente] Erro: Não foi possível conectar ao servidor {self.host}:{self.port}")
            print("[Cliente] Certifique-se de que o servidor está rodando.")
            return False
        except Exception as e:
            print(f"[Cliente] Erro ao conectar: {e}")
            return False

    def disconnect(self):
        """Desconecta do servidor"""
        if self.connected:
            try:
                self._send_message(Message.create(MessageType.DISCONNECT))
            except:
                pass

        self.running = False
        self.connected = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        print("\n[Cliente] Desconectado do servidor")

    def _receive_messages(self):
        """Thread que recebe mensagens do servidor continuamente"""
        buffer = ""

        try:
            while self.running and self.connected:
                data = self.socket.recv(BUFFER_SIZE).decode(ENCODING)

                if not data:
                    print("\n[Cliente] Servidor desconectou")
                    self.connected = False
                    break

                buffer += data
                messages = buffer.split('\n')
                buffer = messages[-1]

                for raw_msg in messages[:-1]:
                    if raw_msg.strip():
                        self._handle_message(raw_msg)

        except ConnectionResetError:
            print("\n[Cliente] Conexão perdida com o servidor")
            self.connected = False
        except Exception as e:
            if self.running:
                print(f"\n[Cliente] Erro ao receber mensagem: {e}")
                self.connected = False

    def _handle_message(self, raw_message: str):
        """
        Processa mensagens recebidas do servidor.

        Args:
            raw_message: Mensagem bruta recebida
        """
        msg = Message.parse(raw_message)
        msg_type = msg.get("type")
        data = msg.get("data", {})

        if msg_type == MessageType.NEWS_UPDATE:
            # Nova notícia recebida
            title = data.get("title", "")
            summary = data.get("summary", "")
            category = data.get("category", "")

            print(f"\n{'='*60}")
            print(f"📰 NOVA NOTÍCIA - [{category.upper()}]")
            print(f"{'='*60}")
            print(f"Título: {title}")
            print(f"Resumo: {summary}")
            print(f"{'='*60}\n")
            print("> ", end="", flush=True)

        elif msg_type == MessageType.SUCCESS:
            message = data.get("message", "")
            print(f"✓ {message}")

        elif msg_type == MessageType.ERROR:
            message = data.get("message", "")
            print(f"✗ Erro: {message}")

        elif msg_type == MessageType.CATEGORIES_LIST:
            categories = data.get("categories", [])
            print(f"\nCategorias disponíveis: {', '.join(categories)}")

    def _send_message(self, message: str):
        """
        Envia uma mensagem para o servidor.

        Args:
            message: Mensagem a enviar
        """
        if self.connected and self.socket:
            try:
                self.socket.sendall(message.encode(ENCODING))
            except Exception as e:
                print(f"[Cliente] Erro ao enviar mensagem: {e}")
                self.connected = False

    def subscribe(self, category: str):
        """Inscreve em uma categoria"""
        self._send_message(Message.subscribe(category))

    def unsubscribe(self, category: str):
        """Remove inscrição de uma categoria"""
        self._send_message(Message.unsubscribe(category))

    def list_categories(self):
        """Lista categorias disponíveis"""
        self._send_message(Message.create(MessageType.LIST_CATEGORIES))

    def run_interactive(self):
        """Executa o cliente em modo interativo"""
        if not self.connect():
            return

        print("\nComandos disponíveis:")
        print("  INSCREVER <categorias> - Inscreve em uma ou mais categorias (separadas por vírgula)")
        print("  REMOVER <categorias>   - Remove inscrição de uma ou mais categorias")
        print("  LISTAR                 - Lista categorias disponíveis")
        print("  SAIR                   - Desconecta do servidor")
        print("\nExemplos:")
        print("  INSCREVER tecnologia")
        print("  INSCREVER cultura, tecnologia")
        print("  REMOVER esportes, política")
        print()

        try:
            while self.connected:
                try:
                    command = input("> ").strip()

                    if not command:
                        continue

                    parts = command.split(maxsplit=1)
                    cmd = parts[0].upper()

                    if cmd == "INSCREVER":
                        if len(parts) < 2:
                            print("✗ Uso: INSCREVER <categoria1>[, categoria2, ...]")
                        else:
                            # Separa múltiplas categorias por vírgula
                            categories = [cat.strip().lower() for cat in parts[1].split(',')]
                            for category in categories:
                                if category:
                                    self.subscribe(category)

                    elif cmd == "REMOVER":
                        if len(parts) < 2:
                            print("✗ Uso: REMOVER <categoria1>[, categoria2, ...]")
                        else:
                            # Separa múltiplas categorias por vírgula
                            categories = [cat.strip().lower() for cat in parts[1].split(',')]
                            for category in categories:
                                if category:
                                    self.unsubscribe(category)

                    elif cmd == "LISTAR":
                        self.list_categories()

                    elif cmd == "SAIR":
                        break

                    else:
                        print(f"✗ Comando desconhecido: {cmd}")
                        print("Use: INSCREVER, REMOVER, LISTAR ou SAIR")

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print()
                    break

        finally:
            self.disconnect()


def main():
    """Função principal para executar o cliente"""
    import argparse

    parser = argparse.ArgumentParser(description="Cliente de Notícias PUB/SUB")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host do servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta do servidor")

    args = parser.parse_args()

    client = NewsClient(args.host, args.port)
    client.run_interactive()


if __name__ == "__main__":
    main()
