"""
Streamlit web interface for Reedz platform
"""
import streamlit as st
from database import Database
from auth import AuthManager
from betting import BettingManager
from scoring import ScoringManager
from models import UserRole, AnswerType, BetStatus


# Admin registration password
ADMIN_REGISTRATION_PASSWORD = "reedz123"


# Page configuration
st.set_page_config(
    page_title="REEDZ Platform",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize database and managers
@st.cache_resource
def get_managers():
    db = Database()
    auth = AuthManager(db)
    betting = BettingManager(db)
    scoring = ScoringManager(db)
    return db, auth, betting, scoring


db, auth, betting, scoring = get_managers()


# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None


# Custom CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #c41e3a 0%, #a31830 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)


def refresh_user():
    """Refresh current user data"""
    if st.session_state.user:
        user = db.get_user_by_id(st.session_state.user.id)
        st.session_state.user = user


def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def login_page():
    """Display login/registration page"""
    st.markdown('<div class="main-header"><h1>🎵 REEDZ</h1><p>Clarinet Section Betting Platform</p></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", width='stretch')
            
            if submit:
                if not username or not password:
                    st.error("Please enter username and password")
                else:
                    success, msg, user = auth.login(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(msg)
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_user")
            new_password = st.text_input("Password", type="password", key="reg_pass")
            
            role_option = st.selectbox("Role", 
                                      ["Member", "Commissioner", "Treasurer"])
            
            admin_password = ""
            if role_option in ["Commissioner", "Treasurer"]:
                admin_password = st.text_input("Admin Password", type="password", key="admin_pass")
            
            register = st.form_submit_button("Register", width='stretch')
            
            if register:
                if not new_username or not new_password:
                    st.error("Username and password are required")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    # Determine role
                    if role_option == "Member":
                        role = UserRole.MEMBER
                    elif role_option == "Commissioner":
                        if admin_password != ADMIN_REGISTRATION_PASSWORD:
                            st.error("Incorrect admin password")
                            st.stop()
                        role = UserRole.COMMISSIONER
                    else:  # Treasurer
                        if admin_password != ADMIN_REGISTRATION_PASSWORD:
                            st.error("Incorrect admin password")
                            st.stop()
                        role = UserRole.TREASURER
                    
                    success, msg, user_id = db.create_user(new_username, new_password, role)
                    if success:
                        st.success(f"{msg} You can now login!")
                    else:
                        st.error(msg)


def dashboard_page():
    """Main dashboard"""
    user = st.session_state.user
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<div class="main-header"><h1>Welcome, {user.username}! 🎵</h1></div>', unsafe_allow_html=True)
    with col2:
        if st.button("Logout", width='stretch'):
            logout()
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Reedz Balance", user.reedz_balance)
    with col2:
        st.metric("Role", user.role.value.title())
    with col3:
        open_bets = betting.get_open_bets()
        st.metric("Open Bets", len(open_bets))
    
    st.markdown("---")
    
    # Main content tabs
    tabs = ["Open Bets", "Submit Prediction", "My Predictions", "Leaderboard"]
    if not user.is_admin():
        tabs.append("Request Admin")
    
    selected_tab = st.tabs(tabs)
    
    # Open Bets Tab
    with selected_tab[0]:
        st.subheader("📊 Open Bets")
        bets = betting.get_open_bets()
        
        if not bets:
            st.info("No open bets at the moment.")
        else:
            for bet in bets:
                with st.expander(f"Week {bet.week}: {bet.title}"):
                    st.write(f"**Description:** {bet.description}")
                    st.write(f"**Answer Type:** {bet.answer_type.value}")
                    
                    predictions = db.get_predictions_for_bet(bet.id)
                    user_pred = next((p for p in predictions if p.user_id == user.id), None)
                    if user_pred:
                        st.success(f"✅ Your prediction: {user_pred.answer}")
    
    # Submit Prediction Tab
    with selected_tab[1]:
        st.subheader("📝 Submit Prediction")
        bets = betting.get_open_bets()
        
        if not bets:
            st.info("No open bets available.")
        else:
            bet_titles = {f"Week {b.week}: {b.title}": b.id for b in bets}
            selected_bet_title = st.selectbox("Select Bet", list(bet_titles.keys()))
            bet_id = bet_titles[selected_bet_title]
            
            answer = st.text_input("Your Answer")
            
            if st.button("Submit Prediction"):
                if answer:
                    success, msg = betting.submit_prediction(user, bet_id, answer)
                    if success:
                        st.success(msg)
                        refresh_user()
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Please enter an answer")
    
    # My Predictions Tab
    with selected_tab[2]:
        st.subheader("📋 My Predictions")
        predictions = betting.get_user_predictions(user)
        
        if not predictions:
            st.info("You haven't made any predictions yet.")
        else:
            for bet, pred in predictions:
                with st.expander(f"Week {bet.week}: {bet.title}"):
                    st.write(f"**Your Answer:** {pred.answer}")
                    st.write(f"**Status:** {bet.status.value}")
                    if bet.status.value == 'resolved' and bet.correct_answer:
                        st.write(f"**Correct Answer:** {bet.correct_answer}")
                    if pred.points_earned is not None:
                        st.success(f"✨ Points Earned: {pred.points_earned} Reedz")
    
    # Leaderboard Tab
    with selected_tab[3]:
        st.subheader("🏆 Leaderboard")
        leaderboard = scoring.get_leaderboard(limit=20)
        
        if leaderboard:
            import pandas as pd
            df = pd.DataFrame(leaderboard)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No leaderboard data yet.")
    
    # Request Admin Tab (for non-admins)
    if not user.is_admin():
        with selected_tab[4]:
            st.subheader("🔒 Request Admin Access")
            st.write("Enter the admin password to become a Commissioner or Treasurer.")
            
            with st.form("admin_request_form"):
                admin_pwd = st.text_input("Admin Password", type="password")
                admin_role = st.selectbox("Select Role", ["Commissioner", "Treasurer"])
                submit_admin = st.form_submit_button("Request Access")
                
                if submit_admin:
                    if admin_pwd == ADMIN_REGISTRATION_PASSWORD:
                        new_role = UserRole.COMMISSIONER if admin_role == "Commissioner" else UserRole.TREASURER
                        success, msg = db.update_user_role(user.id, new_role)
                        if success:
                            st.success(f"✅ Promoted to {admin_role}! Please refresh the page.")
                            refresh_user()
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("❌ Incorrect admin password")


def admin_page():
    """Admin panel"""
    user = st.session_state.user
    
    st.markdown('<div class="main-header"><h1>🔧 Admin Panel</h1></div>', unsafe_allow_html=True)
    
    admin_tabs = st.tabs(["Create Bet", "Close Bet", "Resolve Bet", "User Management"])
    
    # Create Bet
    with admin_tabs[0]:
        st.subheader("➕ Create New Bet")
        with st.form("create_bet_form"):
            title = st.text_input("Bet Title")
            description = st.text_area("Description")
            week = st.number_input("Week Number", min_value=1, value=1)
            answer_type = st.selectbox("Answer Type", ["Numeric", "Text"])
            
            create = st.form_submit_button("Create Bet")
            
            if create:
                if title and description:
                    atype = AnswerType.NUMERIC if answer_type == "Numeric" else AnswerType.TEXT
                    success, msg, bet_id = betting.create_bet(user, title, description, week, atype)
                    if success:
                        st.success(f"{msg} (Bet ID: {bet_id})")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Title and description are required")
    
    # Close Bet
    with admin_tabs[1]:
        st.subheader("🔒 Close Bet")
        open_bets = betting.get_open_bets()
        
        if not open_bets:
            st.info("No open bets to close.")
        else:
            bet_options = {f"Week {b.week}: {b.title}": b.id for b in open_bets}
            selected_bet = st.selectbox("Select Bet to Close", list(bet_options.keys()))
            
            if st.button("Close Bet"):
                bet_id = bet_options[selected_bet]
                success, msg = betting.close_bet(user, bet_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    # Resolve Bet
    with admin_tabs[2]:
        st.subheader("✅ Resolve Bet")
        closed_bets = db.get_bets_by_status(BetStatus.CLOSED)
        
        if not closed_bets:
            st.info("No closed bets to resolve.")
        else:
            bet_options = {f"Week {b.week}: {b.title}": b.id for b in closed_bets}
            selected_bet = st.selectbox("Select Bet to Resolve", list(bet_options.keys()), key="resolve_bet")
            bet_id = bet_options[selected_bet]
            
            # Show bet summary
            summary = betting.get_bet_summary(bet_id)
            if summary:
                st.write(f"**Total Predictions:** {summary['total_predictions']}")
                st.write("**Predictions:**")
                for pred in summary['predictions']:
                    st.write(f"- {pred['username']}: {pred['answer']}")
                
                with st.form("resolve_form"):
                    correct_answer = st.text_input("Enter Correct Answer")
                    resolve = st.form_submit_button("Resolve Bet")
                    
                    if resolve:
                        if correct_answer:
                            success, msg, details = scoring.resolve_bet(user, bet_id, correct_answer)
                            if success:
                                st.success(msg)
                                st.write(f"**Total Reedz Distributed:** {details['total_reedz_distributed']}")
                                refresh_user()
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("Please enter the correct answer")
    
    # User Management
    with admin_tabs[3]:
        st.subheader("👥 User Management")
        
        users = db.get_all_users()
        
        import pandas as pd
        user_data = [{
            'ID': u.id,
            'Username': u.username,
            'Role': u.role.value,
            'Reedz': u.reedz_balance,
            'Active': 'Yes' if u.is_active else 'No'
        } for u in users]
        
        df = pd.DataFrame(user_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        st.markdown("---")
        
        # Promote User
        st.subheader("⬆️ Promote User")
        members = [u for u in users if u.role == UserRole.MEMBER]
        if members:
            member_names = {u.username: u.id for u in members}
            selected_user = st.selectbox("Select Member", list(member_names.keys()))
            new_role = st.selectbox("New Role", ["Commissioner", "Treasurer"])
            
            if st.button("Promote User"):
                user_id = member_names[selected_user]
                role = UserRole.COMMISSIONER if new_role == "Commissioner" else UserRole.TREASURER
                success, msg = auth.promote_user(user, user_id, role)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("No members to promote")
        
        st.markdown("---")
        
        # Adjust Reedz Balance - NEW SECTION
        st.subheader("💰 Adjust Reedz Balance")
        st.write("Manually adjust a user's Reedz balance for dispute resolution.")
        
        all_users = users
        user_names_reedz = {f"{u.username} ({u.reedz_balance} Reedz)": u for u in all_users}
        selected_user_reedz = st.selectbox("Select User", list(user_names_reedz.keys()), key="reedz_user")
        
        target_user = user_names_reedz[selected_user_reedz]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Current Balance:** {target_user.reedz_balance} Reedz")
            adjustment_type = st.radio("Adjustment Type", 
                                      ["Set to specific amount", "Add Reedz", "Subtract Reedz"],
                                      key="adj_type")
        
        with col2:
            if adjustment_type == "Set to specific amount":
                new_balance = st.number_input("New Balance", value=target_user.reedz_balance, step=1)
                if st.button("Set Balance", type="primary"):
                    success, msg = db.set_user_reedz(target_user.id, new_balance)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            elif adjustment_type == "Add Reedz":
                add_amount = st.number_input("Amount to Add", min_value=1, value=1, step=1)
                if st.button("Add Reedz", type="primary"):
                    success, msg = db.update_user_reedz(target_user.id, add_amount)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            else:  # Subtract Reedz
                subtract_amount = st.number_input("Amount to Subtract", min_value=1, value=1, step=1)
                if st.button("Subtract Reedz", type="primary"):
                    success, msg = db.update_user_reedz(target_user.id, -subtract_amount)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        
        st.markdown("---")
        
        # Remove User
        st.subheader("🗑️ Remove User")
        removable_users = [u for u in users if u.id != user.id]
        if removable_users:
            user_names = {u.username: u.id for u in removable_users}
            selected_remove = st.selectbox("Select User to Remove", list(user_names.keys()), key="remove_user")
            
            if st.button("Remove User", type="primary"):
                user_id = user_names[selected_remove]
                success, msg = db.delete_user(user_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


def main():
    """Main application"""
    
    # Sidebar
    with st.sidebar:
        
        
        if st.session_state.authenticated:
            user = st.session_state.user
            st.write(f"Username: **{user.username}**")
            st.write(f"Role: {user.role.value.title()}")
            st.write(f"Reedz: {user.reedz_balance}")
            st.markdown("---")
            
            page = st.radio("Navigation", ["Dashboard", "Admin Panel"] if user.is_admin() else ["Dashboard"])
        else:
            st.info("Please login to continue")
            page = None
    
    # Main content
    if not st.session_state.authenticated:
        login_page()
    else:
        if page == "Dashboard":
            dashboard_page()
        elif page == "Admin Panel":
            admin_page()


if __name__ == "__main__":
    main()
