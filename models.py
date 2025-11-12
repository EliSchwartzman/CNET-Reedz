from enum import Enum
from dataclasses import dataclass
from typing import Optional

class UserRole(Enum):
    ADMIN = "admin"
    MEMBER = "member"

class BetStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"

class AnswerType(Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"
    NUMERIC = "numeric"
    TEXT = "text"

@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: UserRole
    reedz_balance: int
    is_active: bool

@dataclass
class Bet:
    id: int
    week: int
    title: str
    description: str
    status: BetStatus
    answer_type: AnswerType
    correct_answer: Optional[str]
    created_at: str
    closed_at: Optional[str]
    resolved_at: Optional[str]

@dataclass
class Prediction:
    id: int
    bet_id: int
    user_id: int
    answer: str
    points_earned: int
    created_at: str
