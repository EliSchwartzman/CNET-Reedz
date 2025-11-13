import streamlit as st
import pandas as pd
from auth import login_user, register_user, hash_password
from supabase_db import SupabaseDatabase
from models import UserRole, BetStatus, AnswerType
from datetime import datetime

st.set_page_config(page_title="Reedz", layout="wide")
db = SupabaseDatabase()

if "user" not in st.session_state:
    st.session_state.user = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "role" not in st.session_state:
    st.session_state.role = None

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

def show_bets_with_prediction(user_id):
    open_bets = db.get_bets_by_status(BetStatus.OPEN)
    if not open_bets:
        st.info("No open bets available")
    else:
        bet_table = []
        for bet in open_bets:
            bet_type = getattr(bet, "answertype", "UNKNOWN")
            status = getattr(bet, "status", "UNKNOWN")
            bet_table.append({
                "Week": getattr(bet, "week", ""),
                "Title": getattr(bet, "title", ""),
                "Description": getattr(bet, "description", ""),
                "Type": bet_type,
                "Status": status
            })
        st.dataframe(pd.DataFrame(bet_table), use_container_width=True, hide_index=True)

        for bet in open_bets:
            existing_prediction = db.get_prediction_by_user_bet(user_id, bet.id)
            bet_type = getattr(bet, "answertype", "UNKNOWN")
            if existing_prediction:
                st.info(f"You predicted: **{existing_prediction.answer}** for {bet.title} (Week {bet.week})")
            else:
                st.write(f"Prediction for {bet.title} (Week {bet.week})")
                if bet_type == AnswerType.NUMERIC.value:
                    answer = st.text_input("Enter your numeric prediction", key=f"bet{bet.id}_numeric")
                elif bet_type == AnswerType.TEXT.value:
                    answer = st.text_input("Enter your text prediction", key=f"bet{bet.id}_text")
                else:
                    answer = st.radio("Your prediction:", ["YES", "NO", "UNKNOWN"], key=f"bet{bet.id}_choice")
                if st.button("Submit Prediction", key=f"submit_{bet.id}"):
                    success, message, _ = db.create_prediction(bet.id, user_id, answer)
                    if success:
                        st.success("Prediction submitted!")
                        st.rerun()
                    else:
                        st.error(message)

def show_leaderboard():
    st.subheader("Leaderboard")
    users = db.get_all_users()
    leaderboard_data = [
        {"Rank": idx, "Username": u.username, "Reedz": u.reedz_balance}
        for idx, u in enumerate(users[:10], 1)
    ]
    if leaderboard_data:
        st.dataframe(pd.DataFrame(leaderboard_data), use_container_width=True, hide_index=True)
    else:
        st.info("No users on leaderboard")

def member_page():
    st.header("🎯 Reedz - Member Dashboard")
    user = db.get_user_by_id(st.session_state.user_id)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Welcome, {user.username}!")
    with col2:
        if st.button("Logout"):
            logout()
    st.metric("Reedz Balance", user.reedz_balance)
    st.subheader("Available Bets")
    show_bets_with_prediction(st.session_state.user_id)
    show_leaderboard()

def admin_page():
    st.header("🔧 Reedz - Admin Dashboard")
    user = db.get_user_by_id(st.session_state.user_id)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Welcome, Admin {user.username}!")
    with col2:
        if st.button("Logout"):
            logout()

    admintabs = st.tabs(["Create Bet", "Close Bet", "Resolve Bet", "User Management", "Member Features"])

    with admintabs[0]:
        st.subheader("Create New Bet")
        week = st.number_input("Week", min_value=1, step=1)
        title = st.text_input("Bet Title")
        description = st.text_area("Description")
        bet_type = st.selectbox("Prediction Type", ["YESNO/UNKNOWN", "Numeric", "Text"])
        if bet_type == "Numeric":
            answertype = AnswerType.NUMERIC.value
        elif bet_type == "Text":
            answertype = AnswerType.TEXT.value
        else:
            answertype = AnswerType.UNKNOWN.value
        if st.button("Create Bet"):
            if not title:
                st.error("Title is required")
            else:
                success, message, _ = db.create_bet(week, title, description, answertype, user.id)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    with admintabs[1]:
        st.subheader("Close Bet")
        open_bets = db.get_bets_by_status(BetStatus.OPEN)
        if open_bets:
            bet_table = []
            bet_options = {}
            for b in open_bets:
                bet_table.append({
                    "Week": b.week,
                    "Title": b.title,
                    "Description": b.description,
                    "Type": getattr(b, "answertype", "UNKNOWN"),
                    "Status": b.status.value
                })
                bet_options[f"Week {b.week}: {b.title}"] = b.id
            st.dataframe(pd.DataFrame(bet_table), use_container_width=True, hide_index=True)
            selected_bet = st.selectbox("Select bet to close", list(bet_options.keys()))
            bet_id = bet_options[selected_bet]
            if st.button("Close Bet"):
                success, message = db.close_bet(bet_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.info("No open bets available")

    with admintabs[2]:
        st.subheader("Resolve Bet")
        closed_bets = db.get_bets_by_status(BetStatus.CLOSED)
        if closed_bets:
            bet_table = []
            bet_options = {}
            for b in closed_bets:
                bet_table.append({
                    "Week": b.week,
                    "Title": b.title,
                    "Description": b.description,
                    "Type": getattr(b, "answertype", "UNKNOWN"),
                    "Status": b.status.value
                })
                bet_options[f"Week {b.week}: {b.title}"] = b.id
            st.dataframe(pd.DataFrame(bet_table), use_container_width=True, hide_index=True)
            selected_bet = st.selectbox("Select bet to resolve", list(bet_options.keys()))
            bet = db.get_bet_by_id(bet_options[selected_bet])
            if bet.answertype == AnswerType.NUMERIC.value:
                correct_answer = st.text_input("Correct numeric answer")
            elif bet.answertype == AnswerType.TEXT.value:
                correct_answer = st.text_input("Correct text answer")
            else:
                correct_answer = st.radio("Correct answer:", ["YES", "NO", "UNKNOWN"])
            if st.button("Resolve Bet"):
                success, message = db.resolve_bet(bet.id, correct_answer)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.info("No closed bets available")

    with admintabs[3]:
        st.subheader("User Management")
        users = db.get_all_users()
        if not users:
            st.info("No active users")
        else:
            header = pd.DataFrame([{
                "Username": "Username",
                "Role": "Role",
                "Balance": "Balance",
                "Promote/Demote": "Promote/Demote",
                "Delete": "Delete"
            }])
            st.dataframe(header, use_container_width=True, hide_index=True)
            for u in users:
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    st.write(u.username)
                with col2:
                    st.write(u.role.value)
                with col3:
                    st.write(u.reedz_balance)
                with col4:
                    new_role = st.selectbox(f"Role for {u.username}", ["Member", "Admin"], 
                                           index=0 if u.role == UserRole.MEMBER else 1,
                                           key=f"role_{u.id}", label_visibility="collapsed")
                    selected_new_role = UserRole.ADMIN if new_role == "Admin" else UserRole.MEMBER
                    if selected_new_role != u.role:
                        if st.button("Update", key=f"update_role_{u.id}"):
                            success, message = db.update_user_role(u.id, selected_new_role)
                            if success:
                                st.success("Role updated!")
                                st.rerun()
                            else:
                                st.error(message)
                with col5:
                    new_balance = st.number_input(f"Balance for {u.username}", value=u.reedz_balance, 
                                                 key=f"balance_{u.id}", min_value=0, label_visibility="collapsed")
                    if new_balance != u.reedz_balance:
                        difference = new_balance - u.reedz_balance
                        success, msg = db.update_user_reedz(u.id, difference)
                        if success:
                            st.success("Balance updated")
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")
                with col6:
                    if st.button("Delete", key=f"del_{u.id}"):
                        st.warning(f"Delete {u.username}?")
                        col_y, col_n = st.columns(2)
                        with col_y:
                            if st.button("Yes", key=f"confirm_del_{u.id}"):
                                success, message = db.deactivate_user(u.id)
                                if success:
                                    st.success("Deleted")
                                    st.rerun()
                                else:
                                    st.error(message)
                        with col_n:
                            if st.button("No", key=f"cancel_del_{u.id}"):
                                st.info("Cancelled")

    with admintabs[4]:
        st.subheader("Member Features (Admin)")
        st.write("As an admin, you can also participate in betting:")
        show_bets_with_prediction(st.session_state.user_id)
        show_leaderboard()

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
