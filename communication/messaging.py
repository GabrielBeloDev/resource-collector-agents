from typing import Dict, List


class MessageBus:
    def __init__(self):
        self.messages: Dict[str, List[dict]] = {}
        self.registered: set[str] = set()

    def register(self, agent_id: str):
        if agent_id not in self.messages:
            self.messages[agent_id] = []
            self.registered.add(agent_id)

    def send(self, recipient_id: str, content: dict):
        if recipient_id == "broadcast":
            for rid in self.registered:
                self.messages[rid].append(content)
        else:
            if recipient_id not in self.messages:
                self.register(recipient_id)
            self.messages[recipient_id].append(content)

    def receive(self, recipient_id: str):
        inbox = self.messages.get(recipient_id, [])
        self.messages[recipient_id] = []
        return inbox
