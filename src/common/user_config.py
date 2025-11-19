"""
Gerenciamento de configuração persistente do usuário.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


# Diretório de configuração do usuário
CONFIG_DIR = Path.home() / '.news_client'
CONFIG_FILE = CONFIG_DIR / 'config.json'
HISTORY_FILE = CONFIG_DIR / 'command_history'


class UserConfig:
    """Gerencia configurações persistentes do usuário"""

    def __init__(self):
        self.config: Dict[str, Any] = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        """Carrega configuração existente ou cria padrão"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                # Se arquivo estiver corrompido, cria novo
                return self._create_default_config()
        else:
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Cria configuração padrão"""
        return {
            'user_name': None,
            'first_run': True,
            'preferences': {
                'display_mode': 'detailed',  # compact, detailed, full
                'auto_subscribe_on_start': False,
                'initial_categories': [],
                'theme': 'default',
                'language': 'pt-BR'
            },
            'shortcuts': {},
            'history': {
                'total_news_received': 0,
                'favorite_category': None,
                'last_login': None,
                'sessions_count': 0
            }
        }

    def save(self):
        """Salva configuração no arquivo"""
        try:
            # Cria diretório se não existir
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Erro ao salvar configuração: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor de configuração"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Define valor de configuração"""
        keys = key.split('.')
        config = self.config

        # Navega até o penúltimo nível
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Define o valor
        config[keys[-1]] = value

    @property
    def is_first_run(self) -> bool:
        """Verifica se é a primeira execução"""
        return self.config.get('first_run', True)

    def mark_first_run_complete(self):
        """Marca que a primeira execução foi concluída"""
        self.config['first_run'] = False
        self.save()

    @property
    def user_name(self) -> Optional[str]:
        """Nome do usuário"""
        return self.config.get('user_name')

    @user_name.setter
    def user_name(self, name: str):
        """Define nome do usuário"""
        self.config['user_name'] = name
        self.save()

    @property
    def display_mode(self) -> str:
        """Modo de exibição (compact, detailed, full)"""
        return self.get('preferences.display_mode', 'detailed')

    @display_mode.setter
    def display_mode(self, mode: str):
        """Define modo de exibição"""
        self.set('preferences.display_mode', mode)
        self.save()

    @property
    def initial_categories(self) -> List[str]:
        """Categorias para auto-inscrição"""
        return self.get('preferences.initial_categories', [])

    @initial_categories.setter
    def initial_categories(self, categories: List[str]):
        """Define categorias iniciais"""
        self.set('preferences.initial_categories', categories)
        self.save()

    @property
    def auto_subscribe(self) -> bool:
        """Se deve auto-inscrever nas categorias iniciais"""
        return self.get('preferences.auto_subscribe_on_start', False)

    @auto_subscribe.setter
    def auto_subscribe(self, enabled: bool):
        """Ativa/desativa auto-inscrição"""
        self.set('preferences.auto_subscribe_on_start', enabled)
        self.save()

    def increment_news_count(self):
        """Incrementa contador de notícias recebidas"""
        current = self.get('history.total_news_received', 0)
        self.set('history.total_news_received', current + 1)
        self.save()

    def update_favorite_category(self, category: str):
        """Atualiza categoria favorita (mais vista)"""
        self.set('history.favorite_category', category)
        self.save()

    def update_last_login(self):
        """Atualiza data do último login"""
        from datetime import datetime
        self.set('history.last_login', datetime.now().isoformat())
        sessions = self.get('history.sessions_count', 0)
        self.set('history.sessions_count', sessions + 1)
        self.save()

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do usuário"""
        return {
            'total_news': self.get('history.total_news_received', 0),
            'favorite_category': self.get('history.favorite_category'),
            'sessions': self.get('history.sessions_count', 0),
            'last_login': self.get('history.last_login')
        }


def run_first_time_wizard() -> UserConfig:
    """
    Executa wizard de configuração inicial.

    Returns:
        UserConfig configurado
    """
    try:
        from .ui_helpers import console, RICH_AVAILABLE, CATEGORY_EMOJIS
        if RICH_AVAILABLE:
            from rich.panel import Panel
    except ImportError:
        RICH_AVAILABLE = False

    config = UserConfig()

    if RICH_AVAILABLE:
        console.print(Panel(
            "[bold cyan]🎉 BEM-VINDO AO FEED DE NOTÍCIAS![/bold cyan]\n\n"
            "Vamos configurar seu cliente em 3 passos rápidos...",
            title="[bold green]Primeira Execução[/bold green]",
            border_style="green"
        ))
    else:
        print("\n" + "="*60)
        print("        🎉 BEM-VINDO AO FEED DE NOTÍCIAS!")
        print("="*60)
        print("\nVamos configurar seu cliente em 3 passos rápidos...\n")

    # Passo 1: Nome
    print("\n📝 PASSO 1/3: Como devemos te chamar?")
    name = input("Nome (ou Enter para pular): ").strip()
    if name:
        config.user_name = name

    # Passo 2: Categorias Iniciais
    print("\n📂 PASSO 2/3: Quais categorias te interessam?")
    print("\nCategorias disponíveis:")

    categories_list = [
        ('1', 'tecnologia', '💻 Tecnologia'),
        ('2', 'esportes', '⚽ Esportes'),
        ('3', 'cultura', '🎭 Cultura'),
        ('4', 'politica', '🏛️  Política'),
        ('5', 'economia', '💰 Economia'),
        ('6', 'entretenimento', '🎬 Entretenimento')
    ]

    for num, cat, label in categories_list:
        print(f"  {num}. {label}")

    print("\nDigite os números separados por vírgula (ex: 1,2,6)")
    print("Ou deixe em branco para escolher depois:")

    choices = input("> ").strip()

    if choices:
        try:
            selected_nums = [c.strip() for c in choices.split(',')]
            selected_categories = []

            for num, cat, _ in categories_list:
                if num in selected_nums:
                    selected_categories.append(cat)

            if selected_categories:
                config.initial_categories = selected_categories
                config.auto_subscribe = True

                if RICH_AVAILABLE:
                    console.print(f"\n[green]✓[/green] Você será automaticamente inscrito em: [bold]{', '.join(selected_categories)}[/bold]")
                else:
                    print(f"\n✓ Você será automaticamente inscrito em: {', '.join(selected_categories)}")
        except:
            print("⚠️  Seleção inválida, você poderá inscrever depois.")

    # Passo 3: Preferências de Exibição
    print("\n🎨 PASSO 3/3: Como você prefere visualizar as notícias?")
    print("\n  1. Modo compacto (apenas títulos)")
    print("  2. Modo detalhado (título + categoria + data) [Padrão]")
    print("  3. Modo completo (todas as informações)")

    display_choice = input("\nEscolha (1-3, ou Enter para padrão): ").strip()

    display_modes = {
        '1': 'compact',
        '2': 'detailed',
        '3': 'full'
    }

    if display_choice in display_modes:
        config.display_mode = display_modes[display_choice]

    # Finaliza
    config.mark_first_run_complete()
    config.update_last_login()

    if RICH_AVAILABLE:
        console.print(Panel(
            "[bold green]✅ Configuração concluída![/bold green]\n\n"
            "Suas preferências foram salvas.\n"
            "Conectando ao servidor...",
            border_style="green"
        ))
    else:
        print("\n" + "="*60)
        print("✅ Configuração concluída!")
        print("="*60)
        print("\nSuas preferências foram salvas.")
        print("Conectando ao servidor...\n")

    return config
