import settings
from receptors import ReceptorGrid
from manager import SearchManager, TravelManager

import shapely
import matplotlib
from matplotlib import pyplot as plt
matplotlib.use("TkAgg")


class World:
    def __init__(self):
        settings.world = self
        initiate_world_polygon()

        self.grid = ReceptorGrid()
        self.search_manager = SearchManager()
        self.travel_manager = TravelManager()

    def plot(self):
        fig, ax = plt.subplots()

        print("Plotting Receptors")
        df = self.grid.receptors_as_dataframe()
        ax.scatter(df["x"], df["y"], c=df["color"])

        print("Plotting Patrol Locations")
        for pl in self.search_manager.patrol_locations:
            ax.scatter(pl.x, pl.y, color=pl.color, edgecolors="black", alpha=0.4)
            ax.text(pl.x, pl.y - 2, s=str(round(pl.strength, 1)), color="black")
        ax.set_xlim(0, settings.AREA_WIDTH)
        ax.set_ylim(0, settings.TOTAL_HEIGHT)


def initiate_world_polygon():
    """
    We create a polygon of the Trapeze, we lift each point by the value of extension, as otherwise the bottom right
    corner falls out of the positive numbers field. This is just done for convenience, so we only consider positive
    spaces.
    """
    top_left_corner = shapely.Point(0, settings.EXTENSION + settings.BASELINE_HEIGHT)
    top_right_corner = shapely.Point(settings.AREA_WIDTH, settings.TOTAL_HEIGHT)
    bottom_right_corner = shapely.Point(settings.AREA_WIDTH, 0)
    bottom_left_corner = shapely.Point(0, settings.EXTENSION)

    settings.WORLD_POLYGON = shapely.Polygon([top_left_corner, top_right_corner,
                                              bottom_right_corner, bottom_left_corner])
