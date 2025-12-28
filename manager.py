import settings
from agent import Agent
import points

import math
import shapely
import numpy as np


class AgentType:
    def __init__(self, model: str, values: dict):
        self.model = model
        self.active_agents = []
        self.inactive_agents = []
        self.maintenance_agents = []

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

        self.travel_distance = 0
        self.patrol_locations = []
        self.activation_queue = []

    def update_agents(self):
        for agent in self.active_agents:
            agent.move_through_route()

    def create_patrol_location(self) -> points.PatrolLocation:
        x_coord = np.random.uniform(0, settings.AREA_WIDTH)
        y_coord = np.random.uniform(0, settings.TOTAL_HEIGHT)
        while not settings.WORLD_POLYGON.contains(shapely.Point(x_coord, y_coord)):
            x_coord = np.random.uniform(0, settings.AREA_WIDTH)
            y_coord = np.random.uniform(0, settings.TOTAL_HEIGHT)

        location = points.PatrolLocation(x_coord, y_coord, strength=self.speed * self.endurance, radius=self.radius)
        self.patrol_locations.append(location)

        self.travel_distance = max(location.distance_to(points.Point(settings.BASE_X, settings.BASE_Y)),
                                   self.travel_distance)
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

    def update_agents(self) -> None:
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

    def get_statistics(self) -> dict:
        stats = {"time": settings.world_time}
        for at in self.agent_types:
            stats[at.model + "-active"] = len(at.active_agents)
        return stats

    def create_patrol_tessellation(self) -> None:
        for at in self.agent_types:
            for _ in range(at.concurrent_agents):
                self.patrol_locations.append(at.create_patrol_location())
        self.normalize_strength()
        self.distribute_patrol_locations()

    def normalize_strength(self) -> None:
        total_strength = 0
        for pl in self.patrol_locations:
            total_strength += pl.strength
        area_size = settings.AREA_WIDTH * settings.BASELINE_HEIGHT
        for pl in self.patrol_locations:
            pl.strength = (pl.strength / total_strength) * math.sqrt(area_size)

    def distribute_patrol_locations(self) -> None:
        for _ in range(settings.PATROL_ZONE_ITERATIONS):
            for pl in self.patrol_locations:
                pl.update()

            self.update_patrol_assignments()
        self.score_patrol_locations()

        for p in self.patrol_locations:
            p.create_boustrophedon_path()
        print(f"Created {len(self.patrol_locations)} patrol locations")

    def update_patrol_assignments(self) -> None:
        # TODO: Think about whether we should assign points outside the area of interest
        #  (currently off, might affect edge behaviour)
        print(f"Assigning {len(settings.world.grid.receptors)} Receptors to Patrol Locations")
        for pl in self.patrol_locations:
            pl.receptors = []

        for receptor in settings.world.grid.receptors:
            if not receptor.in_zone:
                continue

            closest_patrol = min(self.patrol_locations, key=lambda p: p.distance_to(receptor.location,
                                                                                    metric="adj manhattan")
                                                                      / math.sqrt(p.strength))
            closest_patrol.receptors.append(receptor)
            receptor.color = closest_patrol.color

    def score_patrol_locations(self) -> None:
        performances = []
        total_locations = len(settings.world.grid.receptors)

        for pl in self.patrol_locations:
            assigned_grid_points = len(pl.receptors)
            assigned_share = assigned_grid_points / total_locations
            performances.append({"pl": pl,
                                 "share": assigned_share,
                                 "strength": pl.strength})
        total_strength = sum([p["strength"] for p in performances])
        score = sum([abs(p["share"] - (p["strength"] / total_strength)) for p in performances])
        print(f"Patrol locations score: {score}")


class TravelManager(Manager):
    def __init__(self):
        super().__init__()
        agent_types = settings.AGENT_DATA.keys()

        for at in agent_types:
            if settings.AGENT_DATA[at]["team"] == settings.SEARCHER:
                self.agent_types.append(AgentType(model=at, values=settings.AGENT_DATA[at]))

        self.create_agents()
