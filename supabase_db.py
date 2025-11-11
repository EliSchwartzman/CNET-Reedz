import os
from typing import List, Optional, Tuple
from supabase import create_client, Client
from models import User, Bet, Prediction, UserRole, BetStatus, AnswerType

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class SupabaseDatabase:
    """Cloud database using Supabase PostgreSQL"""

    def __init__(self):
        """Initialize Supabase connection"""
        pass

    # ==================== USER OPERATIONS ====================

    def create_user(self, username: str, password_hash: str, role: UserRole) -> Tuple[bool, str, Optional[int]]:
        """Create a new user"""
        try:
            response = supabase.table("users").insert({
                "username": username,
                "password_hash": password_hash,
                "role": role.value,
                "reedz_balance": 0,
                "is_active": True
            }).execute()
            
            if response.data:
                return True, "User created successfully", response.data[0]["id"]
            return False, "Failed to create user", None
        except Exception as e:
            if "duplicate" in str(e).lower():
                return False, "Username already exists", None
            return False, f"Error: {str(e)}", None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (active only)"""
        try:
            response = supabase.table("users").select("*").eq("username", username).eq("is_active", True).execute()
            if response.data:
                row = response.data[0]
                return User(
                    id=row["id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=UserRole(row["role"]),
                    reedz_balance=row["reedz_balance"],
                    is_active=row["is_active"]
                )
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID (active only)"""
        try:
            response = supabase.table("users").select("*").eq("id", user_id).eq("is_active", True).execute()
            if response.data:
                row = response.data[0]
                return User(
                    id=row["id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=UserRole(row["role"]),
                    reedz_balance=row["reedz_balance"],
                    is_active=row["is_active"]
                )
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_all_users(self) -> List[User]:
        """Get all active users ordered by Reedz balance"""
        try:
            response = supabase.table("users").select("*").eq("is_active", True).order("reedz_balance", desc=True).execute()
            users = []
            for row in response.data:
                users.append(User(
                    id=row["id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=UserRole(row["role"]),
                    reedz_balance=row["reedz_balance"],
                    is_active=row["is_active"]
                ))
            return users
        except Exception as e:
            print(f"Error: {e}")
            return []

    def update_user_reedz(self, user_id: int, amount: int) -> Tuple[bool, str]:
        """Update user's Reedz balance"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            new_balance = user.reedz_balance + amount
            supabase.table("users").update({"reedz_balance": new_balance}).eq("id", user_id).execute()
            return True, "Reedz balance updated"
        except Exception as e:
            return False, f"Error: {str(e)}"
        
    

    def deactivate_user(self, user_id: int) -> Tuple[bool, str]:
        """Deactivate user and delete all associated predictions"""
        try:
            # Delete all predictions for this user
            supabase.table("predictions").delete().eq("user_id", user_id).execute()
            
            # Delete the user
            supabase.table("users").delete().eq("id", user_id).execute()
            
            return True, "User and all associated data deleted"
        except Exception as e:
            return False, f"Error: {str(e)}"

    # ==================== BET OPERATIONS ====================

    def create_bet(self, week: int, title: str, description: str) -> Tuple[bool, str, Optional[int]]:
        """Create a new bet"""
        try:
            response = supabase.table("bets").insert({
                "week": week,
                "title": title,
                "description": description,
                "status": BetStatus.OPEN.value,
                "correct_answer": None,
                "created_at": "now()",
                "closed_at": None,
                "resolved_at": None
            }).execute()
            
            if response.data:
                return True, "Bet created successfully", response.data[0]["id"]
            return False, "Failed to create bet", None
        except Exception as e:
            return False, f"Error: {str(e)}", None

    def get_bet_by_id(self, bet_id: int) -> Optional[Bet]:
        """Get bet by ID"""
        try:
            response = supabase.table("bets").select("*").eq("id", bet_id).execute()
            if response.data:
                row = response.data[0]
                return Bet(
                    id=row["id"],
                    week=row["week"],
                    title=row["title"],
                    description=row["description"],
                    status=BetStatus(row["status"]),
                    correct_answer=row.get("correct_answer"),
                    created_at=row["created_at"],
                    closed_at=row.get("closed_at"),
                    resolved_at=row.get("resolved_at")
                )
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_bets_by_status(self, status: BetStatus) -> List[Bet]:
        """Get all bets by status"""
        try:
            response = supabase.table("bets").select("*").eq("status", status.value).order("created_at", desc=True).execute()
            bets = []
            for row in response.data:
                bets.append(Bet(
                    id=row["id"],
                    week=row["week"],
                    title=row["title"],
                    description=row["description"],
                    status=BetStatus(row["status"]),
                    correct_answer=row.get("correct_answer"),
                    created_at=row["created_at"],
                    closed_at=row.get("closed_at"),
                    resolved_at=row.get("resolved_at")
                ))
            return bets
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_all_bets(self) -> List[Bet]:
        """Get all bets"""
        try:
            response = supabase.table("bets").select("*").order("created_at", desc=True).execute()
            bets = []
            for row in response.data:
                bets.append(Bet(
                    id=row["id"],
                    week=row["week"],
                    title=row["title"],
                    description=row["description"],
                    status=BetStatus(row["status"]),
                    correct_answer=row.get("correct_answer"),
                    created_at=row["created_at"],
                    closed_at=row.get("closed_at"),
                    resolved_at=row.get("resolved_at")
                ))
            return bets
        except Exception as e:
            print(f"Error: {e}")
            return []

    def close_bet(self, bet_id: int) -> Tuple[bool, str]:
        """Close a bet (no more predictions allowed)"""
        try:
            supabase.table("bets").update({
                "status": BetStatus.CLOSED.value,
                "closed_at": "now()"
            }).eq("id", bet_id).execute()
            return True, "Bet closed"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def resolve_bet(self, bet_id: int, correct_answer: str) -> Tuple[bool, str]:
        """Resolve a bet with the correct answer"""
        try:
            supabase.table("bets").update({
                "status": BetStatus.RESOLVED.value,
                "correct_answer": correct_answer,
                "resolved_at": "now()"
            }).eq("id", bet_id).execute()
            return True, "Bet resolved"
        except Exception as e:
            return False, f"Error: {str(e)}"

    # ==================== PREDICTION OPERATIONS ====================

    def create_prediction(self, bet_id: int, user_id: int, answer: str) -> Tuple[bool, str, Optional[int]]:
        """Create a prediction for a bet"""
        try:
            response = supabase.table("predictions").insert({
                "bet_id": bet_id,
                "user_id": user_id,
                "answer": answer,
                "points_earned": 0,
                "created_at": "now()"
            }).execute()
            
            if response.data:
                return True, "Prediction created", response.data[0]["id"]
            return False, "Failed to create prediction", None
        except Exception as e:
            return False, f"Error: {str(e)}", None

    def get_prediction_by_user_bet(self, user_id: int, bet_id: int) -> Optional[Prediction]:
        """Get user's prediction for a specific bet"""
        try:
            response = supabase.table("predictions").select("*").eq("user_id", user_id).eq("bet_id", bet_id).execute()
            if response.data:
                row = response.data[0]
                return Prediction(
                    id=row["id"],
                    bet_id=row["bet_id"],
                    user_id=row["user_id"],
                    answer=row["answer"],
                    points_earned=row["points_earned"],
                    created_at=row["created_at"]
                )
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_predictions_by_bet(self, bet_id: int) -> List[Prediction]:
        """Get all predictions for a bet"""
        try:
            response = supabase.table("predictions").select("*").eq("bet_id", bet_id).execute()
            predictions = []
            for row in response.data:
                predictions.append(Prediction(
                    id=row["id"],
                    bet_id=row["bet_id"],
                    user_id=row["user_id"],
                    answer=row["answer"],
                    points_earned=row["points_earned"],
                    created_at=row["created_at"]
                ))
            return predictions
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_predictions_by_user(self, user_id: int) -> List[Prediction]:
        """Get all predictions by a user"""
        try:
            response = supabase.table("predictions").select("*").eq("user_id", user_id).execute()
            predictions = []
            for row in response.data:
                predictions.append(Prediction(
                    id=row["id"],
                    bet_id=row["bet_id"],
                    user_id=row["user_id"],
                    answer=row["answer"],
                    points_earned=row["points_earned"],
                    created_at=row["created_at"]
                ))
            return predictions
        except Exception as e:
            print(f"Error: {e}")
            return []

    def update_prediction_points(self, prediction_id: int, points: int) -> Tuple[bool, str]:
        """Update points earned on a prediction"""
        try:
            supabase.table("predictions").update({"points_earned": points}).eq("id", prediction_id).execute()
            return True, "Points updated"
        except Exception as e:
            return False, f"Error: {str(e)}"
