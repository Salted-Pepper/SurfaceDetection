import settings

from receptors import ReceptorGrid
from manager import SearchManager, TravelManager


class World:
    def __init__(self):
        settings.world = self
        self.grid = ReceptorGrid()
        self.search_manager = SearchManager()
        self.travel_manager = TravelManager()
