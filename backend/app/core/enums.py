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
    AGENT_MOVED = "agent_moved"
    AGENT_MOVEMENT_REJECTED = "agent_movement_rejected"
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


class MemoryMode(str, Enum):
    NO_MEMORY = "no_memory"
    VECTOR_EPISODIC = "vector_episodic"


class DialogueAct(str, Enum):
    REQUEST = "request"
    OFFER = "offer"
    PROMISE = "promise"
    INFORM = "inform"
    AGREE = "agree"
    REJECT = "reject"
    THANK = "thank"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class InteractionOutcome(str, Enum):
    SUCCESSFUL_TRADE = "successful_trade"
    EMERGENCY_HELP = "emergency_help"
    REFUSAL = "refusal"
    PROMISE_FULFILLED = "promise_fulfilled"
    BROKEN_PROMISE = "broken_promise"


class StreamEventType(str, Enum):
    STREAM_READY = "stream_ready"
    TICK_COMMITTED = "tick_committed"
    AGENT_STATE_CHANGED = "agent_state_changed"
    AGENT_MOVED = "agent_moved"
    ACTION_EXECUTED = "action_executed"
    ACTION_REJECTED = "action_rejected"
    CONVERSATION_MESSAGE = "conversation_message"
    RELATIONSHIP_CHANGED = "relationship_changed"
    MEMORY_CREATED = "memory_created"
    WORLD_EVENT = "world_event"
