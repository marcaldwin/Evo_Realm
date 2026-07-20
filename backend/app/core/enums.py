from enum import Enum


class Occupation(str, Enum):
    FARMER = "farmer"
    MERCHANT = "merchant"
    DOCTOR = "doctor"
    WORKER = "worker"
    LEADER = "leader"

class ResourceType(str, Enum):
    FOOD = "food"
    MEDICINE = "medicine"
    WOOD = "wood"
    MONEY = "money"

class LocationType(str, Enum):
    HOME = "home"
    FARM = "farm"
    MARKET = "market"
    CLINIC = "clinic"
    WORKSHOP = "workshop"
    TOWN_HALL = "town_hall"

class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    RESTING = "resting"
    MOVING = "moving"
    TALKING = "talking"
    TRADING = "trading"
    SEEKING_HELP = "seeking_help"
    INCAPACITATED = "incapacitated"


class ActionType(str, Enum):
    MOVE = "move"
    WORK = "work"
    EAT = "eat"
    REST = "rest"
    BUY = "buy"
    SELL = "sell"
    TRADE = "trade"
    TALK = "talk"
    HELP = "help"
    SEEK_MEDICAL_HELP = "seek_medical_help"
