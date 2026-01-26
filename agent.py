import settings
import routes
from points import Point

import copy

agent_id = 0
base = Point(settings.BASE_X, settings.BASE_Y)


class Agent:
    def __init__(self, model: str, endurance: float, speed: float, maintenance: float):
        global agent_id

        self.agent_id = agent_id
        agent_id += 1
        self.model = model
        self.endurance = endurance
        self.remaining_endurance = endurance
        self.speed = speed
        self.maintenance_time = maintenance
        self.remaining_maintenance = 0

        self.patrol_location = None
        self.base = base
        self.location = copy.deepcopy(base)
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

    def update_maintenance(self):
        self.remaining_maintenance = max(0, self.remaining_maintenance - settings.TIME_DELTA)
        if self.remaining_maintenance == 0:
            self.remaining_endurance = self.endurance

    def update_endurance(self):
        self.remaining_endurance = max(0, self.remaining_endurance - (settings.TIME_DELTA*self.speed))

    def move_through_route(self) -> None:
        turn_travel = self.speed * settings.TIME_DELTA
        print(f"Agent {self.agent_id} at {self.location} - {self.patrol_location.color} - heading to {self.route.get_next_point()}")
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
                if self.returning:
                    self.enter_base()
                    return
                else:
                    self.location = copy.deepcopy(goal)
                    turn_travel -= dist
                    self.route.cycle_next_point()

    def return_to_base(self) -> None:
        self.route = routes.Route([self.base])

    def enter_base(self) -> None:
        print(f"{self} is entering base")
        self.remaining_maintenance = self.maintenance_time
        self.returning = False
        self.called_replacement = False

        if self.plot_object is not None:
            self.plot_object.set_visible(False)

    def activate(self, patrol_location):
        self.patrol_location = patrol_location
        self.route = patrol_location.boustrophedon_path
        self.move_through_route()

        if self.plot_object is not None:
            self.plot_object.set_visible(True)
