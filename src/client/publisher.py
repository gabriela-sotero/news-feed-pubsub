"""
Publicador/Editor de notícias.
Conecta ao servidor e permite publicar notícias que serão distribuídas aos assinantes.
"""

import socket
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import Message, MessageType
from common.config import DEFAULT_HOST, DEFAULT_PORT, BUFFER_SIZE, ENCODING


class NewsPublisher:
    """Publicador de notícias para o sistema PUB/SUB"""

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

            print(f"[Publicador] Conectado ao servidor {self.host}:{self.port}\n")

            # Inicia thread para receber respostas
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            return True

        except ConnectionRefusedError:
            print(f"[Publicador] Erro: Não foi possível conectar ao servidor {self.host}:{self.port}")
            print("[Publicador] Certifique-se de que o servidor está rodando.")
            return False
        except Exception as e:
            print(f"[Publicador] Erro ao conectar: {e}")
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

        print("\n[Publicador] Desconectado do servidor")

    def _receive_messages(self):
        """Thread que recebe respostas do servidor"""
        buffer = ""

        try:
            while self.running and self.connected:
                data = self.socket.recv(BUFFER_SIZE).decode(ENCODING)

                if not data:
                    print("\n[Publicador] Servidor desconectou")
                    self.connected = False
                    break

                buffer += data
                messages = buffer.split('\n')
                buffer = messages[-1]

                for raw_msg in messages[:-1]:
                    if raw_msg.strip():
                        self._handle_message(raw_msg)

        except ConnectionResetError:
            print("\n[Publicador] Conexão perdida com o servidor")
            self.connected = False
        except Exception as e:
            if self.running:
                print(f"\n[Publicador] Erro ao receber mensagem: {e}")
                self.connected = False

    def _handle_message(self, raw_message: str):
        """
        Processa respostas recebidas do servidor.

        Args:
            raw_message: Mensagem bruta recebida
        """
        msg = Message.parse(raw_message)
        msg_type = msg.get("type")
        data = msg.get("data", {})

        if msg_type == MessageType.SUCCESS:
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
                print(f"[Publicador] Erro ao enviar mensagem: {e}")
                self.connected = False

    def publish_news(self, title: str, summary: str, category: str):
        """
        Publica uma notícia no servidor.

        Args:
            title: Título da notícia
            summary: Resumo da notícia
            category: Categoria da notícia
        """
        message = Message.publish_news(title, summary, category)
        self._send_message(message)

    def list_categories(self):
        """Lista categorias disponíveis"""
        self._send_message(Message.create(MessageType.LIST_CATEGORIES))

    def run_interactive(self):
        """Executa o publicador em modo interativo"""
        if not self.connect():
            return

        print("=== PUBLICADOR DE NOTÍCIAS ===")
        print("\nComandos disponíveis:")
        print("  PUBLICAR               - Publica uma nova notícia")
        print("  LISTAR                 - Lista categorias disponíveis")
        print("  SAIR                   - Desconecta do servidor")
        print()

        try:
            while self.connected:
                try:
                    command = input("> ").strip()

                    if not command:
                        continue

                    cmd = command.upper()

                    if cmd == "PUBLICAR":
                        self._interactive_publish()

                    elif cmd == "LISTAR":
                        self.list_categories()

                    elif cmd == "SAIR":
                        break

                    else:
                        print(f"✗ Comando desconhecido: {cmd}")
                        print("Use: PUBLICAR, LISTAR ou SAIR")

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print()
                    break

        finally:
            self.disconnect()

    def _interactive_publish(self):
        """Modo interativo para publicar notícia"""
        try:
            print("\n--- Nova Notícia ---")
            title = input("Título: ").strip()

            if not title:
                print("✗ Título não pode ser vazio")
                return

            summary = input("Resumo: ").strip()

            if not summary:
                print("✗ Resumo não pode ser vazio")
                return

            category = input("Categoria: ").strip().lower()

            if not category:
                print("✗ Categoria não pode ser vazia")
                return

            print(f"\nPublicando notícia em '{category}'...")
            self.publish_news(title, summary, category)

        except (EOFError, KeyboardInterrupt):
            print("\n✗ Publicação cancelada")

    def run_automated(self, news_list: list):
        """
        Publica notícias automaticamente a partir de uma lista.

        Args:
            news_list: Lista de dicionários com title, summary, category
        """
        if not self.connect():
            return

        import time

        print(f"[Publicador] Modo automático - {len(news_list)} notícias para publicar\n")

        for i, news in enumerate(news_list, 1):
            if not self.connected:
                break

            title = news.get("title", "")
            summary = news.get("summary", "")
            category = news.get("category", "")

            print(f"[{i}/{len(news_list)}] Publicando: {title[:50]}...")
            self.publish_news(title, summary, category)

            # Aguarda um pouco entre publicações
            time.sleep(1)

        print("\n[Publicador] Publicação automática concluída")
        time.sleep(1)
        self.disconnect()


def main():
    """Função principal para executar o publicador"""
    import argparse

    parser = argparse.ArgumentParser(description="Publicador de Notícias PUB/SUB")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host do servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta do servidor")
    parser.add_argument("--auto", action="store_true", help="Modo automático com notícias de exemplo")

    args = parser.parse_args()

    publisher = NewsPublisher(args.host, args.port)

    if args.auto:
        # Notícias de exemplo para modo automático
        sample_news = [
            {
                "title": "Nova versão do Python lançada",
                "summary": "Python 3.12 traz melhorias de performance e novos recursos",
                "category": "tecnologia"
            },
            {
                "title": "Time local vence campeonato",
                "summary": "Equipe conquista título após vitória emocionante",
                "category": "esportes"
            },
            {
                "title": "Festival de música acontece no fim de semana",
                "summary": "Evento contará com artistas nacionais e internacionais",
                "category": "cultura"
            },
            {
                "title": "Novas políticas econômicas anunciadas",
                "summary": "Governo apresenta medidas para controle da inflação",
                "category": "economia"
            },
            {
                "title": "Série de sucesso ganha nova temporada",
                "summary": "Produção confirma continuação com elenco original",
                "category": "entretenimento"
            }
        ]
        publisher.run_automated(sample_news)
    else:
        publisher.run_interactive()


if __name__ == "__main__":
    main()
