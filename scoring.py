"""
Scoring and Reedz distribution logic
"""
from typing import Tuple, List, Dict
from supabase_db import SupabaseDatabase
from models import User, Bet, Prediction, BetStatus, AnswerType


class ScoringManager:
    """Handle scoring and Reedz distribution"""
    
    def __init__(self, db: SupabaseDatabase):
        self.db = db
    
    def resolve_bet(self, user: User, bet_id: int, correct_answer: str) -> Tuple[bool, str, Dict]:
        """
        Resolve a bet and distribute Reedz (commissioner only)
        
        Returns: (success, message, scoring_details)
        """
        # Check permissions
        if not user.is_admin():
            return False, "Only commissioners can resolve bets", {}
        
        # Get bet
        bet = self.db.get_bet(bet_id)
        if not bet:
            return False, "Bet not found", {}
        
        if bet.status == BetStatus.RESOLVED:
            return False, "Bet already resolved", {}
        
        # Set correct answer
        success, msg = self.db.set_bet_answer(bet_id, correct_answer)
        if not success:
            return False, msg, {}
        
        # Get all predictions
        predictions = self.db.get_predictions_for_bet(bet_id)
        
        if len(predictions) == 0:
            self.db.update_bet_status(bet_id, BetStatus.RESOLVED)
            return True, "Bet resolved (no predictions)", {}
        
        # Calculate scores
        scores = self._calculate_scores(predictions, correct_answer, bet.answertype)
        
        # Distribute Reedz and update predictions
        total_distributed = 0
        for pred_id, points in scores.items():
            self.db.update_prediction_points(pred_id, points)
            
            # Find user for this prediction
            prediction = next((p for p in predictions if p.id == pred_id), None)
            if prediction:
                self.db.update_user_reedz(prediction.user_id, points)
                total_distributed += points
        
        # Mark bet as resolved
        self.db.update_bet_status(bet_id, BetStatus.RESOLVED)
        
        scoring_details = {
            'total_predictions': len(predictions),
            'total_reedz_distributed': total_distributed,
            'scores': scores
        }
        
        return True, f"Bet resolved! Distributed {total_distributed} Reedz", scoring_details
    
    def _calculate_scores(self, predictions: List[Prediction], 
                         correct_answer: str, answer_type: AnswerType) -> Dict[int, int]:
        """
        Calculate Reedz for each prediction based on accuracy
        
        Returns: dict mapping prediction_id -> points
        
        Scoring rules:
        - 1st place: 21 Reedz
        - 2nd place: 20 Reedz
        - 3rd place: 19 Reedz
        - etc.
        - +5 bonus for exact answer
        - Ties: All tied users get the SAME points
        """
        scores = {}
        
        if answer_type == AnswerType.NUMERIC:
            # Calculate differences for numeric answers
            correct_value = float(correct_answer)
            
            differences = []
            for pred in predictions:
                try:
                    pred_value = float(pred.answer)
                    diff = abs(pred_value - correct_value)
                    differences.append((pred.id, diff, pred_value == correct_value))
                except ValueError:
                    # Invalid numeric answer gets no points
                    scores[pred.id] = 0
            
            # Sort by difference (closest first)
            differences.sort(key=lambda x: x[1])
            
            # Assign points with proper tie handling
            base_points = 21
            current_rank = 0
            previous_diff = None
            
            for i, (pred_id, diff, is_exact) in enumerate(differences):
                # If this is a new difference value, increment rank
                if previous_diff is None or diff != previous_diff:
                    current_rank = i
                
                # Calculate points based on current rank
                points = max(base_points - current_rank, 1)
                
                # Add exact answer bonus
                if is_exact:
                    points += 5
                
                scores[pred_id] = points
                previous_diff = diff
        
        else:  # TEXT answer type
            # For text, only exact matches get points
            correct_lower = correct_answer.strip().lower()
            
            exact_matches = []
            non_matches = []
            
            for pred in predictions:
                pred_lower = pred.answer.strip().lower()
                if pred_lower == correct_lower:
                    exact_matches.append(pred.id)
                else:
                    non_matches.append(pred.id)
            
            # Exact matches all get 26 Reedz (21 + 5 bonus)
            for pred_id in exact_matches:
                scores[pred_id] = 26
            
            # Non-matches get 0
            for pred_id in non_matches:
                scores[pred_id] = 0
        
        return scores
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get top users by Reedz balance
        
        Returns: List of user stats
        """
        users = self.db.get_all_users()
        
        leaderboard = []
        for i, user in enumerate(users[:limit], 1):
            # Get prediction stats
            predictions = self.db.get_predictions_by_user(user.id)
            
            exact_count = sum(1 for p in predictions if p.points_earned and p.points_earned >= 26)
            
            leaderboard.append({
                'rank': i,
                'username': user.username,
                'reedz_balance': user.reedz_balance,
                'total_predictions': len(predictions),
                'exact_answers': exact_count
            })
        
        return leaderboard
