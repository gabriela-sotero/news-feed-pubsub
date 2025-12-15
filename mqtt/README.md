# Sistema de Feed de Notícias - MQTT

Sistema de feed de notícias usando **MQTT (Message Queuing Telemetry Transport)** - um protocolo de mensageria assíncrona leve e eficiente, ideal para IoT e sistemas distribuídos.

## Descrição

O sistema permite que:
- **Publishers** publiquem notícias em tópicos MQTT por categoria
- **Subscribers** se inscrevam em categorias de interesse e recebam notícias em tempo real
- **Broker MQTT** gerencie toda a comunicação entre publicadores e assinantes

## Arquitetura

```
┌──────────────┐                    ┌──────────────┐
│              │                    │              │
│  Publisher 1 │─────┐         ┌────│ Subscriber 1 │
│              │     │         │    │              │
└──────────────┘     │         │    │ Inscrito em: │
                     ▼         ▼    │ tech, sport  │
┌──────────────┐  ┌─────────────┐  └──────────────┘
│              │  │             │
│  Publisher 2 │─▶│   BROKER    │  ┌──────────────┐
│              │  │    MQTT     │  │              │
└──────────────┘  │             │◀─│ Subscriber 2 │
                  │  - Tópicos  │  │              │
                  │  - Routing  │  │ Inscrito em: │
                  │  - QoS      │  │ todas        │
                  └─────────────┘  └──────────────┘
```

### Diferenças vs TCP

| Aspecto | TCP (antes) | MQTT (agora) |
|---------|-------------|--------------|
| **Arquitetura** | Cliente-Servidor direto | Pub/Sub via Broker |
| **Conexão** | Ponto-a-ponto | Intermediário (Broker) |
| **Protocolo** | Socket TCP raw | MQTT sobre TCP |
| **Mensagens** | Necessário gerenciar buffer | Broker gerencia tudo |
| **Histórico** | Servidor mantém | Não mantém (fire-and-forget)* |
| **Escalabilidade** | Limitada | Alta (broker gerencia) |
| **Código** | ~300 linhas (servidor) | Não precisa de servidor |

*MQTT puro não mantém histórico. Para histórico, seria necessário adicionar persistência externa.

## Características

- **Protocolo MQTT**: Leve, assíncrono e eficiente
- **Broker intermediário**: Desacopla publicadores de assinantes
- **QoS 1**: Mensagens entregues pelo menos uma vez
- **15 categorias de notícias**: Tópicos separados por categoria
- **Suporte a "todas"**: Inscrição em múltiplas categorias de uma vez
- **Interface simples**: Comandos diretos e fáceis de usar
- **Broker público**: Usa test.mosquitto.org por padrão (ou configure local)

## Estrutura do Projeto

```
mqtt/
├── publisher.py       # Publicador de notícias
├── client.py          # Cliente/assinante de notícias
├── requirements.txt   # Dependência: paho-mqtt
└── README.md         # Este arquivo
```

## Categorias Disponíveis

O sistema suporta **15 categorias** + "todas":

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

## Tópicos MQTT

As mensagens são publicadas em tópicos no formato:

```
news/tecnologia
news/esportes
news/cultura
...
```

## Instalação

### Pré-requisitos

- Python 3.7 ou superior
- Broker MQTT (uma destas opções):
  - **Opção 1**: Usar broker público `test.mosquitto.org` (padrão, sem instalação)
  - **Opção 2**: Instalar Mosquitto localmente

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/gabriela-sotero/news-feed-pubsub
cd news-feed-pubsub/mqtt
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **(Opcional) Instale Mosquitto local**

**Linux/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

**macOS:**
```bash
brew install mosquitto
brew services start mosquitto
```

**Windows:**
- Baixe de: https://mosquitto.org/download/
- Instale e inicie o serviço

## Como Rodar

### Opção 1: Usando Broker Público (Mais Fácil)

Por padrão, o sistema usa `test.mosquitto.org` - não precisa instalar nada!

**Terminal 1 - Client:**
```bash
cd mqtt
python client.py
```

**Terminal 2 - Publisher:**
```bash
cd mqtt
python publisher.py
```

### Opção 2: Usando Broker Local

Se instalou Mosquitto local:

**Terminal 1 - Broker (se não estiver como serviço):**
```bash
mosquitto
```

**Terminal 2 - Client:**
```bash
cd mqtt
python client.py --broker localhost
```

**Terminal 3 - Publisher:**
```bash
cd mqtt
python publisher.py --broker localhost
```

## Comandos

### Client (Cliente)

```
INSCREVER <categoria>  - Inscreve em uma ou mais categorias
  Aliases: SUB, +

REMOVER <categoria>    - Remove inscrição
  Aliases: UNSUB, -

LISTAR                 - Lista categorias disponíveis
  Aliases: LS

SAIR                   - Desconecta do broker
  Aliases: QUIT, Q
```

**Exemplos:**
```bash
# Inscrever em uma categoria
> INSCREVER tecnologia
> + esportes

# Inscrever em múltiplas categorias
> INSCREVER tecnologia esportes cultura
> SUB economia, negocios

# Inscrever em todas
> INSCREVER todas

# Listar categorias
> LISTAR

# Remover assinatura
> REMOVER tecnologia
> - esportes

# Sair
> SAIR
```

**Argumentos CLI:**
```bash
# Inscrever automaticamente ao iniciar
cd mqtt
python client.py --subscribe tecnologia esportes

# Usar broker diferente
cd mqtt
python client.py --broker localhost --port 1883
```

### Publisher

```
PUBLICAR  - Publica nova notícia
  Aliases: PUB

LISTAR    - Lista categorias disponíveis
  Aliases: LS

SAIR      - Desconecta do broker
  Aliases: QUIT, Q
```

**Exemplos:**
```bash
# Publicar notícia
> PUBLICAR

--- Nova Notícia ---
Título: Python 3.13 lançado
Lead: Nova versão traz JIT compiler experimental
Categoria: tecnologia

✓ Notícia publicada em 'news/tecnologia'

# Listar categorias
> LISTAR

# Sair
> SAIR
```

## Exemplo Completo de Uso

### Terminal 1 - Subscriber
```bash
$ python client.py --subscribe tecnologia esportes

Conectando ao broker test.mosquitto.org:1883...
✓ Conectado ao broker MQTT: test.mosquitto.org:1883

✓ Inscrito em 'tecnologia'
✓ Inscrito em 'esportes'

Comandos:
  INSCREVER <cat> - Inscreve em categoria (ou 'todas')
  REMOVER <cat>   - Remove inscrição
  LISTAR          - Lista categorias
  SAIR            - Desconecta

>

# (Recebe notícia)
============================================================
📰 NOVA NOTÍCIA - [TECNOLOGIA]
============================================================
Título: Python 3.13 lançado
Lead: Nova versão traz JIT compiler experimental
Hora: 2025-12-15T10:30:00
============================================================
>
```

### Terminal 2 - Publisher
```bash
$ python publisher.py

Conectando ao broker test.mosquitto.org:1883...
✓ Conectado ao broker MQTT: test.mosquitto.org:1883

Comandos: PUBLICAR, LISTAR, SAIR

> PUBLICAR

--- Nova Notícia ---
Título: Python 3.13 lançado
Lead: Nova versão traz JIT compiler experimental
Categoria: tecnologia

✓ Notícia publicada em 'news/tecnologia'

>
```

## Formato das Mensagens

As notícias são publicadas em JSON:

```json
{
  "title": "Python 3.13 lançado",
  "lead": "Nova versão traz JIT compiler experimental",
  "category": "tecnologia",
  "timestamp": "2025-12-15T10:30:00.123456"
}
```

## Níveis de QoS (Quality of Service)

O sistema usa **QoS 1** (pelo menos uma vez):
- **QoS 0**: Fire and forget (não garante entrega)
- **QoS 1**: Pelo menos uma vez (garante entrega, pode duplicar) ✓ Usado
- **QoS 2**: Exatamente uma vez (mais lento, sem duplicatas)

## Testando o Sistema

1. **Inicie um subscriber**
```bash
cd mqtt
python client.py --subscribe todas
```

2. **Inicie outro subscriber com categorias específicas**
```bash
# Em outro terminal
cd mqtt
python client.py --subscribe tecnologia
```

3. **Inicie o publisher e publique notícias**
```bash
# Em outro terminal
cd mqtt
python publisher.py
> PUBLICAR
```

4. **Observe**:
   - Primeiro subscriber recebe todas as notícias
   - Segundo subscriber recebe apenas de "tecnologia"
   - Mensagens aparecem em tempo real

## Broker Público vs Local

### Broker Público (test.mosquitto.org)

**Vantagens:**
- Sem instalação necessária
- Funciona imediatamente
- Bom para testes e demonstrações

**Desvantagens:**
- Outros podem ver suas mensagens (público)
- Depende de conexão com internet
- Pode ter latência maior

### Broker Local (Mosquitto)

**Vantagens:**
- Privado e seguro
- Baixa latência
- Controle total

**Desvantagens:**
- Precisa instalar software
- Precisa gerenciar o serviço

## Configurações Avançadas

### Broker Customizado

```bash
# Usar broker privado
cd mqtt
python publisher.py --broker mqtt.example.com --port 1883
cd mqtt
python client.py --broker mqtt.example.com --port 1883
```

### Múltiplos Subscribers

Você pode rodar quantos subscribers quiser:

```bash
# Terminal 1
cd mqtt
python client.py --subscribe tecnologia

# Terminal 2
cd mqtt
python client.py --subscribe esportes

# Terminal 3
cd mqtt
python client.py --subscribe todas
```

Todos recebem as notícias das categorias que assinaram!

## Solução de Problemas

### Erro de conexão com broker público
```
✗ Erro ao conectar: [Errno 8] nodename nor servname provided
```

**Solução**: Verifique sua conexão com internet ou use broker local:
```bash
mosquitto &
cd mqtt
python client.py --broker localhost
```

### Mensagens não chegam

1. Verifique se subscriber está inscrito na categoria:
```bash
> LISTAR
```

2. Verifique se está usando o mesmo broker:
```bash
# Ambos devem usar o mesmo broker
cd mqtt
python publisher.py --broker localhost
cd mqtt
python client.py --broker localhost
```

3. Verifique se o broker está rodando:
```bash
# Se local
ps aux | grep mosquitto
```

### Importar paho.mqtt falha

```bash
pip install paho-mqtt
```

## Comparação com Versão TCP

### O que mudou?

**Removido:**
- `server.py` - Não precisa mais de servidor customizado
- Lógica de socket TCP (accept, connect, send, recv)
- Gerenciamento de buffer e threading manual
- Armazenamento de histórico em servidor

**Adicionado:**
- Biblioteca `paho-mqtt`
- Conexão via broker MQTT
- Sistema de tópicos
- Callbacks assíncronos

**Mantido:**
- Categorias de notícias
- Comandos INSCREVER/REMOVER/LISTAR
- Formato JSON das mensagens
- Interface de linha de comando

### Vantagens MQTT

1. **Código mais simples**: ~150 linhas vs ~300+ (sem servidor)
2. **Mais escalável**: Broker gerencia milhares de conexões
3. **Desacoplamento**: Publisher não sabe quem são os subscribers
4. **Padrão industrial**: Usado em IoT, mobile, web
5. **Broker robusto**: Mosquitto é maduro e confiável

### Desvantagens MQTT

1. **Sem histórico nativo**: MQTT não armazena mensagens antigas
2. **Dependência externa**: Precisa de broker rodando
3. **Fire-and-forget**: Mensagens enviadas só chegam em quem está conectado

## Possíveis Extensões

- Adicionar persistência com banco de dados
- Autenticação no broker (usuário/senha)
- SSL/TLS para segurança
- Retained messages para última notícia
- Will messages para notificar desconexões
- Bridge entre brokers
- Interface web (via WebSocket MQTT)
- Métricas e monitoramento

## Recursos Úteis

- **MQTT.org**: https://mqtt.org/
- **Mosquitto**: https://mosquitto.org/
- **Paho MQTT Python**: https://www.eclipse.org/paho/index.php?page=clients/python/index.php
- **MQTT Explorer** (GUI): http://mqtt-explorer.com/
- **Broker público de teste**: https://test.mosquitto.org/

## Licença

MIT
