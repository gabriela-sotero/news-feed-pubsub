"""
Publicador/Editor de notícias.
Versão melhorada com interface visual rica e validação aprimorada.
"""

import socket
import threading
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import Message, MessageType
from common.config import DEFAULT_HOST, DEFAULT_PORT, BUFFER_SIZE, ENCODING, DEFAULT_CATEGORIES
from common.ui_helpers import (
    normalize_command, normalize_category, suggest_category,
    display_categories_rich, display_history_rich,
    RICH_AVAILABLE, console, CATEGORY_EMOJIS
)

# Tenta importar prompt_toolkit para autocomplete
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


class NewsPublisher:
    """Publicador de notícias para o sistema PUB/SUB"""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.connected = False
        self.news_published = 0

        # Prompt session com autocomplete e histórico
        if PROMPT_TOOLKIT_AVAILABLE:
            from pathlib import Path
            from prompt_toolkit.history import FileHistory

            history_file = Path.home() / '.news_publisher_history'

            completer = WordCompleter(
                ['PUBLICAR', 'LISTAR', 'HISTORICO', 'SAIR', 'HELP'] +
                list(DEFAULT_CATEGORIES),
                ignore_case=True,
                sentence=True
            )

            self.prompt_session = PromptSession(
                completer=completer,
                history=FileHistory(str(history_file))
            )
        else:
            self.prompt_session = None

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

            if RICH_AVAILABLE:
                console.print(f"[green]✓[/green] Conectado ao servidor {self.host}:{self.port}\n")
            else:
                print(f"✓ Conectado ao servidor {self.host}:{self.port}\n")

            # Inicia thread para receber respostas
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            return True

        except ConnectionRefusedError:
            if RICH_AVAILABLE:
                console.print(f"[red]✗ Erro:[/red] Não foi possível conectar ao servidor {self.host}:{self.port}")
                console.print("[yellow]💡 Certifique-se de que o servidor está rodando.[/yellow]")
            else:
                print(f"✗ Erro: Não foi possível conectar ao servidor {self.host}:{self.port}")
                print("💡 Certifique-se de que o servidor está rodando.")
            return False
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]✗ Erro ao conectar:[/red] {e}")
            else:
                print(f"✗ Erro ao conectar: {e}")
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

        if RICH_AVAILABLE:
            console.print(f"\n[yellow]📊 Total de notícias publicadas:[/yellow] {self.news_published}")
            console.print("\n[green]Desconectado do servidor[/green]")
        else:
            print(f"\n📊 Total de notícias publicadas: {self.news_published}")
            print("\nDesconectado do servidor")

    def _receive_messages(self):
        """Thread que recebe respostas do servidor"""
        buffer = ""

        try:
            while self.running and self.connected:
                data = self.socket.recv(BUFFER_SIZE).decode(ENCODING)

                if not data:
                    if RICH_AVAILABLE:
                        console.print("\n[yellow]Servidor desconectou[/yellow]")
                    else:
                        print("\nServidor desconectou")
                    self.connected = False
                    break

                buffer += data
                messages = buffer.split('\n')
                buffer = messages[-1]

                for raw_msg in messages[:-1]:
                    if raw_msg.strip():
                        self._handle_message(raw_msg)

        except ConnectionResetError:
            if RICH_AVAILABLE:
                console.print("\n[red]Conexão perdida com o servidor[/red]")
            else:
                print("\nConexão perdida com o servidor")
            self.connected = False
        except Exception as e:
            if self.running:
                if RICH_AVAILABLE:
                    console.print(f"\n[red]Erro ao receber mensagem:[/red] {e}")
                else:
                    print(f"\nErro ao receber mensagem: {e}")
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
            if RICH_AVAILABLE:
                console.print(f"[green]✓[/green] {message}")
            else:
                print(f"✓ {message}")

        elif msg_type == MessageType.ERROR:
            message = data.get("message", "")
            if RICH_AVAILABLE:
                console.print(f"[red]✗[/red] {message}")
            else:
                print(f"✗ {message}")

        elif msg_type == MessageType.CATEGORIES_LIST:
            categories = data.get("categories", [])
            display_categories_rich(categories)

        elif msg_type == MessageType.NEWS_HISTORY:
            news_list = data.get("news", [])
            display_history_rich(news_list, mode='detailed')

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
                if RICH_AVAILABLE:
                    console.print(f"[red]Erro ao enviar mensagem:[/red] {e}")
                else:
                    print(f"Erro ao enviar mensagem: {e}")
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
        self.news_published += 1

    def list_categories(self):
        """Lista categorias disponíveis"""
        self._send_message(Message.create(MessageType.LIST_CATEGORIES))

    def request_history(self, category: str = None, limit: int = 10):
        """Solicita histórico de notícias"""
        self._send_message(Message.request_history(category, limit))

    def run_interactive(self):
        """Executa o publicador em modo interativo"""
        if not self.connect():
            return

        # Banner
        if RICH_AVAILABLE:
            from rich.panel import Panel
            console.print(Panel(
                "[bold cyan]Publicador de Notícias[/bold cyan]\n"
                "Sistema para publicar notícias que serão distribuídas aos assinantes\n\n"
                "💡 Digite [bold]HELP[/bold] para ver comandos",
                title="[bold green]Editor de Notícias[/bold green]",
                border_style="green"
            ))
        else:
            print("\n" + "="*60)
            print("        PUBLICADOR DE NOTÍCIAS")
            print("="*60)
            print("\n💡 Digite HELP para ver comandos\n")

        try:
            while self.connected:
                try:
                    # Input com autocomplete se disponível
                    if self.prompt_session:
                        command = self.prompt_session.prompt('> ')
                    else:
                        command = input('> ')

                    command = command.strip()

                    if not command:
                        continue

                    self._process_command(command)

                except EOFError:
                    break
                except KeyboardInterrupt:
                    if RICH_AVAILABLE:
                        console.print("\n[yellow]💡 Use SAIR para desconectar[/yellow]")
                    else:
                        print("\n💡 Use SAIR para desconectar")
                    continue

        finally:
            self.disconnect()

    def _process_command(self, command: str):
        """
        Processa comandos do publicador.

        Args:
            command: Comando digitado
        """
        cmd = normalize_command(command.split()[0])

        if cmd == "PUBLICAR":
            self._interactive_publish()

        elif cmd == "LISTAR":
            self.list_categories()

        elif cmd.startswith("HISTORICO"):
            parts = command.split(maxsplit=1)
            args = parts[1] if len(parts) > 1 else ""

            category = None
            limit = 10

            if args:
                arg_parts = args.split()
                if arg_parts[0].isdigit():
                    limit = int(arg_parts[0])
                else:
                    category = normalize_category(arg_parts[0])
                    if len(arg_parts) > 1 and arg_parts[1].isdigit():
                        limit = int(arg_parts[1])

            self.request_history(category, limit)

        elif cmd == "HELP":
            self._show_help()

        elif cmd == "SAIR":
            if RICH_AVAILABLE:
                console.print("[yellow]Desconectando...[/yellow]")
            else:
                print("Desconectando...")
            self.running = False
            self.connected = False

        else:
            if RICH_AVAILABLE:
                console.print(f"[red]✗[/red] Comando desconhecido: [bold]{command.split()[0]}[/bold]")
                console.print("[yellow]💡 Digite HELP para ver comandos[/yellow]")
            else:
                print(f"✗ Comando desconhecido: {command.split()[0]}")
                print("💡 Digite HELP para ver comandos")

    def _show_help(self):
        """Mostra ajuda do publicador"""
        if RICH_AVAILABLE:
            from rich.panel import Panel
            help_text = """
[bold cyan]Comandos Disponíveis:[/bold cyan]

  [bold]PUBLICAR[/bold]               - Publica uma nova notícia
  [bold]LISTAR[/bold]                 - Lista categorias disponíveis
  [bold]HISTORICO[/bold] [cat] [N]    - Ver notícias publicadas
  [bold]HELP[/bold]                   - Mostra esta ajuda
  [bold]SAIR[/bold]                   - Desconectar

[yellow]💡 Dicas:[/yellow]
  • As notícias são distribuídas apenas para assinantes da categoria
  • Escolha categorias apropriadas para melhor alcance
  • Títulos curtos e objetivos funcionam melhor
"""
            console.print(Panel(help_text, title="[bold]Ajuda[/bold]", border_style="cyan"))
        else:
            print("\n" + "="*60)
            print("COMANDOS DISPONÍVEIS")
            print("="*60)
            print("\nPUBLICAR           - Publica uma nova notícia")
            print("LISTAR             - Lista categorias disponíveis")
            print("HISTORICO [cat] [N]- Ver notícias publicadas")
            print("HELP               - Ajuda")
            print("SAIR               - Sair")
            print("="*60 + "\n")

    def _interactive_publish(self):
        """Modo interativo para publicar notícia"""
        try:
            if RICH_AVAILABLE:
                console.print("\n[bold cyan]─── Nova Notícia ───[/bold cyan]")
            else:
                print("\n--- Nova Notícia ---")

            # Título
            if self.prompt_session:
                title = self.prompt_session.prompt('Título: ')
            else:
                title = input("Título: ")
            title = title.strip()

            if not title:
                if RICH_AVAILABLE:
                    console.print("[red]✗[/red] Título não pode ser vazio")
                else:
                    print("✗ Título não pode ser vazio")
                return

            # Resumo
            if self.prompt_session:
                summary = self.prompt_session.prompt('Resumo: ')
            else:
                summary = input("Resumo: ")
            summary = summary.strip()

            if not summary:
                if RICH_AVAILABLE:
                    console.print("[red]✗[/red] Resumo não pode ser vazio")
                else:
                    print("✗ Resumo não pode ser vazio")
                return

            # Categoria
            if RICH_AVAILABLE:
                console.print("\n[dim]Categorias: " + ", ".join(DEFAULT_CATEGORIES) + "[/dim]")

            if self.prompt_session:
                # Autocomplete para categorias
                cat_completer = WordCompleter(list(DEFAULT_CATEGORIES), ignore_case=True)
                cat_session = PromptSession(completer=cat_completer)
                category = cat_session.prompt('Categoria: ')
            else:
                category = input("Categoria: ")

            category = category.strip().lower()

            if not category:
                if RICH_AVAILABLE:
                    console.print("[red]✗[/red] Categoria não pode ser vazia")
                else:
                    print("✗ Categoria não pode ser vazia")
                return

            # Normaliza e valida categoria
            normalized_cat = normalize_category(category)

            if normalized_cat not in DEFAULT_CATEGORIES:
                # Tenta sugerir
                suggestion = suggest_category(normalized_cat, DEFAULT_CATEGORIES)

                if suggestion:
                    if RICH_AVAILABLE:
                        console.print(f"[yellow]⚠️  Categoria '{category}' não existe.[/yellow]")
                        console.print(f"[cyan]💡 Você quis dizer '{suggestion}'? (s/N):[/cyan] ", end="")
                    else:
                        print(f"⚠️  Categoria '{category}' não existe.")
                        print(f"💡 Você quis dizer '{suggestion}'? (s/N): ", end="")

                    choice = input().strip().lower()
                    if choice == 's':
                        normalized_cat = suggestion
                    else:
                        if RICH_AVAILABLE:
                            console.print("[yellow]Publicação cancelada.[/yellow]")
                        else:
                            print("Publicação cancelada.")
                        return
                else:
                    if RICH_AVAILABLE:
                        console.print(f"[red]✗[/red] Categoria '{category}' não existe.")
                        console.print("[yellow]💡 Use LISTAR para ver categorias disponíveis[/yellow]")
                    else:
                        print(f"✗ Categoria '{category}' não existe.")
                        print("💡 Use LISTAR para ver categorias disponíveis")
                    return

            # Preview da notícia
            if RICH_AVAILABLE:
                from rich.panel import Panel
                emoji = CATEGORY_EMOJIS.get(normalized_cat, '📰')

                preview = f"""
[bold]{title}[/bold]

{summary}

[dim]Categoria: {emoji} {normalized_cat.upper()}[/dim]
"""
                console.print("\n" + "─"*60)
                console.print(Panel(preview, title="[bold yellow]Preview[/bold yellow]", border_style="yellow"))
                console.print("─"*60)
                console.print("\n[cyan]Publicar esta notícia? (S/n):[/cyan] ", end="")
            else:
                print(f"\n{'─'*60}")
                print("PREVIEW")
                print(f"{'─'*60}")
                print(f"Título: {title}")
                print(f"Resumo: {summary}")
                print(f"Categoria: {normalized_cat.upper()}")
                print(f"{'─'*60}")
                print("\nPublicar esta notícia? (S/n): ", end="")

            confirm = input().strip().lower()

            if confirm in ['', 's', 'sim', 'y', 'yes']:
                if RICH_AVAILABLE:
                    console.print(f"\n[yellow]Publicando notícia em '{normalized_cat}'...[/yellow]")
                else:
                    print(f"\nPublicando notícia em '{normalized_cat}'...")

                self.publish_news(title, summary, normalized_cat)
            else:
                if RICH_AVAILABLE:
                    console.print("[yellow]Publicação cancelada.[/yellow]")
                else:
                    print("Publicação cancelada.")

        except (EOFError, KeyboardInterrupt):
            if RICH_AVAILABLE:
                console.print("\n[yellow]Publicação cancelada[/yellow]")
            else:
                print("\nPublicação cancelada")

    def run_automated(self, news_list: list):
        """
        Publica notícias automaticamente a partir de uma lista.

        Args:
            news_list: Lista de dicionários com title, summary, category
        """
        if not self.connect():
            return

        import time

        if RICH_AVAILABLE:
            console.print(f"[yellow]📤 Modo automático - {len(news_list)} notícias para publicar[/yellow]\n")
        else:
            print(f"📤 Modo automático - {len(news_list)} notícias para publicar\n")

        for i, news in enumerate(news_list, 1):
            if not self.connected:
                break

            title = news.get("title", "")
            summary = news.get("summary", "")
            category = news.get("category", "")

            if RICH_AVAILABLE:
                console.print(f"[{i}/{len(news_list)}] Publicando: [bold]{title[:50]}[/bold]...")
            else:
                print(f"[{i}/{len(news_list)}] Publicando: {title[:50]}...")

            self.publish_news(title, summary, category)

            # Aguarda um pouco entre publicações
            time.sleep(1)

        if RICH_AVAILABLE:
            console.print("\n[green]✓ Publicação automática concluída[/green]")
        else:
            print("\n✓ Publicação automática concluída")

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
