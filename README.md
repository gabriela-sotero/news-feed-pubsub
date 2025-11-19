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
                                                  │  culture     │
                                                  └──────────────┘
```

## Características

- **Comunicação TCP persistente**: Conexões mantidas para recebimento em tempo real
- **Multi-threading**: Servidor gerencia múltiplas conexões simultâneas
- **Gerenciamento de assinaturas dinâmico**: Clientes podem adicionar/remover assinaturas durante a sessão
- **Armazenamento de notícias**: Histórico mantido em memória e arquivo JSON
- **Protocolo baseado em JSON**: Mensagens estruturadas e extensíveis

## Estrutura do Projeto

```
news-feed-pubsub/
├── src/
│   ├── common/              # Código compartilhado
│   │   ├── protocol.py      # Definições do protocolo
│   │   └── config.py        # Configurações
│   ├── server/              # Servidor
│   │   ├── server.py        # Servidor TCP principal
│   │   ├── subscription_manager.py  # Gerenciamento de assinaturas
│   │   └── news_storage.py  # Armazenamento de notícias
│   └── client/              # Clientes
│       ├── client.py        # Cliente leitor de notícias
│       └── publisher.py     # Publicador/editor de notícias
├── data/                    # Dados persistidos
├── run_server.py           # Script para iniciar servidor
├── run_client.py           # Script para iniciar cliente
├── run_publisher.py        # Script para iniciar publicador
├── requirements.txt        # Dependências (apenas stdlib)
└── README.md              # Este arquivo
```

## Categorias Disponíveis

- tecnologia
- esportes
- cultura
- política
- economia
- entretenimento

## Instalação

Não há dependências externas. Usa apenas a biblioteca padrão do Python.

```bash
# Clone o repositório
git clone https://github.com/gabriela-sotero/news-feed-pubsub
cd news-feed-pubsub

# Python 3.7+ é necessário
python --version
```

## Uso

### 1. Iniciar o Servidor

```bash
python run_server.py
```

Opções:
```bash
python run_server.py --host 0.0.0.0 --port 5555
```

### 2. Iniciar Cliente(s)

Em outro terminal:

```bash
python run_client.py
```

**Comandos do cliente:**
- `INSCREVER <categoria>` - Inscreve em uma categoria
- `REMOVER <categoria>` - Remove inscrição de uma categoria
- `LISTAR` - Lista categorias disponíveis e suas assinaturas
- `SAIR` - Desconecta do servidor

**Exemplos:**
```
> INSCREVER tecnologia
> INSCREVER esportes
> LISTAR
> REMOVER tecnologia
> SAIR
```

### 3. Publicar Notícias

Em outro terminal:

#### Modo Interativo
```bash
python run_publisher.py
```

**Comandos do publicador:**
- `PUBLICAR` - Publica uma nova notícia (será solicitado título, resumo e categoria)
- `LISTAR` - Lista categorias disponíveis
- `SAIR` - Desconecta do servidor

#### Modo Automático (para testes)
```bash
python run_publisher.py --auto
```

Publica 5 notícias de exemplo automaticamente.

## Exemplo de Uso

### Terminal 1 - Servidor
```bash
$ python run_server.py
[Servidor] Iniciado em localhost:5555
[Servidor] Categorias disponíveis: cultura, economia, entretenimento, esportes, política, tecnologia
[Servidor] 0 notícias no histórico
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
[Cliente] Conectado ao servidor localhost:5555

✓ Conectado ao servidor de notícias! Categorias: cultura, economia, entretenimento, esportes, política, tecnologia

> INSCREVER tecnologia
✓ Inscrito em 'tecnologia' com sucesso
>
============================================================
📰 NOVA NOTÍCIA - [TECNOLOGIA]
============================================================
Título: Nova versão do Python lançada
Resumo: Python 3.12 traz melhorias de performance e novos recursos
============================================================

> SAIR
```

### Terminal 3 - Publicador
```bash
$ python run_publisher.py
[Publicador] Conectado ao servidor localhost:5555

=== PUBLICADOR DE NOTÍCIAS ===

> PUBLICAR

--- Nova Notícia ---
Título: Nova versão do Python lançada
Resumo: Python 3.12 traz melhorias de performance e novos recursos
Categoria: tecnologia

Publicando notícia em 'tecnologia'...
✓ Notícia publicada com sucesso (ID: 1)
> SAIR
```

## Protocolo de Comunicação

As mensagens são trocadas em formato JSON com terminador `\n`:

### Comandos Cliente → Servidor
```json
{"type": "INSCREVER", "data": {"category": "tecnologia"}}
{"type": "REMOVER", "data": {"category": "esportes"}}
{"type": "LISTAR", "data": {}}
{"type": "SAIR", "data": {}}
```

### Comandos Publicador → Servidor
```json
{"type": "PUBLICAR", "data": {"title": "...", "summary": "...", "category": "..."}}
```

### Respostas Servidor → Cliente
```json
{"type": "NOTICIA", "data": {"title": "...", "summary": "...", "category": "..."}}
{"type": "SUCESSO", "data": {"message": "..."}}
{"type": "ERRO", "data": {"message": "..."}}
{"type": "CATEGORIAS", "data": {"categories": [...]}}
```

## Testando o Sistema

Para testar o sistema completo:

1. Inicie o servidor em um terminal
2. Inicie múltiplos clientes em terminais diferentes
3. Inscreva cada cliente em diferentes combinações de categorias
4. Use o publicador automático para enviar notícias de teste
5. Observe que cada cliente recebe apenas notícias das categorias assinadas

```bash
# Terminal 1
python run_server.py

# Terminal 2
python run_client.py
# > INSCREVER tecnologia
# > INSCREVER esportes

# Terminal 3
python run_client.py
# > INSCREVER cultura

# Terminal 4
python run_publisher.py --auto
```

## Armazenamento

As notícias são armazenadas em:
- **Memória**: Para distribuição rápida
- **Arquivo**: `data/news.json` para persistência

O histórico mantém até 100 notícias (configurável em `src/common/config.py`).

## Configurações

Edite `src/common/config.py` para alterar:
- Host e porta padrão
- Tamanho do buffer
- Categorias disponíveis
- Arquivo de armazenamento
- Tamanho máximo do histórico

## Funcionalidades Implementadas

- ✅ Servidor TCP com suporte a múltiplas conexões simultâneas
- ✅ Sistema de assinaturas por categoria
- ✅ Distribuição em tempo real de notícias
- ✅ Gerenciamento dinâmico de assinaturas
- ✅ Armazenamento persistente de notícias
- ✅ Cliente interativo para leitura
- ✅ Publicador interativo e automático
- ✅ Protocolo baseado em JSON
- ✅ Thread-safe com locks apropriados

## Possíveis Extensões

- Autenticação de clientes
- Filtros avançados (por palavra-chave, data, etc.)
- Interface web
- Histórico de notícias por cliente
- Métricas e estatísticas
- Suporte a SSL/TLS
- API REST complementar

## Licença

MIT
