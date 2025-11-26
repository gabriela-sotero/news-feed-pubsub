"""
Cliente TCP para o sistema PUB/SUB de notícias.
Versão melhorada com autocomplete, feedback visual rico e configuração persistente.
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
    display_news_rich, display_history_rich, display_categories_rich,
    show_contextual_help,
    RICH_AVAILABLE, console
)

# Tenta importar prompt_toolkit para autocomplete
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import FileHistory
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


class NewsClient:
    """Cliente de notícias com suporte a assinaturas e interface melhorada"""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.connected = False

        # Configuração da sessão (não persiste)
        self.session_config = {
            'user_name': None,
            'initial_categories': []
        }

        # Tracking
        self.subscriptions = set()
        self.news_received_count = 0
        self.session_start = datetime.now()

        # Prompt session com autocomplete (sem histórico persistente)
        if PROMPT_TOOLKIT_AVAILABLE:
            completer = WordCompleter(
                ['INSCREVER', 'REMOVER', 'LISTAR', 'HISTORICO', 'SAIR', 'HELP',
                 'sub', 'unsub', 'ls', 'hist', 'exit', '+', '-'] +
                list(DEFAULT_CATEGORIES),
                ignore_case=True,
                sentence=True
            )

            self.prompt_session = PromptSession(
                completer=completer,
                complete_while_typing=False
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

            # Inicia thread para receber mensagens
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

        # Mostra estatísticas da sessão
        session_duration = (datetime.now() - self.session_start).total_seconds()
        minutes = int(session_duration // 60)
        seconds = int(session_duration % 60)

        if RICH_AVAILABLE:
            console.print(f"\n[yellow]📊 Estatísticas da sessão:[/yellow]")
            console.print(f"   Duração: {minutes}m {seconds}s")
            console.print(f"   Notícias recebidas: {self.news_received_count}")
            console.print("\n[green]Desconectado do servidor[/green]")
        else:
            print(f"\n📊 Estatísticas da sessão:")
            print(f"   Duração: {minutes}m {seconds}s")
            print(f"   Notícias recebidas: {self.news_received_count}")
            print("\nDesconectado do servidor")

    def _receive_messages(self):
        """Thread que recebe mensagens do servidor continuamente"""
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
            lead = data.get("lead", "")
            category = data.get("category", "")

            # Exibe com formatação rica
            display_news_rich(title, lead, category)

            # Atualiza contadores
            self.news_received_count += 1

            # Reimprime prompt
            if RICH_AVAILABLE:
                console.print("> ", end="")
            else:
                print("> ", end="", flush=True)

        elif msg_type == MessageType.SUCCESS:
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
            display_categories_rich(categories, self.subscriptions)

        elif msg_type == MessageType.NEWS_HISTORY:
            news_list = data.get("news", [])
            display_history_rich(news_list, mode='full')

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

    def subscribe(self, category: str):
        """Inscreve em uma categoria"""
        self._send_message(Message.subscribe(category))
        self.subscriptions.add(category)

    def unsubscribe(self, category: str):
        """Remove inscrição de uma categoria"""
        self._send_message(Message.unsubscribe(category))
        self.subscriptions.discard(category)

    def list_categories(self):
        """Lista categorias disponíveis"""
        self._send_message(Message.create(MessageType.LIST_CATEGORIES))

    def request_history(self, category: str = None, limit: int = 10):
        """Solicita histórico de notícias"""
        self._send_message(Message.request_history(category, limit))

    def parse_history_command(self, args: str) -> tuple:
        """
        Parse avançado do comando HISTORICO.

        Args:
            args: Argumentos do comando

        Returns:
            Tupla (categoria, limite)
        """
        if not args.strip():
            return (None, 10)

        # Tenta parsear diferentes formatos
        # HISTORICO tecnologia 5
        # HISTORICO 5
        # HISTORICO tecnologia
        # HISTORICO --categoria tecnologia --limit 5
        # HISTORICO --busca "python"

        category = None
        limit = 10

        # Formato simples
        parts = args.strip().split()

        if len(parts) == 1:
            # Pode ser categoria ou número
            if parts[0].isdigit():
                limit = int(parts[0])
            else:
                category = normalize_category(parts[0])
        elif len(parts) >= 2:
            # Primeiro argumento é categoria, segundo é limite
            if parts[1].isdigit():
                category = normalize_category(parts[0])
                limit = int(parts[1])
            elif parts[0].isdigit():
                limit = int(parts[0])
            else:
                category = normalize_category(parts[0])

        return (category, limit)

    def _interactive_subscribe(self):
        """Menu interativo para inscrição em categorias"""
        categories_list = [
            ('1', 'tecnologia', '💻 Tecnologia'),
            ('2', 'esportes', '⚽ Esportes'),
            ('3', 'cultura', '🎭 Cultura'),
            ('4', 'politica', '🏛️  Política'),
            ('5', 'economia', '💰 Economia'),
            ('6', 'entretenimento', '🎬 Entretenimento')
        ]

        if RICH_AVAILABLE:
            console.print("\n[bold cyan]📂 Categorias Disponíveis:[/bold cyan]\n")
        else:
            print("\n📂 Categorias Disponíveis:\n")

        for num, cat, label in categories_list:
            if cat in self.subscriptions:
                status = "[green]✓[/green]" if RICH_AVAILABLE else "✓"
            else:
                status = "[dim]○[/dim]" if RICH_AVAILABLE else "○"

            if RICH_AVAILABLE:
                console.print(f"  {num}. {status} {label}")
            else:
                print(f"  {num}. {status} {label}")

        # Opção "Todas"
        if RICH_AVAILABLE:
            console.print(f"  7. [bold]📰 Todas[/bold]")
        else:
            print(f"  7. 📰 Todas")

        print("\nDigite os números separados por vírgula (ex: 1,2,6)")
        print("Ou digite 7 para inscrever em todas")
        print("Ou deixe em branco para cancelar:")

        choices = input("> ").strip()

        if not choices:
            if RICH_AVAILABLE:
                console.print("[yellow]Cancelado.[/yellow]")
            else:
                print("Cancelado.")
            return

        try:
            selected_nums = [c.strip() for c in choices.split(',')]
            selected_categories = []

            # Verifica se selecionou "Todas"
            if '7' in selected_nums:
                # Inscreve em todas as categorias que ainda não está inscrito
                for num, cat, _ in categories_list:
                    if cat not in self.subscriptions:
                        selected_categories.append(cat)
            else:
                # Processa seleção individual
                for num, cat, _ in categories_list:
                    if num in selected_nums:
                        if cat not in self.subscriptions:
                            selected_categories.append(cat)

            if selected_categories:
                for cat in selected_categories:
                    self.subscribe(cat)
            else:
                if RICH_AVAILABLE:
                    console.print("[yellow]Nenhuma categoria nova selecionada.[/yellow]")
                else:
                    print("Nenhuma categoria nova selecionada.")
        except:
            if RICH_AVAILABLE:
                console.print("[red]✗[/red] Seleção inválida.")
            else:
                print("✗ Seleção inválida.")

    def _interactive_unsubscribe(self):
        """Menu interativo para remover inscrições"""
        if not self.subscriptions:
            if RICH_AVAILABLE:
                console.print("[yellow]Você não está inscrito em nenhuma categoria.[/yellow]")
            else:
                print("Você não está inscrito em nenhuma categoria.")
            return

        categories_list = [
            ('1', 'tecnologia', '💻 Tecnologia'),
            ('2', 'esportes', '⚽ Esportes'),
            ('3', 'cultura', '🎭 Cultura'),
            ('4', 'politica', '🏛️  Política'),
            ('5', 'economia', '💰 Economia'),
            ('6', 'entretenimento', '🎬 Entretenimento')
        ]

        if RICH_AVAILABLE:
            console.print("\n[bold cyan]📂 Suas Assinaturas:[/bold cyan]\n")
        else:
            print("\n📂 Suas Assinaturas:\n")

        # Mostra apenas as categorias inscritas
        available_nums = []
        for num, cat, label in categories_list:
            if cat in self.subscriptions:
                if RICH_AVAILABLE:
                    console.print(f"  {num}. [green]✓[/green] {label}")
                else:
                    print(f"  {num}. ✓ {label}")
                available_nums.append(num)

        print("\nDigite os números das categorias que deseja remover (ex: 1,2)")
        print("Ou deixe em branco para cancelar:")

        choices = input("> ").strip()

        if not choices:
            if RICH_AVAILABLE:
                console.print("[yellow]Cancelado.[/yellow]")
            else:
                print("Cancelado.")
            return

        try:
            selected_nums = [c.strip() for c in choices.split(',')]
            categories_to_remove = []

            for num, cat, _ in categories_list:
                if num in selected_nums and cat in self.subscriptions:
                    categories_to_remove.append(cat)

            if categories_to_remove:
                # Confirma se for remover múltiplas
                if len(categories_to_remove) > 3:
                    if RICH_AVAILABLE:
                        console.print(f"[yellow]⚠️  Você está prestes a remover {len(categories_to_remove)} categorias.[/yellow]")
                        console.print("[cyan]Confirmar? (s/N):[/cyan] ", end="")
                    else:
                        print(f"⚠️  Você está prestes a remover {len(categories_to_remove)} categorias.")
                        print("Confirmar? (s/N): ", end="")

                    if input().strip().lower() != 's':
                        if RICH_AVAILABLE:
                            console.print("[yellow]Operação cancelada.[/yellow]")
                        else:
                            print("Operação cancelada.")
                        return

                for cat in categories_to_remove:
                    self.unsubscribe(cat)
            else:
                if RICH_AVAILABLE:
                    console.print("[yellow]Nenhuma categoria válida selecionada.[/yellow]")
                else:
                    print("Nenhuma categoria válida selecionada.")
        except:
            if RICH_AVAILABLE:
                console.print("[red]✗[/red] Seleção inválida.")
            else:
                print("✗ Seleção inválida.")

    def _setup_wizard(self):
        """Wizard de configuração no início da sessão"""
        if RICH_AVAILABLE:
            from rich.panel import Panel
            console.print(Panel(
                "[bold cyan]🎉 BEM-VINDO AO FEED DE NOTÍCIAS![/bold cyan]\n\n"
                "Vamos configurar sua sessão...",
                title="[bold green]Configuração da Sessão[/bold green]",
                border_style="green"
            ))
        else:
            print("\n" + "="*60)
            print("        🎉 BEM-VINDO AO FEED DE NOTÍCIAS!")
            print("="*60)
            print("\nVamos configurar sua sessão...\n")

        # Nome
        print("\n📝 Como devemos te chamar?")
        name = input("Nome (ou Enter para pular): ").strip()
        if name:
            self.session_config['user_name'] = name

        # Categorias Iniciais
        print("\n📂 Quais categorias te interessam?")
        print("\nCategorias disponíveis:")

        # Gera lista dinâmica de categorias
        from common.ui_helpers import CATEGORY_EMOJIS

        # Separa "todas" das outras categorias
        other_cats = [cat for cat in DEFAULT_CATEGORIES if cat != 'todas']
        sorted_cats = sorted(other_cats)

        # Monta lista começando com "todas" (0) e depois as outras (1+)
        categories_list = []

        # Adiciona "todas" como opção 0
        if 'todas' in DEFAULT_CATEGORIES:
            emoji = CATEGORY_EMOJIS.get('todas', '📰')
            print(f"  0. {emoji} Todas")

        # Adiciona outras categorias numeradas
        for idx, cat in enumerate(sorted_cats, 1):
            emoji = CATEGORY_EMOJIS.get(cat, '📌')
            cat_display = cat.capitalize()
            print(f"  {idx}. {emoji} {cat_display}")
            categories_list.append((str(idx), cat))

        print("\nDigite os números separados por vírgula (ex: 1,2,6)")
        print("Ou digite 0 para inscrever em todas")
        print("Ou deixe em branco para escolher depois:")

        choices = input("> ").strip()

        if choices:
            try:
                selected_nums = [c.strip() for c in choices.split(',')]
                selected_categories = []

                # Verifica se selecionou "Todas"
                if '0' in selected_nums:
                    # Adiciona categoria "todas"
                    if 'todas' in DEFAULT_CATEGORIES:
                        selected_categories.append('todas')
                else:
                    # Processa seleção individual
                    for num, cat in categories_list:
                        if num in selected_nums:
                            selected_categories.append(cat)

                if selected_categories:
                    self.session_config['initial_categories'] = selected_categories

                    if RICH_AVAILABLE:
                        console.print(f"\n[green]✓[/green] Você será automaticamente inscrito em: [bold]{', '.join(selected_categories)}[/bold]")
                    else:
                        print(f"\n✓ Você será automaticamente inscrito em: {', '.join(selected_categories)}")
            except:
                print("⚠️  Seleção inválida, você poderá inscrever depois.")

        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold green]✅ Configuração concluída![/bold green]\n\n"
                "Conectando ao servidor...",
                border_style="green"
            ))
        else:
            print("\n" + "="*60)
            print("✅ Configuração concluída!")
            print("="*60)
            print("\nConectando ao servidor...\n")

    def run_interactive(self):
        """Executa o cliente em modo interativo"""

        # Wizard de configuração
        self._setup_wizard()

        # Banner de boas-vindas
        if self.session_config['user_name']:
            if RICH_AVAILABLE:
                console.print(f"\n[bold]Olá, {self.session_config['user_name']}![/bold]\n")
            else:
                print(f"\nOlá, {self.session_config['user_name']}!\n")

        # Conecta ao servidor
        if not self.connect():
            return

        # Auto-inscreve em categorias escolhidas
        if self.session_config['initial_categories']:
            if RICH_AVAILABLE:
                console.print("[yellow]Inscrevendo em categorias selecionadas...[/yellow]")
            else:
                print("Inscrevendo em categorias selecionadas...")

            for cat in self.session_config['initial_categories']:
                self.subscribe(cat)

        # Mostra ajuda inicial se não tiver assinaturas
        if not self.subscriptions:
            show_contextual_help(self.subscriptions)

        print()  # Linha em branco

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

                    # Processa comando
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
        Processa um comando do usuário.

        Args:
            command: Comando digitado
        """
        parts = command.split(maxsplit=1)
        cmd = normalize_command(parts[0])

        if cmd == "INSCREVER":
            if len(parts) < 2:
                # Menu interativo de inscrição
                self._interactive_subscribe()
            else:
                # Separa múltiplas categorias por vírgula
                categories = [cat.strip() for cat in parts[1].split(',')]

                for category in categories:
                    if not category:
                        continue

                    # Normaliza categoria
                    normalized = normalize_category(category)

                    # Verifica se categoria existe
                    if normalized not in DEFAULT_CATEGORIES:
                        # Tenta sugerir
                        suggestion = suggest_category(normalized, DEFAULT_CATEGORIES)

                        if suggestion:
                            if RICH_AVAILABLE:
                                console.print(f"[yellow]⚠️  Categoria '{category}' não existe.[/yellow]")
                                console.print(f"[cyan]💡 Você quis dizer '{suggestion}'? (s/N):[/cyan] ", end="")
                            else:
                                print(f"⚠️  Categoria '{category}' não existe.")
                                print(f"💡 Você quis dizer '{suggestion}'? (s/N): ", end="")

                            choice = input().strip().lower()
                            if choice == 's':
                                self.subscribe(suggestion)
                            continue
                        else:
                            if RICH_AVAILABLE:
                                console.print(f"[red]✗[/red] Categoria '{category}' não existe.")
                                console.print("[yellow]💡 Use LISTAR para ver categorias disponíveis[/yellow]")
                            else:
                                print(f"✗ Categoria '{category}' não existe.")
                                print("💡 Use LISTAR para ver categorias disponíveis")
                            continue

                    self.subscribe(normalized)

        elif cmd == "REMOVER":
            if len(parts) < 2:
                # Menu interativo de remoção
                self._interactive_unsubscribe()
            else:
                categories = [cat.strip() for cat in parts[1].split(',')]

                # Se remover múltiplas, pede confirmação
                if len(categories) > 3:
                    if RICH_AVAILABLE:
                        console.print(f"[yellow]⚠️  Você está prestes a remover {len(categories)} categorias.[/yellow]")
                        console.print("[cyan]Confirmar? (s/N):[/cyan] ", end="")
                    else:
                        print(f"⚠️  Você está prestes a remover {len(categories)} categorias.")
                        print("Confirmar? (s/N): ", end="")

                    if input().strip().lower() != 's':
                        if RICH_AVAILABLE:
                            console.print("[yellow]Operação cancelada.[/yellow]")
                        else:
                            print("Operação cancelada.")
                        return

                for category in categories:
                    if category:
                        normalized = normalize_category(category)
                        self.unsubscribe(normalized)

        elif cmd == "LISTAR":
            self.list_categories()

        elif cmd == "HISTORICO":
            args = parts[1] if len(parts) > 1 else ""
            category, limit = self.parse_history_command(args)
            self.request_history(category, limit)

        elif cmd == "HELP":
            show_contextual_help(self.subscriptions)

        elif cmd == "SAIR":
            if RICH_AVAILABLE:
                console.print("[yellow]Desconectando...[/yellow]")
            else:
                print("Desconectando...")
            self.running = False
            self.connected = False

        else:
            if RICH_AVAILABLE:
                console.print(f"[red]✗[/red] Comando desconhecido: [bold]{parts[0]}[/bold]")
                console.print("[yellow]💡 Digite HELP para ver comandos disponíveis[/yellow]")
            else:
                print(f"✗ Comando desconhecido: {parts[0]}")
                print("💡 Digite HELP para ver comandos disponíveis")


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
