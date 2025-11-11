"""
Command-line interface for testing the Reedz platform
bingo
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
        print("🎵 REEDZ - Clarinet Section Betting Platform")
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
        
        # Show "Request Admin Access" for non-admins
        if not self.current_user.is_admin():
            print("\n5. Request Admin Access")
        
        if self.current_user.is_admin():
            print("\n--- Admin Functions ---")
            print("6. Create New Bet")
            print("7. Close Bet")
            print("8. Resolve Bet")
            print("9. View All Users")
            print("10. Promote User to Admin")
            print("11. Remove User")
            print("12. Adjust User Reedz")  # NEW
        
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
        elif choice == '5' and not self.current_user.is_admin():
            self.request_admin_access()
        elif choice == '6' and self.current_user.is_admin():
            self.create_bet()
        elif choice == '7' and self.current_user.is_admin():
            self.close_bet()
        elif choice == '8' and self.current_user.is_admin():
            self.resolve_bet()
        elif choice == '9' and self.current_user.is_admin():
            self.view_all_users()
        elif choice == '10' and self.current_user.is_admin():
            self.promote_user()
        elif choice == '11' and self.current_user.is_admin():
            self.remove_user()
        elif choice == '12' and self.current_user.is_admin():  # NEW
            self.adjust_user_reedz()
        elif choice == '0':
            self.logout()

    def adjust_user_reedz(self):
        """Adjust a user's Reedz balance (admin only)"""
        print("\n--- Adjust User Reedz ---")
        
        # Show all users
        users = self.db.get_all_users()
        
        print("\nAll Users:")
        for user in users:
            print(f"  ID {user.id}: {user.username} - {user.reedz_balance} Reedz")
        
        user_id = input("\nEnter User ID: ").strip()
        if not user_id.isdigit():
            print("❌ Invalid user ID")
            return
        
        user_id = int(user_id)
        target_user = self.db.get_user_by_id(user_id)
        
        if not target_user:
            print("❌ User not found")
            return
        
        print(f"\nCurrent Balance: {target_user.reedz_balance} Reedz")
        print("\nOptions:")
        print("1. Set to specific amount")
        print("2. Add Reedz")
        print("3. Subtract Reedz")
        
        option = input("Choice: ").strip()
        
        if option == '1':
            new_balance = input("Enter new balance: ").strip()
            if not new_balance.lstrip('-').isdigit():
                print("❌ Invalid amount")
                return
            
            success, msg = self.db.set_user_reedz(user_id, int(new_balance))
            print(f"\n{msg}")
        
        elif option == '2':
            amount = input("Enter amount to add: ").strip()
            if not amount.isdigit():
                print("❌ Invalid amount")
                return
            
            success, msg = self.db.update_user_reedz(user_id, int(amount))
            print(f"\n{msg}")
        
        elif option == '3':
            amount = input("Enter amount to subtract: ").strip()
            if not amount.isdigit():
                print("❌ Invalid amount")
                return
            
            success, msg = self.db.update_user_reedz(user_id, -int(amount))
            print(f"\n{msg}")
        
        else:
            print("❌ Invalid option")

    
    def register(self):
        """Register new user with role selection"""
        print("\n--- Register ---")
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        print("\nSelect Role:")
        print("1. Member (Regular user)")
        print("2. Commissioner (Section Leader / Squad Leader)")
        print("3. Treasurer (Maintains official ledger)")
        
        role_choice = input("Choice: ").strip()
        
        # Determine role
        if role_choice == '1':
            role = UserRole.MEMBER
        elif role_choice == '2':
            # Require admin password for Commissioner
            admin_pwd = input("\n🔒 Admin Registration Password: ").strip()
            if admin_pwd != ADMIN_REGISTRATION_PASSWORD:
                print("\n❌ Incorrect admin password. Registration denied.")
                return
            role = UserRole.COMMISSIONER
        elif role_choice == '3':
            # Require admin password for Treasurer
            admin_pwd = input("\n🔒 Admin Registration Password: ").strip()
            if admin_pwd != ADMIN_REGISTRATION_PASSWORD:
                print("\n❌ Incorrect admin password. Registration denied.")
                return
            role = UserRole.TREASURER
        else:
            print("\n❌ Invalid choice. Defaulting to Member.")
            role = UserRole.MEMBER
        
        # Create user with selected role
        success, msg, user_id = self.db.create_user(username, password, role)
        print(f"\n{msg}")
        if success:
            print(f"✅ User ID: {user_id}")
            print(f"   Role: {role.value.title()}")
    
    def login(self):
        """Login user"""
        print("\n--- Login ---")
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        success, msg, user = self.auth.login(username, password)
        print(f"\n{msg}")
        
        if success:
            self.current_user = user
    
    def logout(self):
        """Logout user"""
        self.current_user = None
        print("\nLogged out successfully!")
    
    def create_admin_interactive(self):
        """Create admin user interactively"""
        print("\n--- Create Admin User ---")
        print("This will create a user with admin privileges.")
        
        username = input("\nUsername: ").strip()
        password = input("Password: ").strip()
        
        print("\nSelect Role:")
        print("1. Commissioner (Section Leader / Squad Leader)")
        print("2. Treasurer (Maintains official ledger)")
        role_choice = input("Choice: ").strip()
        
        if role_choice == '1':
            role = UserRole.COMMISSIONER
            role_name = "Commissioner"
        elif role_choice == '2':
            role = UserRole.TREASURER
            role_name = "Treasurer"
        else:
            print("\n❌ Invalid choice")
            return
        
        success, msg, user_id = self.db.create_user(username, password, role)
        print(f"\n{msg}")
        
        if success:
            print(f"✅ Admin User Created!")
            print(f"   User ID: {user_id}")
            print(f"   Username: {username}")
            print(f"   Role: {role_name}")
            print("\nYou can now login with these credentials.")
    
    def request_admin_access(self):
        """Allow existing user to become admin with password"""
        print("\n--- Request Admin Access ---")
        print("To become an admin, you must know the admin password.")
        
        admin_pwd = input("\n🔒 Enter Admin Password: ").strip()
        
        if admin_pwd != ADMIN_REGISTRATION_PASSWORD:
            print("\n❌ Incorrect admin password. Access denied.")
            return
        
        print("\n✅ Password correct!")
        print("\nSelect Admin Role:")
        print("1. Commissioner (Section Leader / Squad Leader)")
        print("2. Treasurer (Maintains official ledger)")
        
        role_choice = input("Choice: ").strip()
        
        if role_choice == '1':
            new_role = UserRole.COMMISSIONER
            role_name = "Commissioner"
        elif role_choice == '2':
            new_role = UserRole.TREASURER
            role_name = "Treasurer"
        else:
            print("\n❌ Invalid choice")
            return
        
        # Update user's role
        success, msg = self.db.update_user_role(self.current_user.id, new_role)
        
        if success:
            print(f"\n✅ You have been promoted to {role_name}!")
            print("Please logout and login again for changes to take effect.")
            
            # Refresh current user data
            self.current_user = self.db.get_user_by_id(self.current_user.id)
        else:
            print(f"\n❌ {msg}")
    
    def promote_user(self):
        """Promote existing user to admin (admin only)"""
        print("\n--- Promote User to Admin ---")
        
        # Show all members
        users = self.db.get_all_users()
        members = [u for u in users if u.role == UserRole.MEMBER]
        
        if not members:
            print("No members to promote.")
            return
        
        print("\nCurrent Members:")
        for user in members:
            print(f"  ID {user.id}: {user.username}")
        
        user_id = input("\nEnter User ID to promote: ").strip()
        if not user_id.isdigit():
            print("Invalid user ID")
            return
        
        print("\nSelect New Role:")
        print("1. Commissioner")
        print("2. Treasurer")
        role_choice = input("Choice: ").strip()
        
        if role_choice == '1':
            new_role = UserRole.COMMISSIONER
        elif role_choice == '2':
            new_role = UserRole.TREASURER
        else:
            print("Invalid choice")
            return
        
        success, msg = self.auth.promote_user(self.current_user, int(user_id), new_role)
        print(f"\n{msg}")
    
    def remove_user(self):
        """Remove a user from the system (admin only)"""
        print("\n--- Remove User ---")
        
        # Show all users
        users = self.db.get_all_users()
        
        print("\nAll Users:")
        for user in users:
            if user.id != self.current_user.id:  # Don't allow removing self
                print(f"  ID {user.id}: {user.username} ({user.role.value}) - {user.reedz_balance} Reedz")
        
        user_id = input("\nEnter User ID to remove: ").strip()
        if not user_id.isdigit():
            print("❌ Invalid user ID")
            return
        
        user_id = int(user_id)
        
        # Prevent self-deletion
        if user_id == self.current_user.id:
            print("❌ You cannot remove yourself!")
            return
        
        # Get user details
        target_user = self.db.get_user_by_id(user_id)
        if not target_user:
            print("User not found")
            return
        
        # Confirm deletion
        confirm = input(f"\n Are you sure you want to remove '{target_user.username}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return
        
        # Remove user
        success, msg = self.db.delete_user(user_id)
        print(f"\n{msg}")
    
    def view_open_bets(self):
        """View all open bets"""
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
            
            # Show if user has already predicted
            predictions = self.db.get_predictions_for_bet(bet.id)
            user_pred = next((p for p in predictions if p.user_id == self.current_user.id), None)
            if user_pred:
                print(f"✅ Your prediction: {user_pred.answer}")
    
    def submit_prediction(self):
        """Submit a prediction"""
        print("\n--- Submit Prediction ---")
        
        # Show open bets first
        bets = self.betting.get_open_bets()
        if not bets:
            print("No open bets available.")
            return
        
        print("\nAvailable Bets:")
        for bet in bets:
            print(f"  ID {bet.id}: Week {bet.week} - {bet.title}")
        
        bet_id = input("\nEnter Bet ID: ").strip()
        if not bet_id.isdigit():
            print("Invalid bet ID")
            return
        
        answer = input("Your Answer: ").strip()
        
        success, msg = self.betting.submit_prediction(self.current_user, int(bet_id), answer)
        print(f"\n{msg}")
        
        # Refresh user data
        self.current_user = self.db.get_user_by_id(self.current_user.id)
    
    def view_my_predictions(self):
        """View user's predictions"""
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
                print(f"✨ Points Earned: {pred.points_earned} Reedz")
    
    def view_leaderboard(self):
        """View leaderboard"""
        print("\n--- Leaderboard ---")
        
        leaderboard = self.scoring.get_leaderboard(limit=20)
        
        print(f"\n{'Rank':<6} {'Username':<20} {'Reedz':<10} {'Predictions':<15} {'Exact':<10}")
        print("=" * 65)
        
        for entry in leaderboard:
            print(f"{entry['rank']:<6} {entry['username']:<20} {entry['reedz_balance']:<10} "
                  f"{entry['total_predictions']:<15} {entry['exact_answers']:<10}")
    
    def create_bet(self):
        """Create new bet (admin only)"""
        print("\n--- Create New Bet ---")
        
        title = input("Title: ").strip()
        description = input("Description: ").strip()
        week = input("Week Number: ").strip()
        
        if not week.isdigit():
            print("Invalid week number")
            return
        
        print("\nAnswer Type:")
        print("1. Numeric (e.g., score difference, time)")
        print("2. Text (e.g., name, word answer)")
        answer_type_choice = input("Choice: ").strip()
        
        if answer_type_choice == '1':
            answer_type = AnswerType.NUMERIC
        elif answer_type_choice == '2':
            answer_type = AnswerType.TEXT
        else:
            print("Invalid choice")
            return
        
        success, msg, bet_id = self.betting.create_bet(
            self.current_user, title, description, int(week), answer_type
        )
        print(f"\n{msg}")
        if success:
            print(f"✅ Bet ID: {bet_id}")
    
    def close_bet(self):
        """Close bet (admin only)"""
        print("\n--- Close Bet ---")
        
        # Show open bets
        bets = self.betting.get_open_bets()
        if not bets:
            print("No open bets to close.")
            return
        
        print("\nOpen Bets:")
        for bet in bets:
            print(f"  ID {bet.id}: Week {bet.week} - {bet.title}")
        
        bet_id = input("\nEnter Bet ID to close: ").strip()
        if not bet_id.isdigit():
            print("Invalid bet ID")
            return
        
        success, msg = self.betting.close_bet(self.current_user, int(bet_id))
        print(f"\n{msg}")
    
    def resolve_bet(self):
        """Resolve bet and distribute Reedz (admin only)"""
        print("\n--- Resolve Bet ---")
        
        # Show closed bets
        closed_bets = self.db.get_bets_by_status(BetStatus.CLOSED)
        if not closed_bets:
            print("No closed bets to resolve.")
            return
        
        print("\nClosed Bets:")
        for bet in closed_bets:
            print(f"  ID {bet.id}: Week {bet.week} - {bet.title}")
        
        bet_id = input("\nEnter Bet ID to resolve: ").strip()
        if not bet_id.isdigit():
            print("Invalid bet ID")
            return
        
        # Show bet summary
        summary = self.betting.get_bet_summary(int(bet_id))
        if not summary:
            print("Bet not found")
            return
        
        bet = summary['bet']
        print(f"\n{'='*50}")
        print(f"Bet: {bet.title}")
        print(f"Answer Type: {bet.answer_type.value}")
        print(f"Total Predictions: {summary['total_predictions']}")
        print(f"\nPredictions:")
        for pred in summary['predictions']:
            print(f"  {pred['username']}: {pred['answer']}")
        
        correct_answer = input("\nEnter Correct Answer: ").strip()
        
        confirm = input(f"\nConfirm answer '{correct_answer}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return
        
        success, msg, details = self.scoring.resolve_bet(self.current_user, int(bet_id), correct_answer)
        print(f"\n{msg}")
        
        if success and details:
            print(f"\n✨ Scoring Summary:")
            print(f"   Total Predictions: {details['total_predictions']}")
            print(f"   Total Reedz Distributed: {details['total_reedz_distributed']}")
        
        # Refresh user data
        self.current_user = self.db.get_user_by_id(self.current_user.id)
    
    def view_all_users(self):
        """View all users (admin only)"""
        print("\n--- All Users ---")
        
        users = self.db.get_all_users()
        
        print(f"\n{'ID':<5} {'Username':<20} {'Role':<15} {'Reedz':<10} {'Active':<10}")
        print("=" * 65)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.role.value:<15} "
                  f"{user.reedz_balance:<10} {'Yes' if user.is_active else 'No':<10}")

def main():
    """Entry point"""
    cli = ReedziCLI()
    cli.run()

if __name__ == "__main__":
    main()
