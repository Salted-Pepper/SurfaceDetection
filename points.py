import math
import random
import settings

point_id = 0

class Point:
    def __init__(self, x, y):
        global point_id
        self.point_id = point_id
        point_id += 1
        self.x = x
        self.y = y

    def get_tuple(self) -> tuple:
        return self.x, self.y

    def __str__(self):
        return f"({self.x:0.2f}, {self.y:0.2f})"

    def __repr__(self):
        return f"Point at ({self.x}, {self.y})"

    def __eq__(self, other) -> bool:
        if self.x == other.x and self.y == other.y:
            return True
        else:
            return False

    def __hash__(self) -> int:
        return self.point_id

    def distance_to(self, other, metric="euclidean") -> float:
        if metric == "euclidean":
            return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        elif metric == "manhattan":
            return abs(self.x - other.x) + abs(self.y - other.y)
        elif metric == "adj manhattan":
            return 0.5 * abs(self.x - other.x) + abs(self.y - other.y)
        raise ValueError(f"Invalid distance metric {metric}")

class PatrolLocation(Point):
    def __init__(self, x, y, strength: float, radius: float):
        super().__init__(x, y)
        self.strength = strength
        self.radius = radius

        self.receptors = []
        self.color = settings.colors.pop()
        self.next_x = None
        self.next_y = None

        self.current_agent = None

    def observe_pressure(self, all_points: list):
        n = len(all_points)
        new_x = 0
        new_y = 0

        for point in all_points:
            x_n, y_n = self.pressure(point)
            new_x += x_n / n
            new_y += y_n / n

        self.next_x = new_x
        self.next_y = new_y
        print(f"Moving point from {self.x}, {self.y} to {self.next_x}, {self.next_y}")


    def pressure(self, other) -> tuple[float, float]:
        distance = self.distance_to(other, metric="adj manhattan")
        strength = self.strength + other.strength

        if distance < 0.001:
            distance = 0.001

        if strength > distance:
            new_x = self.x - (other.x - self.x) * ((strength - distance) / distance) + random.uniform(-1, 1)
            new_y = self.y - (other.y - self.y) * ((strength - distance) / distance) + random.uniform(-1, 1)
        else:
            new_x = self.x
            new_y = self.y
        return new_x, new_y

    def update(self):
        self.x = max(0, min(self.next_x, settings.AREA_WIDTH))
        self.y = max(0, min(self.next_y, settings.BASELINE_HEIGHT))