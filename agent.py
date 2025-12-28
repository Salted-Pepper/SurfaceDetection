import settings
from points import Point

agent_id = 0
base = Point(settings.BASE_X, settings.BASE_Y)


class Agent:
    def __init__(self, model: str, endurance: float, speed: float, maintenance: float, color: str):
        global agent_id

        self.agent_id = agent_id
        agent_id += 1
        self.model = model
        self.endurance = endurance
        self.remaining_endurance = endurance
        self.speed = speed
        self.maintenance_time = maintenance
        self.remaining_maintenance = 0
        self.color = color

        self.patrol_location = None
        self.base = base
        self.location = base

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
        pass


