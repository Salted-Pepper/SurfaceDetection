import points


class Route:
    def __init__(self, waypoints):
        self.waypoints = waypoints

    def __repr__(self) -> str:
        return str([str(p) for p in self.waypoints])


def create_boustrophedon_path(patrol_location) -> Route:
    interior_points = create_interior_points(patrol_location)
    contained_points = patrol_location.select_contained_points(interior_points)
    return Route(contained_points)


def create_interior_points(patrol_location):
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
