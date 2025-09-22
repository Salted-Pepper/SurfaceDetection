import json


# World
world_time = 0

TIME_DELTA = 1
BASELINE_HEIGHT = 600
AREA_WIDTH = 4_500
AREA_ANGLE = 15

SEARCHER = "SEARCHER"
TRAVELLER = "TRAVELLER"


def import_agent_data() -> dict:
    with open("agent_data.json", "r") as file:
        data = json.load(file)

        agent_dict = {}

        for agent in data:
            model = agent.pop("model")
            agent_dict[model] = agent

        return agent_dict

AGENT_DATA = import_agent_data()