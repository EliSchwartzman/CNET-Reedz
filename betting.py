from typing import Tuple, List, Optional
from supabase_db import SupabaseDatabase
from models import User, Bet, Prediction, BetStatus, AnswerType, UserRole

class BettingManager:
    def __init__(self, db: SupabaseDatabase):
        self.db = db

    def create_bet(self, user: User, title: str, description: str, week: int, answer_type: AnswerType) -> Tuple[bool, str, Optional[int]]:
        if user.role != "admin" and user.role != UserRole.ADMIN:
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
        if bet.answer_type == AnswerType.NUMERIC or bet.answer_type == "numeric":
            try:
                float(answer.strip())
            except ValueError:
                return False, "You must enter a numeric value for this bet."
        return self.db.create_prediction(bet_id, user.id, answer.strip())

    def get_open_bets(self) -> List[Bet]:
        return self.db.get_bets_by_status(BetStatus.OPEN)

    def get_user_predictions(self, user: User) -> List[Tuple[Bet, Prediction]]:
        predictions = self.db.get_predictions_by_user(user.id)
        results = []
        for pred in predictions:
            bet = self.db.get_bet_by_id(pred.bet_id)
            if bet:
                results.append((bet, pred))
        return results

    def get_bet_summary(self, bet_id: int) -> Optional[dict]:
        bet = self.db.get_bet_by_id(bet_id)
        if not bet:
            return None
        predictions = self.db.get_predictions_for_bet(bet_id)
        prediction_details = []
        for pred in predictions:
            user = self.db.get_user_by_id(pred.user_id)
            if user:
                prediction_details.append({
                    'username': user.username,
                    'answer': pred.answer,
                    'points_earned': pred.points_earned,
                    'submitted_at': pred.created_at
                })
        return {
            'bet': bet,
            'predictions': prediction_details,
            'total_predictions': len(predictions)
        }
