# Sistema de Feed de Notícias - Implementações de Rede

Este repositório contém diferentes implementações de um sistema de feed de notícias utilizando diversos protocolos de rede.

## Estrutura do Projeto

```
news-feed-pubsub/
├── tcp/                   # Implementação TCP (Sockets TCP)
│   ├── server.py         # Servidor TCP PUB/SUB
│   ├── client.py         # Cliente leitor de notícias
│   ├── publisher.py      # Publicador/editor de notícias
│   ├── data/             # Dados persistidos
│   ├── requirements.txt  # Dependências Python
│   └── README.md         # Documentação detalhada
├── mqtt/                  # Implementação MQTT (Message Broker)
│   ├── publisher.py      # Publicador via MQTT
│   ├── client.py         # Cliente via MQTT
│   ├── requirements.txt  # Dependência: paho-mqtt
│   └── README.md         # Documentação detalhada
└── README.md             # Este arquivo
```

## Implementações Disponíveis

### TCP - Sistema PUB/SUB com Sockets TCP

Sistema distribuído cliente-servidor usando Sockets TCP que funciona como um feed de notícias contínuo baseado no modelo **PUB/SUB (Publisher/Subscriber)**.

**Características:**
- Comunicação TCP persistente
- Multi-threading para múltiplas conexões simultâneas
- Gerenciamento de assinaturas dinâmico
- 16 categorias de notícias
- Armazenamento persistente em JSON
- Interface rica com cores e autocomplete
- Protocolo baseado em JSON

**Documentação completa:** [tcp/README.md](tcp/README.md)

**Início rápido:**
```bash
# Terminal 1 - Servidor
cd tcp
python server.py

# Terminal 2 - Cliente
cd tcp
python client.py

# Terminal 3 - Publicador
cd tcp
python publisher.py
```

### MQTT - Sistema com Broker MQTT

Sistema de feed de notícias usando **MQTT (Message Queuing Telemetry Transport)** - protocolo de mensageria assíncrona leve, ideal para IoT e sistemas distribuídos.

**Características:**
- Arquitetura Pub/Sub via Broker
- Protocolo MQTT sobre TCP
- QoS 1 (entrega garantida)
- 15 categorias de notícias
- Sem necessidade de servidor customizado
- Broker público ou local (Mosquitto)
- Código mais simples e desacoplado

**Documentação completa:** [mqtt/README.md](mqtt/README.md)

**Início rápido:**
```bash
# Terminal 1 - Client
cd mqtt
python client.py

# Terminal 2 - Publisher
cd mqtt
python publisher.py
```

**Nota:** Por padrão usa broker público `test.mosquitto.org`. Para usar broker local, instale Mosquitto e adicione `--broker localhost`.

## Comparação TCP vs MQTT

| Aspecto | TCP | MQTT |
|---------|-----|------|
| **Arquitetura** | Cliente-Servidor direto | Pub/Sub via Broker |
| **Servidor** | Customizado (server.py) | Broker padrão (Mosquitto) |
| **Complexidade** | Alta (~300 linhas) | Baixa (~150 linhas) |
| **Histórico** | Sim (em memória + JSON) | Não (fire-and-forget) |
| **Escalabilidade** | Limitada | Alta |
| **Uso** | Controle total | Padrão industrial |

## Requisitos Gerais

- Python 3.7 ou superior
- Dependências específicas em cada implementação

## Licença

MIT
