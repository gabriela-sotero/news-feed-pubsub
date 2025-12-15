#!/usr/bin/env python3
"""Publicador de notícias via MQTT."""

import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt

DEFAULT_BROKER = "test.mosquitto.org"
DEFAULT_PORT = 1883
TOPIC_PREFIX = "grupo04/news"

CATEGORIES = [
    "tecnologia", "esportes", "cultura", "politica", "economia",
    "entretenimento", "musica", "saude", "ciencia", "educacao",
    "moda", "gastronomia", "viagem", "negocios", "meio-ambiente"
]


class NewsPublisher:
    def __init__(self, broker=DEFAULT_BROKER, port=DEFAULT_PORT):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"publisher_{int(time.time())}"
        )
        self.connected = False
        self.client.on_connect = self._on_connect

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            print(f"✓ Conectado ao broker: {self.broker}:{self.port}\n")
        else:
            print(f"✗ Erro de conexão: {reason_code}")

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(1)
            return self.connected
        except:
            return False

    def publish(self, title, lead, category):
        if category not in CATEGORIES:
            print(f"✗ Categoria inválida")
            return

        news = {
            "title": title,
            "lead": lead,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }

        topic = f"{TOPIC_PREFIX}/{category}"
        self.client.publish(topic, json.dumps(news), qos=1)
        print(f"✓ Publicado em '{category}'")

    def run(self):
        if not self.connect():
            print("✗ Erro ao conectar")
            return

        print("Comandos: PUBLICAR, LISTAR, SAIR\n")

        try:
            while self.connected:
                try:
                    cmd = input('> ').strip().upper()

                    if cmd == "PUBLICAR":
                        print("\n--- Nova Notícia ---")
                        title = input("Título: ").strip()
                        lead = input("Lead: ").strip()
                        print(f"\nCategorias: {', '.join(CATEGORIES)}")
                        category = input("Categoria: ").strip().lower()

                        if title and lead and category:
                            self.publish(title, lead, category)
                            print()

                    elif cmd == "LISTAR":
                        print("\nCategorias:")
                        for cat in CATEGORIES:
                            print(f"  • {cat}")
                        print()

                    elif cmd in ["SAIR", "Q"]:
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
    args = parser.parse_args()

    publisher = NewsPublisher(args.broker, args.port)
    publisher.run()


if __name__ == "__main__":
    main()
