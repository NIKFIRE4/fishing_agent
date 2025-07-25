from aiogram.fsm.state import State, StatesGroup

class SearchStates(StatesGroup):
    waiting_for_search_request = State()
    browsing_spots = State()
    selecting_date = State()