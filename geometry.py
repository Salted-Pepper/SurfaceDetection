import math


def calculate_polar_angle(a, b) -> float:
    """
    calculate polar angle between two points
    :param a: First Point
    :param b: Point relative to first
    :return:
    """
    return math.degrees(math.atan2(b.y - a.y, b.x - a.x))


def ccw(a, b, c) -> float:
    """
    Computes surface area that can be compared to conclude whether turn is counter-clock-wise
    :param a: Point
    :param b: Point
    :param c: Point
    :return:
    """
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def next_point_ccw(a, b, c) -> bool:
    """
    Checks if going from point b to c is clockwise or counterclockwise in reference to the line a to b
    :param a: Point
    :param b: Point
    :param c: Point
    :return:
    """
    area = ccw(a, b, c)
    if area < 0:
        return False
    elif area > 0:
        return True
    else:  # Including collinear points
        return True


def find_lowest_point_in_polygon(points: list) -> object:
    return min(points, key=lambda p: p.y)


def graham_scan(points: list) -> list:
    """
    Applies Graham Scan algorithm to make a convex hull out of a set of points.
    An exception is when the graham scan receives points with "force_maintain" characteristics
    This will create a non-convex hull that ensures that these points are contained
    :param points: List of Points objects
    :return:
    """
    starting_point = find_lowest_point_in_polygon(points)
    points.remove(starting_point)

    points.sort(key=lambda p: calculate_polar_angle(starting_point, p))
    convex_hull = [starting_point, points.pop(0)]

    for index, point in enumerate(points):
        if index == len(points):
            if next_point_ccw(convex_hull[-2], convex_hull[-1], starting_point):
                pass
            else:
                convex_hull.pop()
            convex_hull.append(point)
        else:
            if len(convex_hull) > 2:
                while not next_point_ccw(convex_hull[-2], convex_hull[-1], point):
                    if len(convex_hull) > 0:
                        convex_hull.pop()
                    else:
                        raise ValueError("Unable to find next CCW point to establish convex hull.")
            convex_hull.append(point)
    return convex_hull
