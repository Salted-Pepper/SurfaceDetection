import settings

from agent import Agent

import numpy as np


class AgentType:
    def __init__(self, model: str, values: dict):
        self.model = model
        self.active_agents = []
        self.inactive_agents = []
        self.utilisation = None
        self.last_activation = -np.inf

        self.quantity = values["quantity"]
        self.speed = values["speed"]
        self.endurance = values["endurance"]
        self.maintenance = values["maintenance"]
        self.color = values["color"]
        self.team = values["team"]

        self.ideal_utilisation = (self.endurance / self.speed) / ((self.endurance / self.speed) + self.maintenance)
        self.trip_time = self.endurance / self.speed
        self.activation_interval = (self.trip_time + self.maintenance) / self.quantity

    def calculate_utilisation(self) -> float:
        return len(self.active_agents) / (len(self.inactive_agents) + len(self.active_agents))

    def time_since_last_activation(self) -> float:
        return settings.world_time - self.last_activation

    def allowed_activation(self) -> bool:
        if self.activation_interval <= self.time_since_last_activation():
            return True
        else:
            return False

    def update_agents(self):
        exhausted_agents = []
        for agent in self.active_agents:
            agent.update_endurance()

            if agent.remaining_endurance == 0:
                exhausted_agents.append(agent)

        for agent in self.inactive_agents:
            agent.update_maintenance()

        for agent in exhausted_agents:
            self.active_agents.remove(agent)
            agent.start_maintenance()
            self.inactive_agents.append(agent)


class Manager:
    def __init__(self):
        self.agent_types = []

    def create_agents(self) -> None:
        for at in self.agent_types:
            for _ in range(at.quantity):
                agent = Agent(model=at.model, speed=at.speed, endurance=at.endurance,
                              maintenance=at.maintenance, colour=at.colour)
                at.inactive_agents.append(agent)

    def update_agents(self):
        for at in self.agent_types:
            at.update_agents()


class SearchManager(Manager):
    def __init__(self):
        super().__init__()
        agent_types = settings.AGENT_DATA.keys()

        for at in agent_types:
            if at.team == settings.SEARCHER:
                self.agent_types.append(AgentType(model=at, values=settings.AGENT_DATA[at]))

        self.create_agents()

    def check_activation(self):
        for at in self.agent_types:
            if at.calculate_utilisation() < at.ideal_utilisation and at.allowed_activation():
                available_agents = [a for a in at.inactive_agents if a.remaining_maintenance == 0]
                if len(available_agents) > 0:
                    at.last_activation = settings.world_time
                    agent = available_agents.pop()
                    at.inactive_agents.remove(agent)
                    at.active_agents.append(agent)
                else:
                    print(f"{settings.world_time} - No available agents to reach utilisation for {at.model}")

    def get_statistics(self) -> dict:
        stats = {"time": settings.world_time}
        for at in self.agent_types:
            stats[at.model + "-active"] = len(at.active_agents)
        return stats



class TravelManager(Manager):
    def __init__(self):
        super().__init__()
        agent_types = settings.AGENT_DATA.keys()

        for at in agent_types:
            if at.team == settings.SEARCHER:
                self.agent_types.append(AgentType(model=at, values=settings.AGENT_DATA[at]))

        self.create_agents()
