# Sistema de Feed de Notícias PUB/SUB

Sistema distribuído cliente-servidor usando Sockets TCP que funciona como um feed de notícias contínuo baseado no modelo **PUB/SUB (Publisher/Subscriber)**.

## Descrição

O sistema permite que:
- **Clientes** se inscrevam em categorias de notícias de seu interesse
- **Publicadores** enviem notícias que são automaticamente distribuídas
- **Servidor** gerencie múltiplas conexões simultâneas e distribua notícias apenas para assinantes relevantes

## Arquitetura

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│              │         │              │         │              │
│  Publisher   │────────▶│    Server    │◀────────│   Client 1   │
│              │         │              │         │              │
└──────────────┘         │  - Manages   │         │  Subscribed: │
                         │    subs      │         │  tech, sport │
┌──────────────┐         │  - Routes    │         └──────────────┘
│              │         │    news      │
│  Publisher   │────────▶│  - Stores    │         ┌──────────────┐
│              │         │    history   │         │              │
└──────────────┘         │              │◀────────│   Client 2   │
                         └──────────────┘         │              │
                                                  │  Subscribed: │
                                                  │  todas       │
                                                  └──────────────┘
```

## Características

- **Comunicação TCP persistente**: Conexões mantidas para recebimento em tempo real
- **Multi-threading**: Servidor gerencia múltiplas conexões simultâneas
- **Gerenciamento de assinaturas dinâmico**: Clientes podem adicionar/remover assinaturas durante a sessão
- **Armazenamento de notícias**: Histórico mantido em memória e arquivo JSON
- **Protocolo baseado em JSON**: Mensagens estruturadas e extensíveis
- **Interface rica**: Suporte a Rich library para formatação colorida e bonita
- **Autocomplete**: Sugestões de comandos e categorias durante digitação
- **Menus numerados**: Seleção fácil de categorias por número
- **Aliases de comandos**: Múltiplas formas de executar comandos (ex: `+`, `sub`, `INSCREVER`)

## Estrutura do Projeto

```
news-feed-pubsub/
├── src/
│   ├── common/              # Código compartilhado
│   │   ├── protocol.py      # Definições do protocolo
│   │   ├── config.py        # Configurações
│   │   └── ui_helpers.py    # Helpers de interface (Rich, emojis, formatação)
│   ├── server/              # Servidor
│   │   ├── server.py        # Servidor TCP principal
│   │   ├── subscription_manager.py  # Gerenciamento de assinaturas
│   │   └── news_storage.py  # Armazenamento de notícias
│   └── client/              # Clientes
│       ├── client.py        # Cliente leitor de notícias
│       └── publisher.py     # Publicador/editor de notícias
├── data/                    # Dados persistidos
│   └── news.json           # Histórico de notícias
├── run_server.py           # Script para iniciar servidor
├── run_client.py           # Script para iniciar cliente
├── run_publisher.py        # Script para iniciar publicador
├── requirements.txt        # Dependências (rich, prompt_toolkit)
└── README.md              # Este arquivo
```

## Categorias Disponíveis

O sistema suporta **16 categorias** (15 específicas + "todas"):

- **todas** - Inscreve em todas as categorias de uma vez
- tecnologia
- esportes
- cultura
- política
- economia
- entretenimento
- música
- saúde
- ciência
- educação
- moda
- gastronomia
- viagem
- negócios
- meio-ambiente

## Instalação

### Pré-requisitos

- Python 3.7 ou superior

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/gabriela-sotero/news-feed-pubsub
cd news-feed-pubsub
```

2. **Instale as dependências (opcional, mas recomendado)**
```bash
pip install -r requirements.txt
```

> **Nota**: As dependências (`rich` e `prompt_toolkit`) são opcionais. O sistema funciona sem elas, mas com interface mais simples. Com as bibliotecas instaladas, você terá formatação colorida, tabelas bonitas e autocomplete.

3. **Verifique a versão do Python**
```bash
python --version
# ou
python3 --version
```

## Como Rodar

### Passo 1: Iniciar o Servidor

Em um terminal, execute:

```bash
python run_server.py
```

Ou com configurações personalizadas:
```bash
python run_server.py --host 0.0.0.0 --port 5555
```

Você verá:
```
[Servidor] Iniciado em localhost:5555
[Servidor] Categorias disponíveis: ciencia, cultura, economia, educacao, entretenimento, esportes, gastronomia, meio-ambiente, moda, musica, negocios, politica, saude, tecnologia, todas, viagem
[Servidor] 25 notícias no histórico
[Servidor] Aguardando conexões...
```

### Passo 2: Iniciar Cliente(s)

Em um **novo terminal**, execute:

```bash
python run_client.py
```

O cliente iniciará com um **wizard de configuração** interativo:
1. Digite seu nome (opcional, pode deixar em branco)
2. Escolha categorias de interesse usando números separados por vírgula
3. Comece a receber notícias em tempo real!

**Comandos do cliente:**
- `INSCREVER <categoria>` ou `+ <categoria>` - Inscreve em uma ou mais categorias
- `REMOVER <categoria>` ou `- <categoria>` - Remove inscrição
- `LISTAR` ou `ls` - Lista categorias disponíveis e suas assinaturas
- `HISTORICO [categoria] [N]` ou `hist` - Ver histórico de notícias
- `HELP` ou `?` - Mostra ajuda
- `SAIR` ou `q` - Desconecta do servidor

**Aliases disponíveis:**
- INSCREVER: `sub`, `+`, `add`, `inscrever`
- REMOVER: `unsub`, `-`, `del`, `remove`, `remover`
- LISTAR: `list`, `ls`, `show`, `categorias`
- HISTORICO: `hist`, `history`, `h`, `news`
- SAIR: `exit`, `quit`, `q`, `bye`
- HELP: `ajuda`, `?`

**Exemplos de uso:**

```bash
# Inscrever em uma categoria
> INSCREVER tecnologia
> + esportes

# Inscrever em múltiplas categorias de uma vez
> INSCREVER tecnologia, esportes, cultura
> + economia negocios

# Inscrever em todas as categorias
> INSCREVER todas
> + 0

# Ver histórico
> HISTORICO
> HISTORICO tecnologia 10
> hist esportes 5

# Listar categorias
> LISTAR
> ls

# Remover assinatura
> REMOVER tecnologia
> - esportes

# Ver ajuda
> HELP
> ?

# Sair
> SAIR
> q
```

### Passo 3: Publicar Notícias

Em um **terceiro terminal**, execute:

```bash
python run_publisher.py
```

**Comandos do publicador:**
- `PUBLICAR` ou `pub` - Publica uma nova notícia (será solicitado título, lead e categoria)
- `HISTORICO` ou `hist` - Ver histórico de notícias publicadas
- `REMOVER` ou `del` - Remover notícias específicas do histórico
- `CLEAR` - Limpar todo o histórico de notícias
- `LISTAR` ou `ls` - Lista categorias disponíveis
- `HELP` ou `?` - Mostra ajuda
- `SAIR` ou `q` - Desconecta do servidor

**Exemplo de publicação:**

```bash
> PUBLICAR

--- Nova Notícia ---
Título: Nova versão do Python 3.13 lançada
Lead: Python Software Foundation anuncia nova versão com JIT compiler experimental
Categoria: tecnologia

Publicando notícia em 'tecnologia'...
✓ Notícia publicada com sucesso (ID: 26)
```

**Modo automático (para testes):**
```bash
python run_publisher.py --auto
```

## Exemplo Completo de Uso

### Terminal 1 - Servidor
```bash
$ python run_server.py
[Servidor] Iniciado em localhost:5555
[Servidor] Categorias disponíveis: ciencia, cultura, economia, educacao, entretenimento, esportes, gastronomia, meio-ambiente, moda, musica, negocios, politica, saude, tecnologia, todas, viagem
[Servidor] 25 notícias no histórico
[Servidor] Aguardando conexões...

[Servidor] Nova conexão de ('127.0.0.1', 54321)
[Cliente 127.0.0.1:54321] INSCREVER tecnologia: Inscrito em 'tecnologia' com sucesso
[Servidor] Nova conexão de ('127.0.0.1', 54322)
[Editor 127.0.0.1:54322] Nova notícia publicada em 'tecnologia': Nova versão do Python lançada
[Servidor] Distribuindo notícia de 'tecnologia' para 1 cliente(s)
```

### Terminal 2 - Cliente
```bash
$ python run_client.py

╭─────────────────────── Bem-vindo! ───────────────────────╮
│  Feed de Notícias PUB/SUB                                │
│  Sistema de notícias em tempo real                       │
│                                                           │
│  💡 Digite HELP para ver comandos                        │
│  💡 Use Tab para autocompletar                           │
╰───────────────────────────────────────────────────────────╯

[Cliente] Conectado ao servidor localhost:5555

✓ Conectado ao servidor de notícias!

📂 Categorias Disponíveis:

  0. ○ 📰 Todas
  1. ○ 🔬 Ciencia
  2. ○ 🎭 Cultura
  ...

> + tecnologia
✓ Inscrito em 'tecnologia' com sucesso

# (Ao receber notícia)
╭───────────────────── NOVA NOTÍCIA ──────────────────────╮
│  💻 Nova versão do Python lançada                       │
│                                                          │
│  Categoria: TECNOLOGIA                                   │
│                                                          │
│  Python 3.13 traz melhorias de performance e novos      │
│  recursos                                                │
│                                                          │
│  ───────────────────────────────────────────────────    │
│  2025-01-15 10:30:00                                    │
╰──────────────────────────────────────────────────────────╯
🔔
```

### Terminal 3 - Publicador
```bash
$ python run_publisher.py
[Publicador] Conectado ao servidor localhost:5555

✓ Conectado ao servidor de notícias!

=== MENU PUBLICADOR ===
1. 📝 PUBLICAR - Publicar nova notícia
2. 📚 HISTORICO - Ver histórico
3. 🗑️  REMOVER - Remover notícias
4. 🧹 CLEAR - Limpar histórico
5. 📂 LISTAR - Ver categorias
6. ❓ HELP - Ajuda
7. 🚪 SAIR - Sair

> PUBLICAR

--- Nova Notícia ---
Título: Nova versão do Python lançada
Lead: Python 3.13 traz melhorias de performance e novos recursos
Categoria (ou número): tecnologia

Publicando notícia em 'tecnologia'...
✓ Notícia publicada com sucesso (ID: 26)
```

## Protocolo de Comunicação

As mensagens são trocadas em formato JSON com terminador `\n`:

### Comandos Cliente → Servidor
```json
{"type": "INSCREVER", "data": {"category": "tecnologia"}}
{"type": "REMOVER", "data": {"category": "esportes"}}
{"type": "LISTAR", "data": {}}
{"type": "HISTORICO", "data": {"category": "tecnologia", "limit": 10}}
{"type": "SAIR", "data": {}}
```

### Comandos Publicador → Servidor
```json
{"type": "PUBLICAR", "data": {"title": "...", "lead": "...", "category": "..."}}
{"type": "HISTORICO", "data": {"category": "", "limit": 50}}
{"type": "LIMPAR", "data": {}}
{"type": "REMOVER_NOTICIAS", "data": {"news_ids": [1, 2, 3]}}
```

### Respostas Servidor → Cliente
```json
{"type": "NOTICIA", "data": {"title": "...", "lead": "...", "category": "...", "timestamp": "..."}}
{"type": "SUCESSO", "data": {"message": "..."}}
{"type": "ERRO", "data": {"message": "..."}}
{"type": "CATEGORIAS", "data": {"categories": [...]}}
{"type": "HISTORICO", "data": {"news": [...]}}
```

## Testando o Sistema Completo

Para testar todas as funcionalidades:

1. **Inicie o servidor**
```bash
# Terminal 1
python run_server.py
```

2. **Inicie múltiplos clientes**
```bash
# Terminal 2
python run_client.py
# Inscreva em: tecnologia, esportes

# Terminal 3
python run_client.py
# Inscreva em: todas
```

3. **Inicie o publicador**
```bash
# Terminal 4
python run_publisher.py
```

4. **Teste os recursos:**
   - Publique notícias em diferentes categorias
   - Observe que cada cliente recebe apenas notícias das categorias assinadas
   - Use `HISTORICO` para ver notícias passadas
   - Use `INSCREVER` e `REMOVER` dinamicamente
   - Teste a categoria "todas"
   - Use aliases e números para comandos

## Armazenamento

As notícias são armazenadas em:
- **Memória**: Para distribuição rápida aos clientes conectados
- **Arquivo**: `data/news.json` para persistência entre reinicializações

O histórico mantém até 100 notícias (configurável em `src/common/config.py`).

Exemplo de `data/news.json`:
```json
[
  {
    "id": 1,
    "title": "Nova versão do Python 3.13 lançada",
    "lead": "Python Software Foundation anuncia nova versão com JIT compiler experimental",
    "category": "tecnologia",
    "timestamp": "2025-01-15T10:30:00"
  }
]
```

## Configurações

Edite `src/common/config.py` para alterar:

```python
# Configurações de rede
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
ENCODING = "utf-8"

# Categorias disponíveis (16 categorias)
DEFAULT_CATEGORIES = [
    "todas",
    "tecnologia",
    "esportes",
    # ... mais categorias
]

# Configurações de armazenamento
NEWS_STORAGE_FILE = "data/news.json"
MAX_NEWS_HISTORY = 100
```

## Funcionalidades Implementadas

### Core
- ✅ Servidor TCP com suporte a múltiplas conexões simultâneas
- ✅ Sistema de assinaturas por categoria (16 categorias)
- ✅ Distribuição em tempo real de notícias
- ✅ Gerenciamento dinâmico de assinaturas
- ✅ Armazenamento persistente de notícias
- ✅ Protocolo baseado em JSON
- ✅ Thread-safe com locks apropriados

### Cliente
- ✅ Interface interativa com Rich (cores, tabelas, formatação)
- ✅ Wizard de configuração inicial
- ✅ Autocomplete com prompt_toolkit
- ✅ Aliases de comandos (múltiplas formas de executar)
- ✅ Menus numerados para categorias
- ✅ Inscrição em múltiplas categorias de uma vez
- ✅ Categoria "todas" para inscrição em massa
- ✅ Comando HISTORICO para consultar notícias passadas
- ✅ Emojis específicos por categoria

### Publicador
- ✅ Publicador interativo e automático
- ✅ Comando HISTORICO para ver notícias publicadas
- ✅ Comando REMOVER para deletar notícias específicas
- ✅ Comando CLEAR para limpar histórico completo
- ✅ Interface com menus numerados
- ✅ Validação de categorias

## Dependências

O projeto usa:
- **Python Standard Library** (socket, threading, json, etc.)
- **rich** (opcional) - Interface bonita com cores e tabelas
- **prompt_toolkit** (opcional) - Autocomplete e histórico de comandos

```bash
pip install rich prompt_toolkit
```

> Sem as dependências opcionais, o sistema funciona em modo texto simples.

## Solução de Problemas

### Porta já em uso
```bash
# Use uma porta diferente
python run_server.py --port 5556
python run_client.py --port 5556
```

### Erro de conexão
- Verifique se o servidor está rodando
- Verifique se está usando a mesma porta em todos os componentes
- Verifique o firewall

### Cache do Python
```bash
# Limpe o cache se encontrar problemas
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## Possíveis Extensões

- Autenticação de clientes
- Filtros avançados (por palavra-chave, data, etc.)
- Interface web ou GUI
- Notificações push
- Métricas e estatísticas em tempo real
- Suporte a SSL/TLS para segurança
- API REST complementar
- Banco de dados SQL para histórico
- Sistema de favoritos por usuário
- Busca full-text no histórico

## Licença

MIT
