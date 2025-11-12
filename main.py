"""
Command-line interface for testing the Reedz platforms
"""

from supabase_db import SupabaseDatabase
from auth import AuthManager
from betting import BettingManager
from scoring import ScoringManager
from models import UserRole, AnswerType, BetStatus

# Admin registration password
ADMIN_REGISTRATION_PASSWORD = "reedz123"

class ReedziCLI:
    """Command-line interface for Reedz platform"""

    def __init__(self):
        self.db = SupabaseDatabase()
        self.auth = AuthManager(self.db)
        self.betting = BettingManager(self.db)
        self.scoring = ScoringManager(self.db)
        self.current_user = None

    def run(self):
        """Main application loop"""
        print("=" * 50)
        print("REEDZ - Clarinet Section Betting Platform")
        print("=" * 50)
        while True:
            if not self.current_user:
                self.show_auth_menu()
            else:
                self.show_main_menu()

    def show_auth_menu(self):
        """Show authentication menu"""
        print("\n--- Authentication ---")
        print("1. Login")
        print("2. Register")
        print("3. Create Admin User")
        print("4. Exit")
        choice = input("\nChoice: ").strip()
        if choice == '1':
            self.login()
        elif choice == '2':
            self.register()
        elif choice == '3':
            self.create_admin_interactive()
        elif choice == '4':
            print("Goodbye!")
            exit(0)

    def show_main_menu(self):
        """Show main menu"""
        print(f"\n--- Welcome, {self.current_user.username}! ---")
        print(f"Reedz Balance: {self.current_user.reedz_balance}")
        print(f"Role: {self.current_user.role.value.title()}")
        print("\n1. View Open Bets")
        print("2. Submit Prediction")
        print("3. View My Predictions")
        print("4. View Leaderboard")
        if self.current_user.role != UserRole.ADMIN:
            print("\n5. Request Admin Access")
        if self.current_user.role == UserRole.ADMIN:
            print("\n--- Admin Functions ---")
            print("6. Create New Bet")
            print("7. Close Bet")
            print("8. Resolve Bet")
            print("9. View All Users")
            print("10. Promote User to Admin")
            print("11. Remove User")
            print("12. Adjust User Reedz")
        print("\n0. Logout")
        choice = input("\nChoice: ").strip()
        if choice == '1':
            self.view_open_bets()
        elif choice == '2':
            self.submit_prediction()
        elif choice == '3':
            self.view_my_predictions()
        elif choice == '4':
            self.view_leaderboard()
        elif choice == '5' and self.current_user.role != UserRole.ADMIN:
            self.request_admin_access()
        elif choice == '6' and self.current_user.role == UserRole.ADMIN:
            self.create_bet()
        elif choice == '7' and self.current_user.role == UserRole.ADMIN:
            self.close_bet()
        elif choice == '8' and self.current_user.role == UserRole.ADMIN:
            self.resolve_bet()
        elif choice == '9' and self.current_user.role == UserRole.ADMIN:
            self.view_all_users()
        elif choice == '10' and self.current_user.role == UserRole.ADMIN:
            self.promote_user()
        elif choice == '11' and self.current_user.role == UserRole.ADMIN:
            self.remove_user()
        elif choice == '12' and self.current_user.role == UserRole.ADMIN:
            self.adjust_user_reedz()
        elif choice == '0':
            self.logout()

    def view_open_bets(self):
        print("\n--- Open Bets ---")
        bets = self.betting.get_open_bets()
        if not bets:
            print("No open bets at the moment.")
            return
        for bet in bets:
            print(f"\n{'='*50}")
            print(f"ID: {bet.id}")
            print(f"Week {bet.week}: {bet.title}")
            print(f"Description: {bet.description}")
            print(f"Answer Type: {bet.answer_type.value}")

    def submit_prediction(self):
        print("\n--- Submit Prediction ---")
        bets = self.betting.get_open_bets()
        if not bets:
            print("No open bets available.")
            return
        print("\nAvailable Bets:")
        for bet in bets:
            print(f" ID {bet.id}: Week {bet.week} - {bet.title} ({bet.answer_type.value})")
        betid = input("Enter Bet ID: ").strip()
        if not betid.isdigit():
            print("Invalid bet ID")
            return
        bet = self.db.get_bet_by_id(int(betid))
        if not bet:
            print("Bet not found.")
            return
        if bet.answer_type == AnswerType.NUMERIC:
            answer = input("Your prediction (enter number): ").strip()
        elif bet.answer_type == AnswerType.TEXT:
            answer = input("Your prediction (enter text): ").strip()
        else:
            answer = input("Your prediction (YES/NO/UNKNOWN): ").strip()
        success, msg = self.betting.submit_prediction(self.current_user, int(betid), answer)
        print(msg)
        self.current_user = self.db.get_user_by_id(self.current_user.id)

    def view_my_predictions(self):
        print("\n--- My Predictions ---")
        predictions = self.betting.get_user_predictions(self.current_user)
        if not predictions:
            print("You haven't made any predictions yet.")
            return
        for bet, pred in predictions:
            print(f"\n{'='*50}")
            print(f"Week {bet.week}: {bet.title}")
            print(f"Your Answer: {pred.answer}")
            print(f"Status: {bet.status.value}")
            if bet.status.value == 'resolved' and bet.correct_answer:
                print(f"Correct Answer: {bet.correct_answer}")
            if pred.points_earned is not None:
                print(f"Points Earned: {pred.points_earned} Reedz")

    def view_leaderboard(self):
        print("\n--- Leaderboard ---")
        leaderboard = self.scoring.get_leaderboard(limit=20)
        print(f"\n{'Rank':<6} {'Username':<20} {'Reedz':<10} {'Predictions':<15} {'Exact':<10}")
        print("=" * 65)
        for entry in leaderboard:
            print(f"{entry['rank']:<6} {entry['username']:<20} {entry['reedz_balance']:<10} "
                  f"{entry['total_predictions']:<15} {entry['exact_answers']:<10}")

    def create_bet(self):
        print("\n--- Create New Bet ---")
        title = input("Title: ").strip()
        description = input("Description: ").strip()
        week = input("Week Number: ").strip()
        if not week.isdigit():
            print("Invalid week number")
            return
        print("\nAnswer Type:")
        print("1. Numeric")
        print("2. Text")
        print("3. YES/NO/UNKNOWN")
        answer_type_choice = input("Choice: ").strip()
        if answer_type_choice == '1':
            answer_type = AnswerType.NUMERIC
        elif answer_type_choice == '2':
            answer_type = AnswerType.TEXT
        else:
            answer_type = AnswerType.UNKNOWN
        success, msg, bet_id = self.betting.create_bet(
            self.current_user, title, description, int(week), answer_type
        )
        print(f"\n{msg}")
        if success:
            print(f"Bet ID: {bet_id}")

    def close_bet(self):
        print("\n--- Close Bet ---")
        bets = self.betting.get_open_bets()
        if not bets:
            print("No open bets to close.")
            return
        print("\nOpen Bets:")
        for bet in bets:
            print(f" ID {bet.id}: Week {bet.week} - {bet.title}")
        bet_id = input("Enter Bet ID to close: ").strip()
        if not bet_id.isdigit():
            print("Invalid bet ID")
            return
        success, msg = self.betting.close_bet(self.current_user, int(bet_id))
        print(f"\n{msg}")

    def resolve_bet(self):
        print("\n--- Resolve Bet ---")
        closed_bets = self.db.get_bets_by_status(BetStatus.CLOSED)
        if not closed_bets:
            print("No closed bets to resolve.")
            return
        print("\nClosed Bets:")
        for bet in closed_bets:
            print(f" ID {bet.id}: Week {bet.week} - {bet.title}")
        bet_id = input("Enter Bet ID to resolve: ").strip()
        if not bet_id.isdigit():
            print("Invalid bet ID")
            return
        summary = self.betting.get_bet_summary(int(bet_id))
        if not summary:
            print("Bet not found")
            return
        bet = summary['bet']
        print(f"\n{'='*50}")
        print(f"Bet: {bet.title}")
        print(f"Answer Type: {bet.answer_type.value}")
        print(f"Total Predictions: {summary['total_predictions']}")
        print("\nPredictions:")
        for pred in summary['predictions']:
            print(f" {pred['username']}: {pred['answer']}")
        correct_answer = input("Enter Correct Answer: ").strip()
        confirm = input(f"Confirm answer '{correct_answer}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return
        success, msg, details = self.scoring.resolve_bet(self.current_user, int(bet_id), correct_answer)
        print(f"\n{msg}")
        if success and details:
            print("\nScoring Summary:")
            print(f" Total Predictions: {details['total_predictions']}")
            print(f" Total Reedz Distributed: {details['total_reedz_distributed']}")
        self.current_user = self.db.get_user_by_id(self.current_user.id)

    # Add other admin/user management, registration, login/logout as in your original code

def main():
    """Entry point"""
    cli = ReedziCLI()
    cli.run()

if __name__ == "__main__":
    main()
