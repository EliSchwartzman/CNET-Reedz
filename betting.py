from typing import Tuple, List, Optional
from supabase_db import SupabaseDatabase
from models import User, Bet, Prediction, BetStatus, AnswerType, UserRole

class BettingManager:
    def __init__(self, db: SupabaseDatabase):
        self.db = db

    def create_bet(self, user: User, title: str, description: str,
                week: int, answer_type: AnswerType) -> Tuple[bool, str, Optional[int]]:
        if user.role != UserRole.ADMIN:
            return False, "Only admin can create bets", None
        if not title or len(title) < 3:
            return False, "Title must be at least 3 characters", None
        if week < 1:
            return False, "Invalid week number", None
        return self.db.create_bet(week, title, description, answer_type.value, user.id)


    def submit_prediction(self, user: User, bet_id: int, answer: str) -> Tuple[bool, str]:
        bet = self.db.get_bet_by_id(bet_id)
        if not bet:
            return False, "Bet not found"
        if bet.status != BetStatus.OPEN:
            return False, "This bet is no longer accepting predictions"
        if not answer or len(answer.strip()) == 0:
            return False, "Answer cannot be empty"
        # Validate answer based on bet type
        if bet.answer_type == AnswerType.NUMERIC:
            try:
                float(answer.strip())
            except ValueError:
                return False, "You must enter a number for this bet"
        # Submit prediction
        return self.db.create_prediction(bet_id, user.id, answer.strip())

    def get_open_bets(self) -> List[Bet]:
        return self.db.get_bets_by_status(BetStatus.OPEN)
    # Rest of the class unchanged...
