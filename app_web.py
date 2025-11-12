import streamlit as st
import pandas as pd
from auth import login_user, register_user, hash_password
from supabase_db import SupabaseDatabase
from models import UserRole, BetStatus
from datetime import datetime

st.set_page_config(page_title="Reedz", layout="wide")
db = SupabaseDatabase()

# ==================== SESSION STATE ====================
if "user" not in st.session_state:
    st.session_state.user = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "role" not in st.session_state:
    st.session_state.role = None

# ==================== AUTHENTICATION ====================
def logout():
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.role = None
    st.rerun()

def login_page():
    col1, col2 = st.columns(2)
    with col1:
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            success, message, user_id = login_user(username, password)
            if success:
                user = db.get_user_by_id(user_id)
                st.session_state.user = user
                st.session_state.user_id = user_id
                st.session_state.role = user.role
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(message)
    with col2:
        st.header("Register")
        new_username = st.text_input("Username", key="register_username")
        new_password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        role = st.radio("Register as:", ["Member", "Admin"], horizontal=True, key="register_role")
        selected_role = UserRole.ADMIN if role == "Admin" else UserRole.MEMBER
        if st.button("Register", key="register_button"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message, user_id = register_user(new_username, new_password, selected_role)
                if success:
                    st.success("Registration successful! Please login.")
                else:
                    st.error(message)

def member_page():
    """Member dashboard"""
    st.header("Reedz - Member Dashboard")
    user = db.get_user_by_id(st.session_state.user_id)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Welcome, {user.username}!")
    with col2:
        if st.button("Logout"):
            logout()
    st.metric("Reedz Balance", user.reedz_balance)

    st.subheader("Available Bets")
    open_bets = db.get_bets_by_status(BetStatus.OPEN)
    if not open_bets:
        st.info("No open bets available")
    else:
        bet_table = [{
            "Week": bet.week,
            "Title": bet.title,
            "Description": bet.description,
            "Status": bet.status.value
        } for bet in open_bets]
        st.dataframe(pd.DataFrame(bet_table), use_container_width=True, hide_index=True)

    st.subheader("Leaderboard")
    users = db.get_all_users()
    leaderboard_data = []
    for idx, u in enumerate(users[:10], 1):
        leaderboard_data.append({
            "Rank": idx,
            "Username": u.username,
            "Reedz": u.reedz_balance
        })
    if leaderboard_data:
        st.dataframe(pd.DataFrame(leaderboard_data), use_container_width=True, hide_index=True)
    else:
        st.info("No users on leaderboard")

def admin_page():
    """Admin dashboard - can do both admin and member functions"""
    st.header("Reedz - Admin Dashboard")
    user = db.get_user_by_id(st.session_state.user_id)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Welcome, Admin {user.username}!")
    with col2:
        if st.button("Logout"):
            logout()
    admin_tabs = st.tabs(["Create Bet", "Close Bet", "Resolve Bet", "User Management", "Member Features"])

    with admin_tabs[0]:
        st.subheader("Create New Bet")
        week = st.number_input("Week", min_value=1, step=1)
        title = st.text_input("Bet Title")
        description = st.text_area("Description")
        if st.button("Create Bet"):
            if not title:
                st.error("Title is required")
            else:
                success, message, _ = db.create_bet(week, title, description)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    with admin_tabs[1]:
        st.subheader("Close Bet")
        open_bets = db.get_bets_by_status(BetStatus.OPEN)
        if not open_bets:
            st.info("No open bets")
        else:
            bet_table = [{
                "Week": b.week,
                "Title": b.title,
                "Description": b.description,
                "Status": b.status.value
            } for b in open_bets]
            st.dataframe(pd.DataFrame(bet_table), use_container_width=True, hide_index=True)
            bet_options = {f"Week {b.week}: {b.title}": b.id for b in open_bets}
            selected_bet = st.selectbox("Select bet to close", list(bet_options.keys()))
            if st.button("Close Bet"):
                bet_id = bet_options[selected_bet]
                success, message = db.close_bet(bet_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with admin_tabs[2]:
        st.subheader("Resolve Bet")
        closed_bets = db.get_bets_by_status(BetStatus.CLOSED)
        if not closed_bets:
            st.info("No closed bets")
        else:
            bet_table = [{
                "Week": b.week,
                "Title": b.title,
                "Description": b.description,
                "Status": b.status.value
            } for b in closed_bets]
            st.dataframe(pd.DataFrame(bet_table), use_container_width=True, hide_index=True)
            bet_options = {f"Week {b.week}: {b.title}": b.id for b in closed_bets}
            selected_bet = st.selectbox("Select bet to resolve", list(bet_options.keys()))
            correct_answer = st.radio("Correct answer:", ["YES", "NO", "UNKNOWN"])
            if st.button("Resolve Bet"):
                bet_id = bet_options[selected_bet]
                success, message = db.resolve_bet(bet_id, correct_answer)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with admin_tabs[3]:
        st.subheader("User Management")
        users = db.get_all_users()
        if not users:
            st.info("No active users")
        else:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                st.write("Username")
            with col2:
                st.write("Role")
            with col3:
                st.write("Balance")
            with col4:
                st.write("Set Balance")
            with col5:
                st.write("Promote/Demote")
            with col6:
                st.write("Delete")
            st.divider()
            for u in users:
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    st.write(f"{u.username}")
                with col2:
                    st.write(f"{u.role.value}")
                with col3:
                    st.write(f"{u.reedz_balance}")
                with col4:
                    new_balance = st.number_input(
                        f"Balance for {u.username}", 
                        value=u.reedz_balance, 
                        key=f"balance_{u.id}",
                        min_value=0,
                        label_visibility="collapsed"
                    )
                    if new_balance != u.reedz_balance:
                        difference = new_balance - u.reedz_balance
                        success, msg = db.update_user_reedz(u.id, difference)
                        if success:
                            st.success("✓")
                        else:
                            st.error(f"Error: {msg}")
                with col5:
                    new_role = st.selectbox(
                        f"Role for {u.username}",
                        ["Member", "Admin"],
                        index=0 if u.role == UserRole.MEMBER else 1,
                        key=f"role_{u.id}",
                        label_visibility="collapsed"
                    )
                    selected_new_role = UserRole.ADMIN if new_role == "Admin" else UserRole.MEMBER
                    if selected_new_role != u.role:
                        if st.button(f"Update", key=f"update_role_{u.id}"):
                            success, message = db.update_user_role(u.id, selected_new_role)
                            if success:
                                st.success("✓")
                                st.rerun()
                            else:
                                st.error(message)
                with col6:
                    if st.button("Delete", key=f"del_{u.id}", type="secondary"):
                        st.warning(f"Delete {u.username}?")
                        col_y, col_n = st.columns(2)
                        with col_y:
                            if st.button(f"Yes", key=f"confirm_del_{u.id}"):
                                success, message = db.deactivate_user(u.id)
                                if success:
                                    st.success("Deleted")
                                    st.rerun()
                                else:
                                    st.error(message)
                        with col_n:
                            if st.button("No", key=f"cancel_del_{u.id}"):
                                st.info("Cancelled")
    with admin_tabs[4]:
        st.subheader("Make Predictions (Member Features)")
        st.write("As an admin, you can also participate in betting:")
        open_bets = db.get_bets_by_status(BetStatus.OPEN)
        if not open_bets:
            st.info("No open bets available")
        else:
            bet_table = [{
                "Week": bet.week,
                "Title": bet.title,
                "Description": bet.description,
                "Status": bet.status.value
            } for bet in open_bets]
            st.dataframe(pd.DataFrame(bet_table), use_container_width=True, hide_index=True)
        st.subheader("Leaderboard")
        users = db.get_all_users()
        leaderboard_data = []
        for idx, u in enumerate(users[:10], 1):
            leaderboard_data.append({
                "Rank": idx,
                "Username": u.username,
                "Reedz": u.reedz_balance
            })
        if leaderboard_data:
            st.dataframe(pd.DataFrame(leaderboard_data), use_container_width=True, hide_index=True)

# ==================== MAIN APP ====================
def main():
    if st.session_state.user is None:
        st.title("Reedz")
        login_page()
    else:
        if st.session_state.role == UserRole.ADMIN:
            admin_page()
        else:
            member_page()

if __name__ == "__main__":
    main()
