#!/usr/bin/env python3
"""Cliente de notícias via MQTT."""

import json
import time
import paho.mqtt.client as mqtt

DEFAULT_BROKER = "test.mosquitto.org"
DEFAULT_PORT = 1883
TOPIC_PREFIX = "grupo04/news"

CATEGORIES = [
    "tecnologia", "esportes", "cultura", "politica", "economia",
    "entretenimento", "musica", "saude", "ciencia", "educacao",
    "moda", "gastronomia", "viagem", "negocios", "meio-ambiente"
]


class NewsClient:
    def __init__(self, broker=DEFAULT_BROKER, port=DEFAULT_PORT):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"client_{int(time.time())}"
        )
        self.connected = False
        self.subscriptions = set()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            print(f"✓ Conectado ao broker: {self.broker}:{self.port}\n")
            for category in self.subscriptions.copy():
                topic = f"{TOPIC_PREFIX}/{category}"
                self.client.subscribe(topic, qos=1)
        else:
            print(f"✗ Erro de conexão: {reason_code}")

    def _on_message(self, client, userdata, msg):
        try:
            news = json.loads(msg.payload.decode())
            print(f"\n{'='*60}")
            print(f"📰 [{news['category'].upper()}] {news['title']}")
            print(f"{'='*60}")
            print(f"{news['lead']}")
            print(f"{'='*60}\n> ", end="", flush=True)
        except:
            pass

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(1)
            return self.connected
        except:
            return False

    def subscribe(self, categories):
        if isinstance(categories, str):
            categories = [categories]

        for cat in categories:
            cat = cat.strip().lower()

            if cat == "todas":
                for c in CATEGORIES:
                    self.subscriptions.add(c)
                    self.client.subscribe(f"{TOPIC_PREFIX}/{c}", qos=1)
                print("✓ Inscrito em todas as categorias")
                return

            if cat in CATEGORIES:
                self.subscriptions.add(cat)
                self.client.subscribe(f"{TOPIC_PREFIX}/{cat}", qos=1)
                print(f"✓ Inscrito em '{cat}'")
            else:
                print(f"✗ Categoria inválida: {cat}")

    def unsubscribe(self, categories):
        if isinstance(categories, str):
            categories = [categories]

        for cat in categories:
            cat = cat.strip().lower()
            if cat in self.subscriptions:
                self.subscriptions.remove(cat)
                self.client.unsubscribe(f"{TOPIC_PREFIX}/{cat}")
                print(f"✓ Removido de '{cat}'")

    def list_categories(self):
        print("\nCategorias:")
        for cat in CATEGORIES:
            status = "✓" if cat in self.subscriptions else "○"
            print(f"  {status} {cat}")
        print()

    def run(self):
        if not self.connect():
            print("✗ Erro ao conectar")
            return

        print("Comandos: INSCREVER <cat>, REMOVER <cat>, LISTAR, SAIR\n")

        try:
            while self.connected:
                try:
                    cmd = input('> ').strip().split(maxsplit=1)
                    if not cmd:
                        continue

                    if cmd[0].upper() in ["INSCREVER", "+"]:
                        if len(cmd) > 1:
                            self.subscribe(cmd[1].replace(',', ' ').split())

                    elif cmd[0].upper() in ["REMOVER", "-"]:
                        if len(cmd) > 1:
                            self.unsubscribe(cmd[1].replace(',', ' ').split())

                    elif cmd[0].upper() == "LISTAR":
                        self.list_categories()

                    elif cmd[0].upper() in ["SAIR", "Q"]:
                        break

                except (EOFError, KeyboardInterrupt):
                    break
        finally:
            self.client.loop_stop()
            self.client.disconnect()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default=DEFAULT_BROKER)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--subscribe", "-s", nargs="+")
    args = parser.parse_args()

    client = NewsClient(args.broker, args.port)

    if client.connect() and args.subscribe:
        client.subscribe(args.subscribe)
        print()

    client.run()


if __name__ == "__main__":
    main()
