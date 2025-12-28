import math
import shapely

import matplotlib.pyplot as plt

import geometry
import settings

point_id = 0


class Point:
    def __init__(self, x, y):
        global point_id
        self.point_id = point_id
        point_id += 1
        self.x = x
        self.y = y

        self.convex_hull = None

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

        self.current_agent = None
        self.boustrophedon_path = None

    def __str__(self):
        return "Patrol Location"

    def centralize(self) -> None:
        receptors_inside_zone = [r for r in self.receptors if r.in_zone]

        if len(receptors_inside_zone) == 0:
            self.move_to_closest_receptor()
            return

        avg_x = sum(r.location.x for r in receptors_inside_zone) / len(receptors_inside_zone)
        avg_y = sum(r.location.y for r in receptors_inside_zone) / len(receptors_inside_zone)

        self.x = avg_x
        self.y = avg_y

    def update(self):
        self.centralize()

    def move_to_closest_receptor(self):
        closest_receptor = min(settings.world.grid.receptors, key=lambda r: self.distance_to(r.location))
        self.x = closest_receptor.location.x
        self.y = closest_receptor.location.y

    def calculate_convex_hull(self):
        self.convex_hull = geometry.graham_scan([r.location for r in self.receptors])

    def create_boustrophedon_path(self):
        import routes
        self.calculate_convex_hull()
        self.boustrophedon_path = routes.create_boustrophedon_path(self)

    def show_boustrophedon_path(self):
        fig = plt.figure()
        ax = fig.add_subplot()

        for p_1, p_2 in zip(self.convex_hull[:-1], self.convex_hull[1:]):
            ax.plot([p_1.x, p_2.x], [p_1.y, p_2.y], color="black")
        ax.plot([self.convex_hull[0].x, self.convex_hull[-1].x],
                [self.convex_hull[0].y, self.convex_hull[-1].y], color="black")

        for p_1, p_2 in zip(self.boustrophedon_path.waypoints[:-1], self.boustrophedon_path.waypoints[1:]):
            ax.arrow(x=p_1.x, y=p_1.y, dx=p_2.x - p_1.x, dy=p_2.y - p_1.y, width=1,
                     facecolor="orange", edgecolor="none")
        plt.show()

    def reached_path_point(self) -> None:
        self.boustrophedon_path.cycle_next_point()

    def select_contained_points(self, points) -> list[Point]:
        polygon = shapely.Polygon([p.get_tuple() for p in self.convex_hull])
        contained_points = []
        for p in points:
            if polygon.contains(shapely.Point(p.x, p.y)):
                contained_points.append(p)
        return contained_points
