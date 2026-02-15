# TODO - next steps:
#   - Update Agent Location
#   - Ensure agent types take over assigned zones during changes
import logging
import datetime

import pandas as pd

from world import World

today = datetime.date.today().strftime("%d_%m_%Y")

logger = logging.getLogger(__name__)
logging.basicConfig(filename=today+".log", encoding='utf-8', level=logging.DEBUG)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

if __name__ == '__main__':
    world = World()
    world.simulate()

    df = world.travel_manager.stats_to_df()
    df[df["detected"]].hist(["time"])
