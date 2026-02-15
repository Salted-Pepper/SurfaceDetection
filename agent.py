from __future__ import annotations

import settings
import routes
from points import Point
import math
import random
import events
import logging

import copy

logger = logging.getLogger(__name__)
agent_id = 0


class Agent:
    def __init__(self,
                 model: str,
                 endurance: float,
                 speed: float,
                 maintenance: float,
                 base: Point):
        global agent_id

        self.spawn_time = settings.world_time
        self.agent_id = agent_id
        agent_id += 1
        self.model = model
        self.endurance = endurance
        self.remaining_endurance = endurance
        self.speed = speed
        self.maintenance_time = maintenance
        self.remaining_maintenance = 0

        self.current_return_distance = 0
        self.patrol_location = None
        self.base = base
        self.location = copy.deepcopy(self.base)
        self.route = None
        self.returning = False
        self.called_replacement = False

        self.plot_object = None

    def __str__(self):
        return (f"Agent {self.agent_id} - "
                f"Endurance: {self.remaining_endurance} - "
                f"Rem Maint: {self.remaining_maintenance}")

    def __repr__(self):
        return (f"Agent {self.agent_id} - "
                f"Endurance: {self.remaining_endurance} - "
                f"Rem Maint: {self.remaining_maintenance}")

    def start_maintenance(self):
        self.remaining_maintenance = self.maintenance_time

    def update_maintenance(self) -> bool:
        finished = False
        self.remaining_maintenance = max(0, self.remaining_maintenance - settings.TIME_DELTA)
        if self.remaining_maintenance == 0:
            self.remaining_endurance = self.endurance
            finished = True
        return finished

    def update_endurance(self):
        self.remaining_endurance = max(0, self.remaining_endurance - (settings.TIME_DELTA*self.speed))

    def move_through_route(self) -> None:
        turn_travel = self.speed * settings.TIME_DELTA

        i = 0
        while turn_travel > 0:
            goal = self.route.get_next_point()
            dist = self.location.distance_to(goal)

            if dist > turn_travel:
                share_traveled = turn_travel / dist
                self.location.x = self.location.x * (1-share_traveled) + goal.x * share_traveled
                self.location.y = self.location.y * (1-share_traveled) + goal.y * share_traveled
                turn_travel = 0
                self.remaining_endurance -= turn_travel
            else:
                self.remaining_endurance -= dist
                self.location.x,  self.location.y = self.base.x, self.base.y
                if self.returning:
                    self.enter_base()
                    self.current_return_distance = 0
                    return events.ENTERED_BASE
                else:
                    self.location = copy.deepcopy(goal)
                    turn_travel -= dist
                    self.route.cycle_next_point()
            i += 1
            if i > 100:
                raise ValueError(f"Unit {self} movement not converging.")

        self.update_current_return_distance()
        return events.COMPLETED_TURN

    def update_current_return_distance(self) -> None:
        self.current_return_distance = self.location.distance_to(self.base)

    def return_to_base(self) -> None:
        self.returning = True
        self.route = routes.Route([self.base])

    def enter_base(self) -> None:
        logger.debug(f"{self} is entering base")
        self.remaining_maintenance = self.maintenance_time
        self.returning = False
        self.called_replacement = False
        self.start_maintenance()

        if self.plot_object is not None:
            self.plot_object.set_visible(False)

    def activate(self, patrol_location) -> None:
        self.patrol_location = patrol_location
        self.route = patrol_location.boustrophedon_path
        self.move_through_route()

        if self.plot_object is not None:
            self.plot_object.set_visible(True)

    def deactivate(self) -> None:
        self.plot_object.set_visible(False)


class Traveller(Agent):
    def __init__(self, model: str,
                 endurance: float,
                 speed: float,
                 maintenance: float,
                 base: Point,
                 air_visibility: str,
                 surface_visibility: str,
                 ):
        super().__init__(model, endurance, speed, maintenance, base)
        self.air_visibility = air_visibility
        self.surface_visibility = surface_visibility


class Searcher(Agent):
    def __init__(self, model: str, endurance: float,
                 speed: float,
                 maintenance: float,
                 base: Point,
                 skill_level: str,
                 operating_domain: str,
                 ):
        super().__init__(model, endurance, speed, maintenance, base)
        self.operating_domain = operating_domain
        self.skill_level = skill_level

    def check_if_need_to_return(self) -> None:
        if not self.returning:
            if self.remaining_endurance < (1+settings.DISTANCE_SAFETY_MARGIN) * self.current_return_distance:
                self.return_to_base()

    def check_if_need_replacement(self) -> bool:
        if not self.called_replacement:
            if self.remaining_endurance < (2+settings.DISTANCE_SAFETY_MARGIN) * self.current_return_distance:
                self.called_replacement = True
                return True
        return False

    def check_detection(self, agent) -> bool:
        if self.operating_domain == settings.SURFACE_SEARCHER:
            success = self.surface_to_surface_detection(agent)
        elif self.operating_domain == settings.AIR_SEARCHER:
            success = self.air_to_surface_detection(agent)
        else:
            raise ValueError(f"Unknown operating domain {self.operating_domain}.")
        return success

    def surface_to_surface_detection(self, agent: Traveller) -> bool:
        target_size = agent.surface_visibility
        detection_range = settings.SURFACE_DETECTING_SURFACE[self.skill_level][target_size]
        distance = self.location.distance_to(agent.location)

        if detection_range < distance:
            return False
        else:
            return True

    def air_to_surface_detection(self, agent: Traveller) -> bool:
        if self.skill_level == settings.BASIC_SKILL:
            k = 2747
        elif self.skill_level == settings.ADVANCED_SKILL:
            k = 39633
        else:
            raise ValueError(f"Unknown Skill Level {self.skill_level}")

        distance = self.location.distance_to(agent.location)
        if distance > 300:
            return False

        sea_state = settings.world.receptor_grid.get_receptor_at_location(self.location).sea_state
        h = 10
        s = settings.sea_state_values.get(sea_state, 0.4)
        r = settings.rcs_dict[agent.air_visibility]
        if distance < 1:
            distance = 1

        detection_probability = (1 - math.exp(-(k * h * r * s) / distance ** 3))
        logger.debug(f"Detection prob {self} - {agent} is {detection_probability}")
        if random.uniform(0, 1) < detection_probability:
            return True
        else:
            return False
        pass
