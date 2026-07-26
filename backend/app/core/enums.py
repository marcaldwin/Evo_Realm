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


class EventType(str, Enum):
    FARM_WORK_SUCCEEDED = "farm_work_succeeded"
    FARM_WORK_REJECTED = "farm_work_rejected"
    WAGE_EARNED = "wage_earned"
    FOOD_PURCHASED = "food_purchased"
    FOOD_PURCHASE_REJECTED = "food_purchase_rejected"
    FOOD_CONSUMED = "food_consumed"
    FOOD_CONSUMPTION_REJECTED = "food_consumption_rejected"
    RESTED = "rested"


class WorldStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
