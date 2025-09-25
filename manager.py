import settings
from agent import Agent
from points import PatrolLocation

import math
import numpy as np


class AgentType:
    def __init__(self, model: str, values: dict):
        self.model = model
        self.active_agents = []
        self.inactive_agents = []
        self.utilisation = None
        self.last_activation = -np.inf

        self.radius = values["radius"]
        self.quantity = values["quantity"]
        self.speed = values["speed"]
        self.endurance = values["endurance"]
        self.maintenance = values["maintenance"]
        self.color = values["color"]
        self.team = values["team"]

        self.ideal_utilisation = (self.endurance / self.speed) / ((self.endurance / self.speed) + self.maintenance)
        self.trip_time = self.endurance / self.speed
        self.activation_interval = (self.trip_time + self.maintenance) / self.quantity
        self.concurrent_agents = int(np.floor(self.quantity * self.ideal_utilisation))

        self.patrol_locations = []

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

    def create_patrol_location(self) -> PatrolLocation:
        x_coord = np.random.uniform(0, settings.AREA_WIDTH)
        y_coord = np.random.uniform(0, settings.BASELINE_HEIGHT)
        location = PatrolLocation(x_coord, y_coord, strength=self.speed * self.endurance, radius=self.radius)
        self.patrol_locations.append(location)
        return location


class Manager:
    def __init__(self):
        self.agent_types = []

    def create_agents(self) -> None:
        for at in self.agent_types:
            for _ in range(at.quantity):
                agent = Agent(model=at.model, speed=at.speed, endurance=at.endurance,
                              maintenance=at.maintenance, color=at.color)
                at.inactive_agents.append(agent)

    def update_agents(self):
        for at in self.agent_types:
            at.update_agents()

class SearchManager(Manager):
    def __init__(self):
        super().__init__()
        agent_types = settings.AGENT_DATA.keys()

        for at in agent_types:
            if settings.AGENT_DATA[at]["team"] == settings.SEARCHER:
                self.agent_types.append(AgentType(model=at, values=settings.AGENT_DATA[at]))

        self.create_agents()
        self.patrol_locations = []
        self.create_patrol_tessellation()

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

    def create_patrol_tessellation(self):
        for at in self.agent_types:
            for _ in range(at.concurrent_agents):
                self.patrol_locations.append(at.create_patrol_location())
                print(f"Created patrol location at {self.patrol_locations[-1]}")
        self.normalize_strength()
        self.distribute_patrol_locations()

    def normalize_strength(self):
        total_strength = 0
        for pl in self.patrol_locations:
            total_strength += pl.strength
        area_size = settings.AREA_WIDTH * settings.BASELINE_HEIGHT
        for pl in self.patrol_locations:
            pl.strength = (pl.strength/total_strength) * math.sqrt(area_size)

    def distribute_patrol_locations(self):
        for _ in range(settings.PATROL_ZONE_ITERATIONS):
            for pl in self.patrol_locations:
                    pl.observe_pressure(self.patrol_locations)

            for pl in self.patrol_locations:
                pl.update()
        print(f"Created {len(self.patrol_locations)} patrol locations")
        self.assign_receptors_to_patrol_locations()

    def assign_receptors_to_patrol_locations(self):
        print(f"Assigning {len(settings.world.grid.receptors)} Receptors to Patrol Locations")
        for receptor in settings.world.grid.receptors:
            closest_patrol = min(self.patrol_locations, key=lambda p: p.distance_to(receptor.location,
                                                                                    metric="adj manhattan")
                                                                      / math.sqrt(p.strength))
            closest_patrol.receptors.append(receptor)
            receptor.color = closest_patrol.color


class TravelManager(Manager):
    def __init__(self):
        super().__init__()
        agent_types = settings.AGENT_DATA.keys()

        for at in agent_types:
            if settings.AGENT_DATA[at]["team"] == settings.SEARCHER:
                self.agent_types.append(AgentType(model=at, values=settings.AGENT_DATA[at]))

        self.create_agents()
