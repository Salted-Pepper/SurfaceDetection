from __future__ import annotations

import settings
import numpy as np
import pandas as pd
import shapely

from perlin_noise import PerlinNoise

from points import Point


class Receptor:
    def __init__(self, point):
        self.location = point
        self.color = None

        self.in_zone = self.check_if_in_zone()

        self.pheromones = 0
        self.decay = True

        # Sea State Variables
        self.sea_state = 2
        self.last_uniform_value = 0.5
        self.new_uniform_value = 0.5

    def __repr__(self):
        return f'Receptor at ({self.location}) with pheromones {self.pheromones}'

    def __str__(self):
        return f"r({self.location.x}, {self.location.y})"

    def in_range_of_point(self, point: Point, radius: float) -> bool:
        if point.distance_to(self.location) <= radius:
            return True
        else:
            return False

    def check_if_in_zone(self) -> bool:
        if settings.WORLD_POLYGON.contains(shapely.Point(self.location.x, self.location.y)):
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
        """
        self.area_x_start = -settings.AREA_BORDER
        self.area_x_end = settings.AREA_WIDTH + settings.AREA_BORDER

        self.area_y_start = -settings.AREA_BORDER
        self.area_y_end = settings.TOTAL_HEIGHT + settings.AREA_BORDER

        num_cols = (self.area_x_end - self.area_x_start) // settings.GRID_SIZE
        num_rows = (self.area_y_end - self.area_y_start) // settings.GRID_SIZE

        self.max_cols = int(np.ceil(num_cols))
        self.max_rows = int(np.ceil(num_rows))

        for row in range(self.max_rows):
            for col in range(self.max_cols):
                x_location = self.area_x_start + col * settings.GRID_SIZE
                y_location = self.area_y_start + row * settings.GRID_SIZE

                self.receptors.append(Receptor(Point(x_location, y_location)))

    def get_receptor_at_location(self, point: Point) -> Receptor | None:

        if (point.x < self.area_y_start
                or self.area_x_end < point.x
                or point.y < self.area_y_start
                or self.area_y_end < point.y):
            raise ValueError(f"Illegal location - {point}")

        row = int((point.y - self.area_y_start) / settings.GRID_SIZE)
        col = int((point.x - self.area_x_start) / settings.GRID_SIZE)
        index = row * self.max_cols + col

        return self.receptors[index]

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
        min_row = int(max(np.floor((min_x - self.area_x_start) / settings.GRID_SIZE), 0))
        max_row = int(min(np.ceil((max_x - self.area_x_end) / settings.GRID_SIZE), self.max_rows))

        min_col = int(max(np.floor((min_y - self.area_y_start) / settings.GRID_SIZE), 0))
        max_col = int(min(np.ceil((max_y - self.area_y_end) / settings.GRID_SIZE), self.max_cols))

        receptors_in_radius = []
        for row_index in range(min_row, max_row):
            for col_index in range(min_col, max_col):
                index = self.max_cols * row_index + col_index
                r = self.receptors[index]

                if r.in_range_of_point(point, radius):
                    receptors_in_radius.append(r)
        return receptors_in_radius

    def update_sea_states(self) -> None:
        """
        Creates sampled probabilities based on Perlin Noise.
        Once the cumulative transition probability exceeds this random value, sets it to the corresponding state.
        :return:
        """
        self.update_u_values()

        for receptor in self.receptors:
            transition_probabilities = settings.weather_markov_dict[receptor.sea_state]
            prob = 0
            for key in transition_probabilities.keys():
                prob += transition_probabilities[key]
                if prob > receptor.new_uniform_value:
                    receptor.sea_state = key
                    break

    def update_u_values(self) -> None:
        """
        Updates the uniform probabilities for each receptor, which serves as input to sample the next transition
        in the Markov Chain.
        :return:
        """
        cols = self.max_cols
        rows = self.max_rows

        noise = PerlinNoise(octaves=8)
        noise_data = [[noise([j / rows, i / cols]) for i in range(cols)] for j in range(rows)]
        # normalize noise
        min_value = min(x if isinstance(x, int) else min(x) for x in noise_data)
        noise_data = [[n + abs(min_value) for n in rows] for rows in noise_data]
        max_value = max(x if isinstance(x, int) else max(x) for x in noise_data)
        noise_data = [[n / max_value for n in rows] for rows in noise_data]
        min(x if isinstance(x, int) else min(x) for x in noise_data)
        max(x if isinstance(x, int) else max(x) for x in noise_data)
        new_u_matrix = noise_data

        for index, receptor in enumerate(self.receptors):
            receptor.last_uniform_value = receptor.new_uniform_value
            receptor.new_uniform_value = new_u_matrix[index // cols][index % cols]

    def receptors_as_dataframe(self) -> pd.DataFrame:
        records = []
        for receptor in self.receptors:
            if receptor.color is None:
                receptor.color = "black"

            records.append({"x": receptor.location.x, "y": receptor.location.y, "color": receptor.color})

        return pd.DataFrame.from_records(records)
