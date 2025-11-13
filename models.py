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
    YESNO = "yesno"
    NUMERIC = "numeric"
    TEXT = "text"
    UNKNOWN = "unknown"


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
    description: Optional[str]
    status: BetStatus
    answertype: AnswerType
    correct_answer: Optional[str]
    created_at: str
    closed_at: Optional[str]
    resolved_at: Optional[str]
    creator_id: Optional[int]


@dataclass
class Prediction:
    id: int
    bet_id: int
    user_id: int
    answer: str
    points_earned: int
    created_at: str
