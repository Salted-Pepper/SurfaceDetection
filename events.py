

class Event:
    def __init__(self, code):
        self.code = code

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.code == other
        elif isinstance(other, Event):
            return self.code == other.code
        else:
            raise ValueError(f"Unable to compare Event to type {type(other)}.")


ENTERED_BASE = Event("entered_base")
COMPLETED_TURN = Event("completed_turn")
