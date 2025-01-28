import streamlit as st
import bcrypt
import sqlite3
import random
import pandas as pd
from datetime import datetime

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )''')
    conn.commit()
    c.execute('''CREATE TABLE IF NOT EXISTS subtraction_practice (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    question TEXT,
                    user_answer INTEGER,
                    correct_answer INTEGER,
                    is_correct BOOLEAN,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(username) REFERENCES users(username)
                )''')
    conn.commit()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    username TEXT,
                    item TEXT,
                    FOREIGN KEY(username) REFERENCES users(username)
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

def insert_record(username, question, user_answer, correct_answer, is_correct):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO subtraction_practice (username, question, user_answer, correct_answer, is_correct, date) VALUES (?, ?, ?, ?, ?, ?)",
        (username, question, user_answer, correct_answer, is_correct, datetime.now())
    )
    conn.commit()
    conn.close()

def add_to_inventory(username, item):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO inventory (username, item) VALUES (?, ?)", (username, item))
    conn.commit()
    conn.close()

def get_inventory(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT item FROM inventory WHERE username = ?", (username,))
    items = c.fetchall()
    conn.close()
    return [item[0] for item in items]

def clear_inventory(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM inventory WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def generate_question(previous_questions):
    while True:
        num1 = random.randint(9, 18)
        num2 = random.randint(5, 12)
        if num1 < num2:  # Ensure no negative results
            num1, num2 = num2, num1
        question = (num1, num2)
        if question not in previous_questions:
            previous_questions.add(question)
            return question

# Load items CSV
def load_items():
    url = "https://raw.githubusercontent.com/mikealynch/streamlit-portal-demo/refs/heads/main/items.csv"
    items_df = pd.read_csv(url)
    return items_df

# Initialize database
init_db()

# Session state variables
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
if "correct_count" not in st.session_state:
    st.session_state.correct_count = 0
if "question" not in st.session_state:
    st.session_state.previous_questions = set()
    st.session_state.question = generate_question(st.session_state.previous_questions)
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "rewardItem" not in st.session_state:
    st.session_state.rewardItem = ""    
if "reward" not in st.session_state:
    st.session_state.reward = False    
if "celebration" not in st.session_state:
    st.session_state.celebration = False  # Boolean flag to control image display
if "disappointment" not in st.session_state:
    st.session_state.disappointment = False  # Boolean flag to control image display
if "show_next" not in st.session_state:
    st.session_state.show_next = False
if "user_answer" not in st.session_state:
    st.session_state.user_answer = None

items_df = load_items()

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
            st.success("Login successful! Redirecting...")
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
            else:
                st.error("Username already exists. Please choose a different one.")
        else:
            st.warning("Please fill out all fields.")

def members_only_page():
    if st.session_state["logged_in"]:
        st.title(f"Welcome, {st.session_state['username']}!")
        st.success("You have accessed the members-only page.")

        # Math game logic
        st.title("Math Practice: Subtraction Table")

        # Display the question
        num1, num2 = st.session_state.question

        if not st.session_state.show_next:
            # Input form for the answer
            with st.form("answer_form", clear_on_submit=True):
                st.markdown(f"<h2>What is {num1} - {num2}?</h2>", unsafe_allow_html=True)
                user_answer = st.number_input("Your Answer:", step=1, format="%d", key="user_answer")
                submit_button = st.form_submit_button("Submit")

                if submit_button:
                    correct_answer = num1 - num2
                    is_correct = user_answer == correct_answer

                    # Provide feedback
                    if is_correct:
                        st.session_state.feedback = "Correct! Well done!"
                        st.session_state.correct_count += 1
                        st.session_state.celebration = True  # Enable image display for correct answers
                        st.session_state.disappointment = False
                        st.session_state.reward = False
                        
                        # Check if eligible for an item
                        if st.session_state.correct_count % 3 == 0:
                            st.session_state.reward = True
                            random_row = items_df.sample().iloc[0]
                            random_title = random_row["Title"]
                            random_url = random_row["URL"]
                            hyperlinked_title = f"<a href='{random_url}' target='_blank'>{random_title}</a>"
                            add_to_inventory(st.session_state["username"], random_title)
                            st.session_state.rewardItem = random_title

                            

                    else:
                        st.session_state.feedback = f"Incorrect. The correct answer is {correct_answer}."
                        st.session_state.celebration = False  # Disable image for incorrect answers
                        st.session_state.disappointment = True
                        st.session_state.reward = False

                    # Save to database
                    insert_record(st.session_state["username"], f"{num1} - {num2}", user_answer, correct_answer, is_correct)
                    st.session_state.show_next = True  # Toggle to show the next question button
                    st.rerun()  # Force UI refresh

        # Show feedback if available
        if st.session_state.feedback:
            st.markdown(f"<h3>{st.session_state.feedback}</h3>", unsafe_allow_html=True)

         # Show celebration image if the user answered correctly
        if st.session_state.reward:
            st.success(f"You earned a new item: {st.session_state.rewardItem}")

            # Show celebration image if the user answered correctly
        if st.session_state.celebration:
            st.image(
                "https://github.com/mikealynch/math-pals/raw/main/squishmallows.gif",
                caption="Great job!",
                use_container_width=True
            )

        # Show disappointment image if the user answered incorrectly
        if st.session_state.disappointment:
            st.image(
                "https://raw.githubusercontent.com/mikealynch/math-pals/refs/heads/main/dis_pika.jpg",
                caption="NOPE!",
                use_container_width=True
            )

        # Show "Next Question" button
        if st.session_state.show_next:
            if st.button("Next Question"):
                # Generate a new question, reset the flow, and clear the user input
                st.session_state.question = generate_question(st.session_state.previous_questions)
                st.session_state.feedback = ""
                st.session_state.celebration = False
                st.session_state.disappointment = False
                st.session_state.show_next = False
                st.session_state.user_answer = None  # Reset user answer
                st.rerun()  # Force the app to rerun

        # Display progress
        st.header(f"Correct answers: {st.session_state.correct_count}/28")

    else:
        st.warning("Access denied. Please log in.")

def inventory_page():
    if st.session_state["logged_in"]:
        st.title("Your Inventory")
        inventory = get_inventory(st.session_state["username"])
        if inventory:
            st.write("Here are your items:")
            for item in inventory:
                item_row = items_df[items_df['Title'] == item]
                if not item_row.empty:
                    item_url = item_row.iloc[0]['URL']
                    st.markdown(f"- [**{item}**]({item_url})", unsafe_allow_html=True)
        else:
            st.write("Your inventory is empty. Keep playing to earn items!")

        # Clear inventory button
        if st.button("Clear Inventory"):
            clear_inventory(st.session_state["username"])
            st.success("Your inventory has been cleared.")
    else:
        st.warning("Access denied. Please log in.")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", options=["Login", "Register", "Members Only", "Inventory"])

if page == "Login":
    login_page()
elif page == "Register":
    register_page()
elif page == "Members Only":
    members_only_page()
elif page == "Inventory":
    inventory_page()

# Redirect to appropriate page if logged in
if st.session_state["logged_in"] and page != "Members Only":
    st.sidebar.info("You are logged in. Access the Members Only page.")
