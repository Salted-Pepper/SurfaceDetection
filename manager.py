import copy
import math
import random

import shapely
import numpy as np
from abc import abstractmethod

import settings
from agent import Agent
import points

import logging
logger = logging.getLogger(__name__)

searcher_base = points.Point(settings.BASE_X, settings.BASE_Y)
exit_point = points.Point(settings.BASE_X, settings.BASE_Y)


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

        self.ingress_distance = settings.AREA_WIDTH + abs(settings.BASE_X)
        self.concurrent_locations = self.calculate_concurrent_locations()

        self.patrol_locations = []
        self.activation_queue = []

    def __str__(self):
        return (f"{self.model} - "
                f"Active: {len(self.active_agents)}, "
                f"Inactive: {len(self.inactive_agents)}, "
                f"Maint: {len(self.maintenance_agents)}")

    def calculate_concurrent_locations(self) -> int:
        ingress_time = self.ingress_distance / self.speed
        downtime = self.maintenance + 2 * ingress_time
        uptime = (self.endurance - 2*self.ingress_distance) / self.speed
        required = np.ceil(downtime / uptime) + 1
        print(f"{self.model} has {int(np.floor(self.quantity / required))} concurrent locations")
        return int(np.floor(self.quantity / required))

    def create_patrol_location(self) -> points.PatrolLocation:
        x_coord = np.random.uniform(0, settings.AREA_WIDTH)
        y_coord = np.random.uniform(0, settings.TOTAL_HEIGHT)
        while not settings.WORLD_POLYGON.contains(shapely.Point(x_coord, y_coord)):
            x_coord = np.random.uniform(0, settings.AREA_WIDTH)
            y_coord = np.random.uniform(0, settings.TOTAL_HEIGHT)

        location = points.PatrolLocation(x_coord, y_coord, strength=self.speed * self.endurance, radius=self.radius)
        self.patrol_locations.append(location)

        self.ingress_distance = max(location.distance_to(points.Point(settings.BASE_X, settings.BASE_Y)),
                                    self.ingress_distance)
        print(f"Model {self.model} has {len(self.patrol_locations)} patrol locations "
              f"for {self.concurrent_locations} agents.")
        return location

    def update_agents(self) -> None:

        for agent in copy.copy(self.maintenance_agents):
            completed = agent.update_maintenance()
            if completed:
                self.maintenance_agents.remove(agent)
                self.inactive_agents.append(agent)

        active_agents = copy.copy(self.active_agents)
        for agent in active_agents:
            current_ingress_distance = agent.location.distance_to(agent.base)

            if not agent.called_replacement:
                if agent.remaining_endurance < 2 * current_ingress_distance:
                    self.call_next_agent(patrol_location=agent.patrol_location)
                    agent.called_replacement = True

            if not agent.returning:
                if agent.remaining_endurance < current_ingress_distance * 1.1:
                    agent.return_to_base()

            agent.move_through_route()

            if agent.remaining_maintenance > 0:
                if agent.location != agent.base:
                    raise ValueError("Agent out of base with remaining maintenance")
                self.active_agents.remove(agent)
                self.maintenance_agents.append(agent)

    def plot_agents(self, ax):
        for agent in self.active_agents:
            if agent.plot_object is None:
                agent.plot_object = ax.scatter(agent.location.x, agent.location.y,
                                               color=agent.patrol_location.color, marker="X", zorder=2,
                                               edgecolor="black")
            else:
                agent.plot_object.set_offsets([[agent.location.x, agent.location.y]])

    def call_next_agent(self, patrol_location: points.PatrolLocation) -> None:
        if len(self.inactive_agents) == 0:
            raise ValueError(f"No inactive agents available for {self.model} "
                             f"- agents in maint: {self.maintenance_agents}")
        next_agent = self.inactive_agents.pop()
        self.active_agents.append(next_agent)
        next_agent.activate(patrol_location)


class Manager:
    def __init__(self):
        self.agent_types = []

    @abstractmethod
    def create_agents(self) -> None:
        pass

    @abstractmethod
    def manage_agents(self) -> None:
        pass

    @abstractmethod
    def plot_agents(self, ax) -> None:
        pass


class SearchManager(Manager):
    """
    Oversees several Agent Types that each are responsible for assigned patrol locations.
    """
    def __init__(self):
        super().__init__()
        agent_types = settings.AGENT_DATA.keys()

        for at in agent_types:
            if settings.AGENT_DATA[at]["team"] == settings.SEARCHER:
                self.agent_types.append(AgentType(model=at, values=settings.AGENT_DATA[at]))

        self.create_agents()
        self.patrol_locations = []
        self.create_patrol_tessellation()

    def create_agents(self) -> None:
        for at in self.agent_types:
            for _ in range(at.quantity):
                agent = Agent(model=at.model, speed=at.speed, endurance=at.endurance,
                              maintenance=at.maintenance, base=searcher_base)
                at.inactive_agents.append(agent)

    def manage_agents(self) -> None:
        for agent_type in self.agent_types:
            agent_type.update_agents()

    def get_statistics(self) -> dict:
        stats = {"time": settings.world_time}
        for at in self.agent_types:
            stats[at.model + "-active"] = len(at.active_agents)
        return stats

    def create_patrol_tessellation(self) -> None:
        for at in self.agent_types:
            for _ in range(at.concurrent_locations):
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

        for at in self.agent_types:
            for pl in at.patrol_locations:
                at.call_next_agent(pl)
        logger.info(f"Created {len(self.patrol_locations)} patrol locations")

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

    def plot_agent_types(self, ax) -> None:
        for at in self.agent_types:
            at.plot_agents(ax)


class TravelManager(Manager):
    """
    Oversees agents passing through the zone directly
    """
    def __init__(self):
        super().__init__()
        self.active_agents = []
        self.stats = []

        self.create_agents()

    def create_agents(self) -> None:
        self.generate_entries()

    def generate_entries(self):
        # TODO: change random entry process
        if random.uniform(0, 1) > 0.8:
            self.new_entry()

    def new_entry(self):
        # TODO: Replace characteristics with actual values
        entry_y = random.uniform(settings.ENTRY_Y_MIN, settings.ENTRY_Y_MAX)
        entry_point = points.Point(settings.ENTRY_X, entry_y)
        model = "tbd"
        speed = 25
        new_agent = Agent(model, endurance=math.inf, speed=speed, maintenance=0, base=exit_point)
        self.active_agents.append(new_agent)
        new_agent.location = entry_point
        new_agent.return_to_base()

    def manage_agents(self) -> None:
        self.generate_entries()

        for agent in copy.copy(self.active_agents):
            agent.move_through_route()
            print(f"traveller is at {agent.location}")
            if not agent.returning:
                self.active_agents.remove(agent)

    def plot_agents(self, ax) -> None:
        for agent in self.active_agents:
            if agent.plot_object is None:
                agent.plot_object = ax.scatter(agent.location.x, agent.location.y,
                                               color="forestgreen", marker="<", zorder=2,
                                               edgecolor="black")
            else:
                agent.plot_object.set_offsets([[agent.location.x, agent.location.y]])

