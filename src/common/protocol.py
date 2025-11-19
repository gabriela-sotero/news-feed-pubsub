"""
Protocolo de comunicação para o sistema PUB/SUB de notícias.
Define os comandos e formato das mensagens trocadas entre cliente e servidor.
"""

import json
from typing import Dict, Any, List


class MessageType:
    """Tipos de mensagens do protocolo"""
    # Cliente -> Servidor
    SUBSCRIBE = "INSCREVER"
    UNSUBSCRIBE = "REMOVER"
    LIST_CATEGORIES = "LISTAR"
    HISTORY = "HISTORICO"
    DISCONNECT = "SAIR"

    # Editor -> Servidor
    PUBLISH = "PUBLICAR"

    # Servidor -> Cliente
    NEWS_UPDATE = "NOTICIA"
    NEWS_HISTORY = "HISTORICO_LISTA"
    SUCCESS = "SUCESSO"
    ERROR = "ERRO"
    CATEGORIES_LIST = "CATEGORIAS"


class Message:
    """Classe para encapsular mensagens do protocolo"""

    @staticmethod
    def create(msg_type: str, data: Dict[str, Any] = None) -> str:
        """
        Cria uma mensagem no formato JSON.

        Args:
            msg_type: Tipo da mensagem (MessageType)
            data: Dados adicionais da mensagem

        Returns:
            String JSON da mensagem com terminador \\n
        """
        message = {
            "type": msg_type,
            "data": data or {}
        }
        return json.dumps(message, ensure_ascii=False) + "\n"

    @staticmethod
    def parse(raw_message: str) -> Dict[str, Any]:
        """
        Faz parse de uma mensagem recebida.

        Args:
            raw_message: String JSON da mensagem

        Returns:
            Dicionário com type e data
        """
        try:
            return json.loads(raw_message.strip())
        except json.JSONDecodeError:
            return {"type": MessageType.ERROR, "data": {"message": "Formato inválido"}}

    @staticmethod
    def subscribe(category: str) -> str:
        """Cria mensagem de inscrição em categoria"""
        return Message.create(MessageType.SUBSCRIBE, {"category": category})

    @staticmethod
    def unsubscribe(category: str) -> str:
        """Cria mensagem de remoção de inscrição"""
        return Message.create(MessageType.UNSUBSCRIBE, {"category": category})

    @staticmethod
    def publish_news(title: str, summary: str, category: str) -> str:
        """Cria mensagem de publicação de notícia"""
        return Message.create(MessageType.PUBLISH, {
            "title": title,
            "summary": summary,
            "category": category
        })

    @staticmethod
    def news_update(title: str, summary: str, category: str) -> str:
        """Cria mensagem de atualização de notícia para cliente"""
        return Message.create(MessageType.NEWS_UPDATE, {
            "title": title,
            "summary": summary,
            "category": category
        })

    @staticmethod
    def success(message: str) -> str:
        """Cria mensagem de sucesso"""
        return Message.create(MessageType.SUCCESS, {"message": message})

    @staticmethod
    def error(message: str) -> str:
        """Cria mensagem de erro"""
        return Message.create(MessageType.ERROR, {"message": message})

    @staticmethod
    def categories_list(categories: List[str]) -> str:
        """Cria mensagem com lista de categorias"""
        return Message.create(MessageType.CATEGORIES_LIST, {"categories": categories})

    @staticmethod
    def request_history(category: str = None, limit: int = 10) -> str:
        """Cria mensagem de solicitação de histórico"""
        data = {"limit": limit}
        if category:
            data["category"] = category
        return Message.create(MessageType.HISTORY, data)

    @staticmethod
    def news_history(news_list: List[Dict[str, Any]]) -> str:
        """Cria mensagem com lista de notícias do histórico"""
        return Message.create(MessageType.NEWS_HISTORY, {"news": news_list})
