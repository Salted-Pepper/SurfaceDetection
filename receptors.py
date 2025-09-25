import settings
import numpy as np

from points import Point


class Receptor:
    def __init__(self, point):
        self.location = point

        self.pheromones = 0
        self.decay = True

        # Sea State Variables
        self.sea_state = 2
        self.last_uniform_value = 0.5
        self.new_uniform_value = 0.5

    def __repr__(self):
        return f'Receptor at ({self.location}) with pheromones {self.pheromones}'

    def in_range_of_point(self, point: Point, radius: float) -> bool:
        if point.distance_to(self.location) <= radius:
            return True
        else:
            return False

class ReceptorGrid:
    def __init__(self):
        self.receptors = []

        self.max_cols = None
        self.max_rows = None

        self.area_x_start = None
        self.area_x_end = None
        self.area_y_start = None
        self.area_y_end = None

        self.initiate_grid()

    def initiate_grid(self):
        """
        Creates all receptors in the grid given the settings.
        Initiates the pheromone values (0 for empty, inf for outside AoI)
        """
        self.area_x_start =  - settings.AREA_BORDER
        self.area_x_end = settings.AREA_WIDTH + settings.AREA_BORDER

        self.area_y_start = - settings.AREA_BORDER
        self.area_y_end = settings.BASELINE_HEIGHT + settings.AREA_BORDER

        num_cols = (self.area_x_end - self.area_x_start) // settings.GRID_SIZE
        num_rows = (self.area_y_end - self.area_y_start) // settings.GRID_SIZE

        self.max_cols = int(np.ceil(num_cols))
        self.max_rows = int(np.ceil(num_rows))

        for row in range(self.max_rows):
            for col in range(self.max_cols):
                x_location = self.area_x_start + col * settings.GRID_SIZE
                y_location = self.area_y_start + row * settings.GRID_SIZE

                self.receptors.append(Receptor(Point(x_location, y_location)))

    def select_receptors_in_radius(self, point: Point, radius: float) -> list:
        """
        Select all the receptors within a radius of a point.
        Prevents having to cycle through all points by using how the list of receptors was created
        :param point: Point object
        :param radius: Radius around the point
        :return:
        """
        # only check receptors in the rectangle of size radius - select receptors in the list based on
        # how the list is constructed.
        x, y = point.x, point.y
        min_x = x - radius
        max_x = x + radius
        min_y = y - radius
        max_y = y + radius

        # see in which rows and columns this rectangle is:
        min_row = int(max(np.floor((min_x - self.area_x_start)/ settings.GRID_SIZE), 0))
        max_row = int(min(np.ceil((max_x - self.area_x_end)/ settings.GRID_SIZE), self.max_rows))

        min_col = int(max(np.floor((min_y - self.area_y_start) /  settings.GRID_SIZE), 0))
        max_col = int(min(np.ceil((max_y - self.area_y_end) / settings.GRID_SIZE), self.max_cols))

        receptors_in_radius = []
        for row_index in range(min_row, max_row):
            for col_index in range(min_col, max_col):
                index = self.max_cols * row_index + col_index
                r = self.receptors[index]

                if r.in_range_of_point(point, radius):
                    receptors_in_radius.append(r)
        return receptors_in_radius