from enum import Enum

from app.entities import GameModeType
from app.services.modes.campaign_mode import CampaignMode
from app.services.modes.capture_flag_mode import CaptureFlagMode
from app.services.modes.free_for_all_mode import FreeForAllMode


# class GameModeClassName(Enum):
#     GameModeType.CAMPAIGN = CampaignMode
#     GameModeType.FREE_FOR_ALL = FreeForAllMode
#     GameModeType.CAPTURE_THE_FLAG = CaptureFlagMode

GAME_MODE_CLASS_MAPPING = {
    GameModeType.CAMPAIGN: CampaignMode,
    GameModeType.FREE_FOR_ALL: FreeForAllMode,
    GameModeType.CAPTURE_THE_FLAG: CaptureFlagMode,
}