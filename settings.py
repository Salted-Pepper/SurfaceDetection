import json
import random
import matplotlib.colors as mcolors
import math

# World
world = None
world_time = 0

TIME_DELTA = 1
SIMULATION_TIME = 800
BASELINE_HEIGHT = 600
AREA_WIDTH = 4500
AREA_ANGLE = 5
EXTENSION = math.tan(AREA_ANGLE * math.pi / 180) * AREA_WIDTH
TOTAL_HEIGHT = BASELINE_HEIGHT + 2*EXTENSION

BASE_X = -500
BASE_Y = TOTAL_HEIGHT / 2

WORLD_POLYGON = None

AREA_BORDER = 100
GRID_SIZE = 20

PATROL_ZONE_ITERATIONS = 50

SEARCHER = "SEARCHER"
TRAVELLER = "TRAVELLER"

colors = list(mcolors.CSS4_COLORS.keys())
random.shuffle(colors)


def import_agent_data() -> dict:
    with open("agent_data.json", "r") as file:
        data = json.load(file)

        agent_dict = {}

        for agent in data:
            model = agent.pop("model")
            agent_dict[model] = agent

        return agent_dict


AGENT_DATA = import_agent_data()
