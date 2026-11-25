"""Agent classes for the QuickBite food delivery system (Lab 8)."""


class AgentDescriptor:
    def __init__(self, name, agent_type, responsibilities, percepts, actions,
                 goals, protocols, characteristics):
        self.name = name
        self.type = agent_type
        self.responsibilities = responsibilities
        self.percepts = percepts
        self.actions = actions
        self.goals = goals
        self.protocols = protocols
        self.characteristics = characteristics

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "responsibilities": self.responsibilities,
            "percepts": self.percepts,
            "actions": self.actions,
            "goals": self.goals,
            "protocols": self.protocols,
            "characteristics": self.characteristics,
        }


class BaseAgent:
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.inbox = []

    def receive(self, message):
        self.inbox.append(message)

    def handle(self, message):
        raise NotImplementedError


class CustomerAgent(BaseAgent):
    def handle(self, message):
        if message.get("performative") == "inform" and "delivered" in str(message.get("content", "")).lower():
            return {"performative": "accept", "content": "Thank you, order received."}
        return {"performative": "inform", "content": "Order placed."}


class RestaurantAgent(BaseAgent):
    def handle(self, message):
        if message.get("performative") == "request":
            return {"performative": "accept", "content": "Order accepted, preparing."}
        return {"performative": "inform", "content": "Food ready for pickup."}


class RiderAgent(BaseAgent):
    def handle(self, message):
        if message.get("performative") == "request":
            return {"performative": "accept", "content": "Pickup accepted."}
        return {"performative": "inform", "content": "Order delivered."}


class DispatcherAgent(BaseAgent):
    def handle(self, message):
        return {"performative": "request", "content": "Assigning..."}


DESCRIPTORS = [
    AgentDescriptor("CustomerAgent", "BDI",
                    "Place orders, track status, receive delivery",
                    ["order confirmation", "status updates"],
                    ["place_order", "cancel_order", "rate_delivery"],
                    ["get food delivered"], ["order", "status"], "one per customer"),
    AgentDescriptor("RestaurantAgent", "Reactive",
                    "Accept orders, prepare food, notify ready",
                    ["new order", "preparation complete"],
                    ["accept_order", "mark_ready", "reject_order"],
                    ["fulfil orders"], ["order", "ready"], "one per restaurant"),
    AgentDescriptor("RiderAgent", "Reactive",
                    "Accept pickup, deliver, report status",
                    ["pickup assigned", "delivery complete"],
                    ["accept_pickup", "mark_delivered"],
                    ["deliver on time"], ["pickup", "delivery"], "many"),
    AgentDescriptor("Dispatcher", "Orchestrator",
                    "Match orders to restaurants and riders, track progress",
                    ["order placed", "food ready", "rider free"],
                    ["assign_restaurant", "assign_rider", "notify_customer"],
                    ["minimise delivery time"], ["order", "assignment", "status"], "singleton"),
]


def build_agents():
    return {d.name: BaseAgent.__class__ and None for d in DESCRIPTORS}


if __name__ == "__main__":
    import json
    print(json.dumps([d.to_dict() for d in DESCRIPTORS], indent=2))
