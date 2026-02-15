import json
import random
import matplotlib.colors as mcolors
import math

####################################################
# WORLD SETTINGS
####################################################
world = None
world_time = 0
TIME_DELTA = 1
SIMULATION_TIME = 1000

BASELINE_HEIGHT = 600
AREA_WIDTH = 4500
AREA_ANGLE = 5
EXTENSION = math.tan(AREA_ANGLE * math.pi / 180) * AREA_WIDTH
TOTAL_HEIGHT = BASELINE_HEIGHT + 2 * EXTENSION

BASE_X = -500
BASE_Y = TOTAL_HEIGHT / 2

ENTRY_X = AREA_WIDTH + 500
ENTRY_Y_MIN = 0
ENTRY_Y_MAX = TOTAL_HEIGHT

WORLD_POLYGON = None

AREA_BORDER = 100
GRID_SIZE = 20

####################################################
# VISUAL/ZONE SETTINGS
####################################################
SEARCH_VERTICAL_ALIGNMENT = 0.6  # Val between 0-1, the higher the more vertical the zones

colors = list(mcolors.CSS4_COLORS.keys())
random.shuffle(colors)

####################################################
# CALCULATION SETTINGS
####################################################
PATROL_ZONE_ITERATIONS = 50
DISTANCE_SAFETY_MARGIN = 0.01
MAX_DISCOVER_DISTANCE = 100

"""
This weather dict is a Markov Chain estimate from sea state transitions as estimated in a 
separate project using historical sea state data on swell.
"""
weather_markov_dict = {0: {0: 0.86797, 1: 0.13202, 2: 1e-05, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       1: {0: 0.01759, 1: 0.91031, 2: 0.072, 3: 0.0001, 4: 0.0, 5: 0, 6: 0, 7: 0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       2: {0: 0.00028, 1: 0.07991, 2: 0.84874, 3: 0.07046, 4: 0.0006, 5: 1e-05, 6: 0.0, 7: 0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       3: {0: 0.00012, 1: 0.00891, 2: 0.20346, 3: 0.67584, 4: 0.10752, 5: 0.00405, 6: 9e-05, 7: 0.0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       4: {0: 6e-05, 1: 0.00465, 2: 0.0558, 3: 0.27422, 4: 0.49631, 5: 0.1529, 6: 0.01496, 7: 0.00106,
                           8: 4e-05, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       5: {0: 1e-05, 1: 0.00211, 2: 0.02767, 3: 0.12292, 4: 0.30308, 5: 0.37542, 6: 0.13974, 7: 0.02456,
                           8: 0.00385, 9: 0.00054, 10: 9e-05, 11: 0, 12: 0, 13: 0, 14: 0},
                       6: {0: 0, 1: 0.00064, 2: 0.018, 3: 0.07771, 4: 0.15775, 5: 0.28886, 6: 0.28494, 7: 0.13138,
                           8: 0.03085, 9: 0.00733, 10: 0.00195, 11: 0.00061, 12: 0, 13: 0, 14: 0},
                       7: {0: 0, 1: 0.00027, 2: 0.01244, 3: 0.05629, 4: 0.10846, 5: 0.18872, 6: 0.25432, 7: 0.20376,
                           8: 0.11955, 9: 0.04385, 10: 0.00886, 11: 0.00304, 12: 0.00045, 13: 0, 14: 0},
                       8: {0: 0, 1: 0, 2: 0.00566, 3: 0.05019, 4: 0.08571, 5: 0.11737, 6: 0.19562, 7: 0.19614,
                           8: 0.14466, 9: 0.1323, 10: 0.06178, 11: 0.00927, 12: 0.00103, 13: 0.00026, 14: 0},
                       9: {0: 0, 1: 0, 2: 0.00112, 3: 0.03652, 4: 0.05506, 5: 0.08708, 6: 0.14944, 7: 0.19663,
                           8: 0.1309, 9: 0.12978, 10: 0.14888, 11: 0.0573, 12: 0.00618, 13: 0.00056, 14: 0.00056},
                       10: {0: 0, 1: 0, 2: 0, 3: 0.01331, 4: 0.04197, 5: 0.04606, 6: 0.07062, 7: 0.14944,
                            8: 0.19345, 9: 0.13204, 10: 0.14637, 11: 0.15967, 12: 0.03992, 13: 0.00716, 14: 0},
                       11: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0.01843, 5: 0.03456, 6: 0.06452, 7: 0.07834,
                            8: 0.12903, 9: 0.19124, 10: 0.27419, 11: 0.15207, 12: 0.0553, 13: 0, 14: 0.0023},
                       12: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0.01111, 6: 0.04444, 7: 0.05556,
                            8: 0.08889, 9: 0.21111, 10: 0.34444, 11: 0.17778, 12: 0.06667, 13: 0, 14: 0},
                       13: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0.1,
                            8: 0.1, 9: 0.2, 10: 0.3, 11: 0.2, 12: 0, 13: 0.1, 14: 0},
                       14: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0,
                            8: 0, 9: 0, 10: 0, 11: 0.5, 12: 0.5, 13: 0, 14: 0}}

# Maps sea state level to corresponding detection adjustment factor
sea_state_values = {0: 1,
                    1: 0.89,
                    2: 0.77,
                    3: 0.68,
                    4: 0.62,
                    5: 0.53,
                    6: 0.47}

####################################################
# AGENT CHARACTERISTICS
####################################################
SEARCHER = "SEARCHER"
TRAVELLER = "TRAVELLER"

SURFACE_SEARCHER = "surface"
AIR_SEARCHER = "air"

BASIC_SKILL = "basic"
ADVANCED_SKILL = "advanced"

STEALTHY = "stealthy"
VSMALL = "vsmall"
SMALL = "small"
MEDIUM = "medium"
LARGE = "large"

spawn_prob_dict = {STEALTHY: 0.25,
                   VSMALL: 0.5,
                   SMALL: 1,
                   MEDIUM: 1.25,
                   LARGE: 1.5}

rcs_dict = {STEALTHY: 0.25,
            VSMALL: 0.5,
            SMALL: 1,
            MEDIUM: 1.25,
            LARGE: 1.5}

SURFACE_DETECTING_SURFACE = {BASIC_SKILL: {LARGE: 56,
                                           MEDIUM: 56,
                                           SMALL: 37,
                                           VSMALL: 20,
                                           STEALTHY: 11},
                             ADVANCED_SKILL: {LARGE: 37,
                                              MEDIUM: 37,
                                              SMALL: 28,
                                              VSMALL: 17,
                                              STEALTHY: 9}}


####################################################
# DATA IMPORT
####################################################

def import_agent_data() -> dict:
    with open("agent_data.json", "r") as file:
        data = json.load(file)

        agent_dict = {}

        for agent in data:
            model = agent.pop("model")
            agent_dict[model] = agent

        return agent_dict


AGENT_DATA = import_agent_data()
