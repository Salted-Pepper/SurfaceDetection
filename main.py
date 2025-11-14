# TODO - next steps:
#   - Update Agent Location
#   - Ensure agent types take over assigned zones during changes
from world import World


if __name__ == '__main__':
    world = World()

    world.plot()

    world.search_manager.score_patrol_locations()
