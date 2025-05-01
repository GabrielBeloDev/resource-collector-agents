from typing import Dict, List


class MessageBus:
    def __init__(self):
        self.messages: Dict[str, List[dict]] = {}

    def send(self, recipient_id: str, content: dict):
        if recipient_id not in self.messages:
            self.messages[recipient_id] = []
        self.messages[recipient_id].append(content)

    def receive(self, recipient_id: str):
        msgs = self.messages.get(recipient_id, [])
        self.messages[recipient_id] = []
        return msgs
