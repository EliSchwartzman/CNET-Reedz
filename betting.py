"""
Betting system logic
"""
from typing import Tuple, List, Optional
from supabase_db import SupabaseDatabase
from models import User, Bet, Prediction, BetStatus, AnswerType

class BettingManager:
    """Handle betting operations"""

    def __init__(self, db: SupabaseDatabase):
        self.db = db

    def create_bet(self, user: User, title: str, description: str,
                   week: int, answer_type: AnswerType) -> Tuple[bool, str, Optional[int]]:
        """Create a new bet (admin only)"""
        if not user.is_admin():
            return False, "Only admin can create bets", None
        if not title or len(title) < 3:
            return False, "Title must be at least 3 characters", None
        if week < 1:
            return False, "Invalid week number", None
        # Create bet
        return self.db.create_bet(title, description, week, answer_type, user.id)

    def submit_prediction(self, user: User, bet_id: int, answer: str) -> Tuple[bool, str]:
        """Submit a prediction for a bet"""
        bet = self.db.get_bet(bet_id)
        if not bet:
            return False, "Bet not found"
        if bet.status != BetStatus.OPEN:
            return False, "This bet is no longer accepting predictions"
        if not answer or len(answer.strip()) == 0:
            return False, "Answer cannot be empty"
        # For numeric bets, validate number format
        if bet.answer_type == AnswerType.NUMERIC:
            try:
                float(answer.strip())
            except ValueError:
                return False, "Answer must be a number for this bet"
        # Only allow one prediction per user per bet
        if self.user_has_predicted(user.id, bet_id):
            return False, "You have already submitted a prediction for this bet"
        # Submit prediction
        return self.db.create_prediction(bet_id, user.id, answer.strip())

    def user_has_predicted(self, user_id: int, bet_id: int) -> bool:
        """Return True if user already submitted a prediction for this bet"""
        existing = self.db.get_prediction_by_user_bet(user_id, bet_id)
        return existing is not None

    def get_existing_prediction(self, user_id: int, bet_id: int) -> Optional[Prediction]:
        """Get the existing prediction object for this user and bet"""
        return self.db.get_prediction_by_user_bet(user_id, bet_id)

    def close_bet(self, user: User, bet_id: int) -> Tuple[bool, str]:
        """Close a bet to new predictions (admin only)"""
        if not user.is_admin():
            return False, "Only Commissioners can close bets"
        return self.db.update_bet_status(bet_id, BetStatus.CLOSED)

    def get_open_bets(self) -> List[Bet]:
        """Get all open bets"""
        return self.db.get_bets_by_status(BetStatus.OPEN)

    def get_user_predictions(self, user: User) -> List[Tuple[Bet, Prediction]]:
        """Get all predictions by a user with bet details"""
        predictions = self.db.get_predictions_by_user(user.id)
        results = []
        for pred in predictions:
            bet = self.db.get_bet(pred.bet_id)
            if bet:
                results.append((bet, pred))
        return results

    def get_bet_summary(self, bet_id: int) -> Optional[dict]:
        """Get summary of a bet including all predictions"""
        bet = self.db.get_bet(bet_id)
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
                    'submitted_at': pred.submitted_at
                })
        return {
            'bet': bet,
            'predictions': prediction_details,
            'total_predictions': len(predictions)
        }
