"""
Data models for the Reedz betting platform
"""
from dataclasses import dataclass
from datetime import datetime # Used to keep track of when user interactions occur and to ensure rule following
from typing import Optional, List
from enum import Enum       # Enum works similar to a dictionary where a variable is paired with a key.


class UserRole(Enum):  
    """User role types"""
    MEMBER = "member"
    COMMISSIONER = "commissioner"
    TREASURER = "treasurer"

class BetStatus(Enum):
    """Bet status types"""
    OPEN = "open"           # Accepting predictions
    CLOSED = "closed"       # No longer accepting predictions
    RESOLVED = "resolved"   # Result entered, Reedz distributed

class AnswerType(Enum):
    """Type of answer expected"""
    NUMERIC = "numeric"     # Expecting number responses
    TEXT = "text"           # Expecting letter responses

@dataclass
class User:                 # Defines the characteristics of a user and sets the type
    """User data model"""
    id: int                 # A unique user ID is generated upon registering
    username: str           # Expecting string 
    password_hash: str      
    role: UserRole          # Sets a role to connect 
    reedz_balance: int = 0  # Sets the default balance to 0
    is_active: bool = True  # Sets the default active state to true when the account is made
    created_at: datetime = None
    
    def is_admin(self) -> bool:     # A basic check to see if the user has admin permisions
        """Check if user has admin privileges"""
        return self.role in [UserRole.COMMISSIONER, UserRole.TREASURER]

@dataclass
class Bet:
    """Bet data model"""
    id: int                 # Every bet will have a bet ID to make it unique from other bets
    title: str              # The title of the bet that the admin sets
    description: str        # A description explaining specifically what the bet is
    week: int               # Additional uniqueness specific to each season aligning with the weeks of the season
    answer_type: AnswerType     # 
    correct_answer: Optional[str] = None
    status: BetStatus = BetStatus.OPEN
    created_by: int = None  # User ID of commissioner who created it
    created_at: datetime = None # Datetime has not been configured at this time
    closed_at: datetime = None
    resolved_at: datetime = None

@dataclass
class Prediction:
    """User prediction data model"""
    id: int
    bet_id: int
    user_id: int
    answer: str
    submitted_at: datetime = None
    points_earned: Optional[int] = None  # Set when bet is resolved

@dataclass
class LeaderboardEntry:
    """Leaderboard entry"""
    rank: int
    username: str
    reedz_balance: int
    total_predictions: int
    exact_answers: int