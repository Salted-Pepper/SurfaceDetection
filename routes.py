import points


class Route:
    def __init__(self, waypoints: list[points.Point]):
        self.waypoints = waypoints

    def __repr__(self) -> str:
        return str([str(p) for p in self.waypoints])

    def cycle_next_point(self) -> None:
        """
        Moves the next point in line to the back of the route
        :return:
        """
        waypoint = self.waypoints.pop(0)
        self.waypoints.append(waypoint)

    def get_next_point(self) -> points.Point:
        return self.waypoints[0]


def create_boustrophedon_path(patrol_location: points.PatrolLocation) -> Route:
    interior_points = create_sorted_interior_points(patrol_location)
    contained_points = patrol_location.select_contained_points(interior_points)
    return Route(contained_points)


def create_sorted_interior_points(patrol_location: points.PatrolLocation) -> list[points.Point]:
    """
    Creates interior points for the boundaries of the convex hull.
    Points are listed in a boustrophedon path order for later use
    :param patrol_location:
    :return: List of points sorted from left to right,
        varying top to bottem and bottem to top for boustrophedon pathing.
    """
    r = patrol_location.radius

    min_x = min([p.x for p in patrol_location.convex_hull]) + r
    max_x = max([p.x for p in patrol_location.convex_hull]) - r
    min_y = min([p.y for p in patrol_location.convex_hull]) + r
    max_y = max([p.y for p in patrol_location.convex_hull]) - r

    horizontal_dots = (max_x - min_x) // r
    vertical_dots = (max_y - min_y) // r

    dots = []

    current_y = min_y
    y_prime = r

    for x_count in range(horizontal_dots):
        current_x = min_x + x_count * r
        for y_count in range(vertical_dots):
            dots.append(points.Point(current_x, current_y))
            current_y += y_prime

        # shift to next line and reverse order
        y_prime = -y_prime
        current_x += r

    return dots
