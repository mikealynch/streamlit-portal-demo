import streamlit as st
import bcrypt
import sqlite3

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

def add_user(username, hashed_password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:  # Username already exists
        conn.close()
        return False

def validate_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        stored_password = result[0]
        return bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8"))
    return False

# Initialize database
init_db()

# Session state variables
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

# Page routing logic
def login_page():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Login")

    if submit_login:
        if validate_user(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            members_only_page()
        else:
            st.error("Invalid username or password. Please try again.")

def register_page():
    st.title("Register")
    with st.form("registration_form"):
        username = st.text_input("Enter a username")
        password = st.text_input("Enter a password", type="password")
        submit_register = st.form_submit_button("Register")

    if submit_register:
        if username and password:
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            if add_user(username, hashed_password):
                st.success("User registered successfully! Please log in.")
                login_page()
            else:
                st.error("Username already exists. Please choose a different one.")
        else:
            st.warning("Please fill out all fields.")

def members_only_page():
    if st.session_state["logged_in"]:
        st.title(f"Welcome, {st.session_state['username']}!")
        st.success("You have accessed the members-only page.")
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            login_page()
    else:
        st.warning("Access denied. Please log in.")
        login_page()

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", options=["Login", "Register", "Members Only"])

if page == "Login":
    login_page()
elif page == "Register":
    register_page()
elif page == "Members Only":
    members_only_page()
