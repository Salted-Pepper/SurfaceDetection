import settings

from receptors import ReceptorGrid
from manager import SearchManager, TravelManager

import matplotlib
from matplotlib import pyplot as plt
matplotlib.use("TkAgg")


class World:
    def __init__(self):
        settings.world = self
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
        ax.set_ylim(0, settings.BASELINE_HEIGHT)
