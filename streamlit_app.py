import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# --- 1. GLOBAL CONFIGURATION (GENERIC) ---
EVENT_NAME = "40th Birthday Bash"
LOCATION = "Balmoral Beach - Rocky Island"
COORDS = {"lat": -33.8245, "lon": 151.2505}
BUDGET_LIMIT = 2000

# --- 2. PAGE SETUP & MOBILE STYLING ---
st.set_page_config(page_title=EVENT_NAME, layout="wide", page_icon="🌊")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eee; }
    div.stButton > button:first-child { 
        height: 3em; width: 100%; border-radius: 10px; font-weight: bold; background-color: #007BFF; color: white;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DUAL-ACCESS SECURITY ---
if "access" not in st.session_state:
    st.session_state.access = None

def login():
    st.title(f"🔐 {EVENT_NAME}")
    pwd = st.text_input("Enter Access Code", type="password")
    if st.button("Log In"):
        if pwd == st.secrets["admin_password"]:
            st.session_state.access = "admin"
            st.rerun()
        elif pwd == st.secrets["guest_password"]:
            st.session_state.access = "guest"
            st.rerun()
        else:
            st.error("Invalid Code.")

if not st.session_state.access:
    login()
    st.stop()

# --- 4. DATA CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
url = st.secrets["gsheet_url"]

# --- 5. NAVIGATION ---
st.sidebar.title(f"🎈 {EVENT_NAME}")
if st.session_state.access == "admin":
    menu = ["📍 Overview", "👥 Guest List", "💰 Budget & Tasks", "🍕 Catering Math", "📝 Planner Chat", "🎲 Theme & Games", "📸 Gallery"]
else:
    menu = ["📍 Overview", "🍕 Menu & Games", "📸 Gallery"]

choice = st.sidebar.radio("Menu", menu)

# --- 6. PAGE LOGIC ---

# PAGE: OVERVIEW & MAP
if choice in ["📍 Overview"]:
    st.header("Event Logistics")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Date", "Feb 28, 2026")
        st.metric("Venue", "Rocky Island")
        st.info(f"**Rain Plan:** Meet at the Balmoral Rotunda.")
    with c2:
        st.map(pd.DataFrame([COORDS]))

# PAGE: GUEST LIST (COLLABORATIVE)
elif choice == "👥 Guest List":
    st.header("Guest Management")
    df = conn.read(spreadsheet=url, worksheet="Guests", ttl=0)
    
    if st.session_state.access == "admin":
        edited_df = st.data_editor(df, num_rows="dynamic")
        if st.button("Save & Sync to Google Sheets"):
            conn.update(spreadsheet=url, data=edited_df)
            st.success("Synced!")
    else:
        st.dataframe(df[["Name", "Status"]])

# PAGE: CATERING MATH
elif choice in ["🍕 Catering Math", "🍕 Menu & Games"]:
    st.header("Pizza & Menu")
    st.write("**Menu:** Gourmet Woodfired Pizzas, Asian Salad Bowls, Custom 'icare' Water.")
    
    # Collaborative Pizza Logic
    df_guests = conn.read(spreadsheet=url, worksheet="Guests", ttl=0)
    confirmed = len(df_guests[df_guests['Status'] == 'Confirmed'])
    st.metric("Confirmed Guests", confirmed)
    
    pizzas = -((confirmed * 3) // -8) # 3 slices per person
    st.metric("Total Large Pizzas Needed", f"{pizzas} Boxes")

# PAGE: THEME & GAMES
elif choice in ["🎲 Theme & Games", "🍕 Menu & Games"]:
    st.header("Theme: Naari Shakti & Chitchat")
    st.write("**Core Props:** Instapot, Pink Knitting Kit, 3 Empowerment Books.")
    st.divider()
    st.subheader("Interactive Games")
    st.markdown("""
    - **Decibel Meter:** Record the loudest laughter! 
    - **Yoga Pose-Off:** Tree Pose competition on the sand.
    - **Shark-Net Swim:** Volleyball inside the netted area.
    """)

# PAGE: BUDGET & TASKS
elif choice == "💰 Budget & Tasks":
    st.header("Finances & Checklist")
    tab1, tab2 = st.tabs(["Budgeting", "Tasks"])
    with tab1:
        spent = st.number_input("Total Spent ($)", value=850)
        st.progress(spent / BUDGET_LIMIT)
        st.write(f"Remaining: ${BUDGET_LIMIT - spent}")
    with tab2:
        st.checkbox("Secure Rotunda (10:00 AM)")
        st.checkbox("Label icare/Suncorp Bottles")

# PAGE: PLANNER CHAT
elif choice == "📝 Planner Chat":
    st.header("Internal Planner Notes")
    msg = st.chat_input("Post a message for your co-planner...")
    if msg:
        st.write(f"**[{datetime.datetime.now().strftime('%H:%M')}]**: {msg}")
    st.info("Tip: Use this to track parking or pizza delivery status.")

# PAGE: GALLERY
elif choice == "📸 Gallery":
    st.header("Photo Memories")
    files = st.file_uploader("Upload photos from your phone", accept_multiple_files=True)
    if files:
        cols = st.columns(2)
        for i, f in enumerate(files):
            cols[i % 2].image(f, use_container_width=True)

if st.sidebar.button("Log Out"):
    st.session_state.access = None
    st.rerun()