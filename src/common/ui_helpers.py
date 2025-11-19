"""
Helpers para melhorar a interface do usuário.
Inclui formatação, validação, e utilitários de UX.
"""

from typing import List, Optional, Dict, Any
from difflib import get_close_matches
from datetime import datetime
import os

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Instância global do console Rich
console = Console() if RICH_AVAILABLE else None

# Aliases de comandos
COMMAND_ALIASES = {
    'INSCREVER': ['sub', 'subscribe', 'add', '+', 'inscrever'],
    'REMOVER': ['unsub', 'unsubscribe', 'del', 'remove', '-', 'remover'],
    'LISTAR': ['list', 'ls', 'show', 'categorias', 'listar'],
    'HISTORICO': ['hist', 'history', 'h', 'news', 'historico'],
    'SAIR': ['exit', 'quit', 'q', 'bye', 'sair'],
    'HELP': ['ajuda', 'help', '?']
}

# Emojis por categoria
CATEGORY_EMOJIS = {
    'tecnologia': '💻',
    'esportes': '⚽',
    'cultura': '🎭',
    'politica': '🏛️',
    'economia': '💰',
    'entretenimento': '🎬'
}

# Aliases de categorias
CATEGORY_ALIASES = {
    'tech': 'tecnologia',
    'tecnology': 'tecnologia',
    'tec': 'tecnologia',
    'sport': 'esportes',
    'esporte': 'esportes',
    'sports': 'esportes',
    'cult': 'cultura',
    'culture': 'cultura',
    'pol': 'politica',
    'politics': 'politica',
    'econ': 'economia',
    'economy': 'economia',
    'ent': 'entretenimento',
    'entertainment': 'entretenimento'
}


def normalize_command(cmd: str) -> str:
    """
    Normaliza comando considerando aliases.

    Args:
        cmd: Comando digitado pelo usuário

    Returns:
        Comando normalizado em MAIÚSCULAS
    """
    cmd_clean = cmd.strip()
    cmd_upper = cmd_clean.upper()

    # Verifica se é o comando principal
    for main_cmd, aliases in COMMAND_ALIASES.items():
        if cmd_upper == main_cmd:
            return main_cmd
        # Verifica aliases (case-insensitive)
        if cmd_clean.lower() in [a.lower() for a in aliases]:
            return main_cmd

    return cmd_upper


def normalize_category(category: str) -> str:
    """
    Normaliza categoria considerando aliases.

    Args:
        category: Categoria digitada pelo usuário

    Returns:
        Categoria normalizada
    """
    cat_lower = category.strip().lower()

    # Verifica se é um alias
    if cat_lower in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[cat_lower]

    return cat_lower


def suggest_category(input_cat: str, available_categories: List[str]) -> Optional[str]:
    """
    Sugere categoria mais próxima usando fuzzy matching.

    Args:
        input_cat: Categoria digitada
        available_categories: Lista de categorias disponíveis

    Returns:
        Categoria sugerida ou None
    """
    # Primeiro tenta normalizar
    normalized = normalize_category(input_cat)

    if normalized in available_categories:
        return normalized

    # Fuzzy matching
    matches = get_close_matches(
        input_cat.lower(),
        available_categories,
        n=1,
        cutoff=0.6
    )

    return matches[0] if matches else None


def display_news_rich(title: str, summary: str, category: str, timestamp: str = None):
    """
    Exibe notícia com formatação rica usando Rich.

    Args:
        title: Título da notícia
        summary: Resumo da notícia
        category: Categoria da notícia
        timestamp: Timestamp da notícia (opcional)
    """
    if not RICH_AVAILABLE:
        # Fallback para display simples
        print(f"\n{'='*60}")
        print(f"📰 NOVA NOTÍCIA - [{category.upper()}]")
        print(f"{'='*60}")
        print(f"Título: {title}")
        print(f"Resumo: {summary}")
        if timestamp:
            print(f"Data: {timestamp}")
        print(f"{'='*60}\n")
        return

    emoji = CATEGORY_EMOJIS.get(category, '📰')

    content = f"""
# {emoji} {title}

**Categoria:** {category.upper()}

{summary}
"""

    if timestamp:
        content += f"\n---\n*{timestamp}*"

    console.print(Panel(
        Markdown(content),
        title="[bold yellow]NOVA NOTÍCIA[/bold yellow]",
        border_style="bright_blue",
        box=box.DOUBLE
    ))

    # Som de notificação
    print('\a')


def display_history_rich(news_list: List[Dict[str, Any]], mode: str = 'detailed'):
    """
    Exibe histórico de notícias formatado.

    Args:
        news_list: Lista de notícias
        mode: Modo de exibição ('compact', 'detailed', 'full')
    """
    if not news_list:
        if RICH_AVAILABLE:
            console.print("[yellow]📭 Nenhuma notícia encontrada no histórico.[/yellow]")
        else:
            print("\n📭 Nenhuma notícia encontrada no histórico.")
        return

    if not RICH_AVAILABLE or mode == 'compact':
        # Display simples
        print(f"\n{'='*60}")
        print(f"📚 HISTÓRICO - {len(news_list)} notícia(s)")
        print(f"{'='*60}")
        for news in news_list:
            emoji = CATEGORY_EMOJIS.get(news['category'], '📰')
            print(f"\n{emoji} [{news['category'].upper()}] {news['title']}")
            if mode != 'compact':
                print(f"   {news['summary']}")
                print(f"   {news['timestamp'][:19].replace('T', ' ')}")
            print(f"{'-'*60}")
        print()
        return

    # Display com Rich Table
    table = Table(
        title=f"📚 Histórico de Notícias ({len(news_list)} notícia(s))",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED
    )

    if mode == 'compact':
        table.add_column("Categoria", style="cyan", width=15)
        table.add_column("Título", style="white")

        for news in news_list:
            emoji = CATEGORY_EMOJIS.get(news['category'], '📰')
            table.add_row(
                f"{emoji} {news['category'].upper()}",
                news['title']
            )
    elif mode == 'full':
        table.add_column("ID", style="dim", width=6)
        table.add_column("Categoria", style="cyan", width=15)
        table.add_column("Título", style="white", width=30)
        table.add_column("Resumo", style="bright_black", width=40)
        table.add_column("Data", style="green", width=19)

        for news in news_list:
            emoji = CATEGORY_EMOJIS.get(news['category'], '📰')
            summary_short = news['summary'][:40] + '...' if len(news['summary']) > 40 else news['summary']
            table.add_row(
                str(news['id']),
                f"{emoji} {news['category'].upper()}",
                news['title'][:30] + '...' if len(news['title']) > 30 else news['title'],
                summary_short,
                news['timestamp'][:19].replace('T', ' ')
            )
    else:  # detailed
        table.add_column("Categoria", style="cyan", width=15)
        table.add_column("Título", style="white", width=40)
        table.add_column("Data", style="green", width=19)

        for news in news_list:
            emoji = CATEGORY_EMOJIS.get(news['category'], '📰')
            table.add_row(
                f"{emoji} {news['category'].upper()}",
                news['title'][:40] + '...' if len(news['title']) > 40 else news['title'],
                news['timestamp'][:19].replace('T', ' ')
            )

    console.print(table)


def display_categories_rich(categories: List[str], subscriptions: set = None):
    """
    Exibe categorias disponíveis com menu numerado.

    Args:
        categories: Lista de categorias disponíveis
        subscriptions: Set de categorias inscritas (opcional)
    """
    if subscriptions is None:
        subscriptions = set()

    # Menu numerado das categorias
    categories_menu = [
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

    for num, cat, label in categories_menu:
        if cat in subscriptions:
            status = "[green]✓[/green]" if RICH_AVAILABLE else "✓"
        else:
            status = "[dim]○[/dim]" if RICH_AVAILABLE else "○"

        if RICH_AVAILABLE:
            console.print(f"  {num}. {status} {label}")
        else:
            print(f"  {num}. {status} {label}")

    if subscriptions:
        if RICH_AVAILABLE:
            console.print(f"\n[green]✓[/green] Você está inscrito em: [bold]{', '.join(sorted(subscriptions))}[/bold]")
        else:
            print(f"\n✓ Você está inscrito em: {', '.join(sorted(subscriptions))}")


def print_welcome_banner():
    """Exibe banner de boas-vindas."""
    if RICH_AVAILABLE:
        console.print(Panel(
            "[bold cyan]Feed de Notícias PUB/SUB[/bold cyan]\n"
            "Sistema de notícias em tempo real\n\n"
            "💡 Digite [bold]HELP[/bold] para ver comandos\n"
            "💡 Use [bold]Tab[/bold] para autocompletar",
            title="[bold green]Bem-vindo![/bold green]",
            border_style="green"
        ))
    else:
        print("\n" + "="*60)
        print("        Feed de Notícias PUB/SUB")
        print("    Sistema de notícias em tempo real")
        print("="*60)
        print("\n💡 Digite HELP para ver comandos\n")


def print_status_bar(connected: bool, subscriptions: set, news_count: int):
    """
    Exibe barra de status.

    Args:
        connected: Se está conectado
        subscriptions: Set de categorias inscritas
        news_count: Número de notícias recebidas
    """
    status_icon = '🟢' if connected else '🔴'
    status_text = 'Conectado' if connected else 'Desconectado'
    time_str = datetime.now().strftime('%H:%M:%S')

    status = (
        f"{status_icon} {status_text} | "
        f"📊 {len(subscriptions)} categoria(s) | "
        f"📰 {news_count} notícia(s) | "
        f"🕐 {time_str}"
    )

    if RICH_AVAILABLE:
        console.print(f"[dim]{status}[/dim]")
    else:
        print(status)


def show_contextual_help(subscriptions: set):
    """
    Mostra ajuda contextual baseada no estado do usuário.

    Args:
        subscriptions: Set de categorias inscritas
    """
    if not subscriptions:
        help_text = """
[bold cyan]Comandos Disponíveis:[/bold cyan]

  [bold]INSCREVER[/bold] <categoria>     - Inscreve em uma ou mais categorias
      Aliases: sub, +, add
      Exemplo: INSCREVER tecnologia
      Exemplo: + esportes, cultura

  [bold]LISTAR[/bold]                    - Lista categorias disponíveis
      Aliases: ls, list

  [bold]HISTORICO[/bold] [cat] [N]       - Ver notícias passadas
      Aliases: hist, h
      Exemplo: HISTORICO
      Exemplo: HISTORICO tecnologia 5

  [bold]HELP[/bold]                      - Mostra esta ajuda
      Aliases: ?, ajuda

  [bold]SAIR[/bold]                      - Desconecta do servidor
      Aliases: quit, q, exit

[yellow]💡 Dica:[/yellow] Você ainda não está inscrito em nenhuma categoria.
    Comece com: [bold]INSCREVER tecnologia[/bold]
"""
    else:
        help_text = f"""
[bold cyan]Comandos Disponíveis:[/bold cyan]

  [bold]INSCREVER[/bold] <categoria>     - Adicionar mais categorias
  [bold]REMOVER[/bold] <categoria>       - Remover categoria
      Aliases: unsub, -, del

  [bold]LISTAR[/bold]                    - Ver suas assinaturas
  [bold]HISTORICO[/bold] [cat] [N]       - Ver notícias passadas
  [bold]HELP[/bold]                      - Mostra esta ajuda
  [bold]SAIR[/bold]                      - Desconectar

[green]✓[/green] Suas assinaturas: [bold]{', '.join(sorted(subscriptions))}[/bold]

[yellow]💡 Dica:[/yellow] Use [bold]HISTORICO[/bold] para ver notícias anteriores
"""

    if RICH_AVAILABLE:
        console.print(Panel(help_text, title="[bold]Ajuda[/bold]", border_style="cyan"))
    else:
        print("\n" + "="*60)
        print("COMANDOS DISPONÍVEIS")
        print("="*60)
        print("\nINSCREVER <categoria> - Inscreve em categoria")
        print("REMOVER <categoria>   - Remove inscrição")
        print("LISTAR                - Lista categorias")
        print("HISTORICO [cat] [N]   - Ver histórico")
        print("HELP                  - Ajuda")
        print("SAIR                  - Sair")
        if subscriptions:
            print(f"\nSuas assinaturas: {', '.join(sorted(subscriptions))}")
        print("="*60 + "\n")


def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')
