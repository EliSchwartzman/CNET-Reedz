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
        try:
            response = supabase.table("users").insert({
                "username": username,
                "password_hash": password_hash,
                "role": role.value,
                "reedz_balance": 0,
                "is_active": True
            }).execute()
            if hasattr(response, 'data') and response.data:
                return True, "User created successfully", response.data[0]["id"]
            return False, "Failed to create user", None
        except Exception as e:
            if "duplicate" in str(e).lower():
                return False, "Username already exists", None
            return False, f"Error: {str(e)}", None

    def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            response = supabase.table("users").select("*").eq("username", username).eq("is_active", True).execute()
            if hasattr(response,'data') and response.data:
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
        try:
            response = supabase.table("users").select("*").eq("id", user_id).eq("is_active", True).execute()
            if hasattr(response, 'data') and response.data:
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
        try:
            response = supabase.table("users").select("*").eq("is_active", True).order("reedz_balance", desc=True).execute()
            users = []
            if hasattr(response,'data') and response.data:
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

    def deactivate_user(self, user_id: int) -> Tuple[bool, str]:
        try:
            supabase.table("predictions").delete().eq("user_id", user_id).execute()
            supabase.table("users").delete().eq("id", user_id).execute()
            return True, "User and all associated data deleted"
        except Exception as e:
            return False, f"Error: {str(e)}"

    # ==================== BET OPERATIONS ====================

    def create_bet(self, week: int, title: str, description: str, answertype: str, creator_id: int) -> Tuple[bool, str, Optional[int]]:
        try:
            response = supabase.table("bets").insert({
                "week": week,
                "title": title,
                "description": description,
                "answertype": answertype,
                "status": BetStatus.OPEN.value,
                "correct_answer": None,
                "created_at": "now()",
                "closed_at": None,
                "resolved_at": None,
                "creator_id": creator_id,
            }).execute()
            if hasattr(response, 'data') and response.data:
                return True, "Bet created successfully", response.data[0]["id"]
            return False, "Failed to create bet", None
        except Exception as e:
            return False, f"Error: {str(e)}", None

    def get_bet_by_id(self, bet_id: int) -> Optional[Bet]:
        try:
            response = supabase.table("bets").select("*").eq("id", bet_id).single().execute()
            if not hasattr(response, 'data') or not response.data:
                return None
            row = response.data
            try:
                answertype = AnswerType(row["answertype"])
            except Exception:
                answertype = AnswerType.UNKNOWN
            bet_status = BetStatus(row["status"]) if row.get("status") else BetStatus.OPEN
            return Bet(
                id=row["id"],
                week=row["week"],
                title=row["title"],
                description=row.get("description"),
                status=bet_status,
                answertype=answertype,
                correct_answer=row.get("correct_answer"),
                created_at=row.get("created_at"),
                closed_at=row.get("closed_at"),
                resolved_at=row.get("resolved_at"),
                creator_id=row.get("creator_id")
            )
        except Exception as e:
            print(f"Error in get_bet_by_id: {e}")
            return None

    def get_bets_by_status(self, status: BetStatus) -> List[Bet]:
        try:
            response = supabase.table("bets").select("*").eq("status", status.value).order("created_at", desc=True).execute()
            bets = []
            if not hasattr(response, 'data') or not response.data:
                return []
            for row in response.data:
                try:
                    answertype = AnswerType(row["answertype"])
                except Exception:
                    answertype = AnswerType.UNKNOWN
                bet_status = BetStatus(row["status"]) if row.get("status") else BetStatus.OPEN
                bets.append(Bet(
                    id=row["id"],
                    week=row["week"],
                    title=row["title"],
                    description=row.get("description"),
                    status=bet_status,
                    answertype=answertype,
                    correct_answer=row.get("correct_answer"),
                    created_at=row.get("created_at"),
                    closed_at=row.get("closed_at"),
                    resolved_at=row.get("resolved_at"),
                    creator_id=row.get("creator_id")
                ))
            return bets
        except Exception as e:
            print("Error fetching bets:", e)
            return []

    def get_all_bets(self) -> List[Bet]:
        try:
            response = supabase.table("bets").select("*").order("created_at", desc=True).execute()
            bets = []
            if hasattr(response, 'data') and response.data:
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
        try:
            resp = supabase.table("bets").update({
                "status": BetStatus.CLOSED.value,
                "closed_at": "now()"
            }).eq("id", bet_id).execute()
            if hasattr(resp, 'data') and resp.data:
                return True, "Bet closed"
            else:
                return False, "Failed to close bet"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def resolve_bet(self, bet_id: int, correct_answer: str) -> Tuple[bool, str]:
        try:
            response = supabase.table("bets").update({
                "correct_answer": correct_answer,
                "status": BetStatus.RESOLVED.value,
                "resolved_at": "now()"
            }).eq("id", bet_id).execute()
            if not hasattr(response, 'data') or not response.data:
                return False, "Failed to resolve bet"
            return True, "Bet resolved successfully"
        except Exception as e:
            return False, str(e)

    # ==================== PREDICTION OPERATIONS ====================

    def create_prediction(self, bet_id: int, user_id: int, answer: str) -> Tuple[bool, str, Optional[int]]:
        try:
            response = supabase.table("predictions").insert({
                "bet_id": bet_id,
                "user_id": user_id,
                "answer": answer,
                "points_earned": 0,
                "created_at": "now()"
            }).execute()
            if hasattr(response, 'data') and response.data:
                return True, "Prediction created", response.data[0]["id"]
            return False, "Failed to create prediction", None
        except Exception as e:
            return False, f"Error: {str(e)}", None

    def get_prediction_by_user_bet(self, user_id: int, bet_id: int) -> Optional[Prediction]:
        try:
            response = supabase.table("predictions").select("*").eq("user_id", user_id).eq("bet_id", bet_id).execute()
            if hasattr(response, 'data') and response.data:
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
        try:
            response = supabase.table("predictions").select("*").eq("bet_id", bet_id).execute()
            predictions = []
            if hasattr(response, 'data') and response.data:
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
        try:
            response = supabase.table("predictions").select("*").eq("user_id", user_id).execute()
            predictions = []
            if hasattr(response, 'data') and response.data:
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
        try:
            resp = supabase.table("predictions").update({"points_earned": points}).eq("id", prediction_id).execute()
            print(f"update_prediction_points: Attempted to set id={prediction_id}, points={points}, resp={resp}")
            if hasattr(resp, 'data') and resp.data:
                print(f"SUCCESS: Updated prediction {prediction_id} with {points} points.")
                return True, "Points updated"
            else:
                print(f"FAIL: Could not update prediction {prediction_id} with {points} points. resp={resp}")
                return False, "Failed to update points"
        except Exception as e:
            print(f"Error updating prediction points: {e}")
            return False, f"Error: {str(e)}"

    def update_user_reedz(self, user_id: int, amount: int) -> Tuple[bool, str]:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                print(f"update_user_reedz: User {user_id} NOT FOUND")
                return False, "User not found"
            new_balance = user.reedz_balance + amount
            resp = supabase.table("users").update({"reedz_balance": new_balance}).eq("id", user_id).execute()
            print(f"update_user_reedz: User {user_id} amount={amount}, new_balance={new_balance}, resp={resp}")
            if hasattr(resp, 'data') and resp.data:
                return True, "Reedz balance updated"
            else:
                print(f"FAIL: Could not update user {user_id}'s balance. resp={resp}")
                return False, "Failed to update Reedz balance"
        except Exception as e:
            print(f"Error updating user Reedz: {e}")
            return False, f"Error: {str(e)}"

