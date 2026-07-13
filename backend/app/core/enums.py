from enum import Enum


class Occupation(str, Enum):
    FARMER = "farmer"
    MERCHANT = "merchant"
    DOCTOR = "doctor"
    WORKER = "worker"
    LEADER = "leader"