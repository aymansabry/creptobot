from enum import Enum, auto

class UserState(Enum):
    MAIN_MENU = auto()
    WALLET_SELECTION = auto()
    DEPOSIT_AMOUNT = auto()
    TRADE_CONFIRMATION = auto()

class StateManager:
    def __init__(self):
        self.user_states = {}
    
    def set_state(self, user_id: int, state: UserState):
        self.user_states[user_id] = state
    
    def get_state(self, user_id: int) -> UserState:
        return self.user_states.get(user_id, UserState.MAIN_MENU)
