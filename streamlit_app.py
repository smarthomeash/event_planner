import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime
from fpdf import FPDF

# --- 1. GLOBAL CONFIGURATION ---
# (Generic variables pre-filled for your Balmoral 40th)
EVENT_NAME = "40th Birthday Bash"
LOCATION = "Balmoral Beach - Rocky Island"
BACKUP_LOC = "Balmoral Rotunda"
COORDS = {"lat": -33.8245, "lon": 151.2505}
BUDGET_CAP = 2000.0

st.set_page_config(page_title=EVENT_NAME, layout="wide", page_icon="🧘‍♀️")

# --- 2. MOBILE CSS OPTIMIZATION ---
st.markdown("""
    <style>
    /* Bigger buttons for touch screens */
    div.stButton > button:first-child { 
        height: 3.5em; width: 100%; border-radius: 12px; font-weight: bold; background-color: #007BFF; color: white; 
    }
    /* Clean metrics boxes */
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    /* Planner Note Styling */
    .note-box { padding: 10px; border-left: 5px solid #ff9800; background-color: #fff3e0; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION (Admin vs Guest) ---
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
            st.error("Invalid Password.")

if not st.session_state.access:
    login()
    st.stop()

# --- 4. DATA CONNECTION ---
# Connects to your Google Sheet. Requires 'gsheet_url' in st.secrets
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = st.secrets["gsheet_url"]

# --- 5. NAVIGATION MENU ---
st.sidebar.title(f"🎈 {EVENT_NAME}")
st.sidebar.caption(f"Role: {st.session_state.access.upper()}")

if st.session_state.access == "admin":
    menu = [
        "📍 Dashboard & Map",
        "👥 Guests & Pizza Calc", 
        "💰 Budget & Tasks", 
        "🎭 Theme & Props", 
        "🎲 Games & Activities",
        "📝 Planner Chat",
        "📸 Gallery",
        "📦 Export Archive"
    ]
else:
    menu = [
         "📍 Dashboard & Map",
        "👥 Guests & Pizza Calc", 
        "💰 Budget & Tasks", 
        "🎭 Theme & Props", 
        "🎲 Games & Activities",
        "📝 Planner Chat",
        "📸 Gallery",
        "📦 Export Archive"

        # "📍 Event Info", 
        # "🍕 Menu & Logistics", 
        # "🎲 Games & Fun", 
        # "📸 Gallery"
    ]

choice = st.sidebar.radio("Navigate", menu)

# --- 6. PAGE LOGIC (VALIDATED) ---

# --- PAGE: DASHBOARD ---
if choice in ["📍 Dashboard & Map", "📍 Event Info"]:
    st.header("📍 Live Event Status")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.metric("Date", "Feb 28, 2026")
        st.metric("Venue", "Rocky Island")
        st.info(f"**☔ Rain Plan:** If weather turns, pivot immediately to **{BACKUP_LOC}**.")
        st.warning("⚠️ **Shark Alert:** Swimming allowed ONLY in the netted area.")
    with c2:
        # Balmoral Map
        st.map(pd.DataFrame([COORDS]))

# --- PAGE: GUESTS & PIZZA ---
elif choice in ["👥 Guests & Pizza Calc", "🍕 Menu & Logistics"]:
    st.header("👥 Guest Management & Menu")
    
    # 1. Load Data
    try:
        df_guests = conn.read(spreadsheet=SHEET_URL, worksheet="Guests", ttl=0)
    except:
        st.error("Sheet Error: Check that your Google Sheet has a 'Guests' tab.")
        st.stop()
    
    # 2. Admin Editing vs Guest Viewing
    if st.session_state.access == "admin":
        st.subheader("RSVP Control")
        edited_df = st.data_editor(df_guests, num_rows="dynamic")
        if st.button("Sync Changes to Google Sheet"):
            conn.update(spreadsheet=SHEET_URL, data=edited_df)
            st.success("Synced!")
    else:
        st.subheader("Who is coming?")
        st.dataframe(df_guests[["Name", "Status"]])

    # 3. The Pizza Calculator (3 slices rule)
    st.divider()
    st.subheader("🍕 Catering Logic")
    confirmed_count = len(df_guests[df_guests['Status'].astype(str).str.lower() == 'confirmed'])
    pizzas_needed = -((confirmed_count * 3) // -8) # Ceiling division logic
    
    col_a, col_b = st.columns(2)
    col_a.metric("Confirmed Humans", confirmed_count)
    col_b.metric("Pizza Boxes (Large)", f"{pizzas_needed} Boxes")
    
    if st.session_state.access == "guest":
        st.write("**Menu:** Gourmet Woodfired Pizzas, Asian Salad Bowls, Branded Water.")

# --- PAGE: BUDGET & TASKS (Admin Only) ---
elif choice == "💰 Budget & Tasks":
    st.header("📊 Planner Control Room")
    t1, t2 = st.tabs(["Budget Tracker", "2-Person Checklist"])
    
    with t1:
        spent = st.number_input("Total Spent So Far ($)", value=850.0)
        prog = min(spent / BUDGET_CAP, 1.0)
        st.progress(prog)
        st.write(f"**Remaining:** ${BUDGET_CAP - spent}")
        if spent > BUDGET_CAP:
            st.error("Over Budget!")
            
    with t2:
        st.write("### Setup Checklist (10:00 AM Start)")
        st.checkbox("Secure Spot: Rocky Island / Rotunda")
        st.checkbox("Pickup: '40' Balloons from Born to Party")
        st.checkbox("Decor: Place Yoga Mats & Swim Rings")
        st.checkbox("Branding: Apply **icare** & **Suncorp** labels to water")
        st.checkbox("Safety: Check First Aid & Sunscreen")

# --- PAGE: THEME & PROPS ---
elif choice == "🎭 Theme & Props":
    st.header("✨ Theme: 'Naari Shakti' (Women Power)")
    st.markdown("""
    **The Vibe:** Empowered, Relaxed, and "Talkative".
    
    **Essential Prop Checklist:**
    - [ ] **The Instapot:** Centerpiece (represents "Talkative Girls")
    - [ ] **Book 1:** *Naari Shakti*
    - [ ] **Book 2:** *Multitasking 101*
    - [ ] **Book 3:** *Scriptures*
    - [ ] **Knitting Kit:** Pink yarn for the Left Chair
    """)

# --- PAGE: GAMES ---
elif choice in ["🎲 Games & Activities", "🎲 Games & Fun"]:
    st.header("🎮 Beach Games Tracker")
    
    st.subheader("1. Decibel Meter Challenge 📢")
    st.write("Objective: Who can laugh or talk the loudest?")
    leader = st.text_input("Current Leader Name & Score", "Birthday Girls (105 dB)")
    
    st.subheader("2. Yoga Pose-Off 🧘‍♀️")
    st.write("Objective: Last person standing in Tree Pose on the sand.")
    
    st.subheader("3. Shark-Net Volleyball 🏐")
    st.write("Keep the beach balls inside the swimming enclosure.")

# --- PAGE: CHAT (Admin Only) ---
elif choice == "📝 Planner Chat":
    st.header("💬 Internal Thread")
    st.info("Use this to communicate between the Rotunda and the Car Park.")
    
    # Simple session-state chat (resets on reload, use Sheet for permanent)
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []
        
    msg = st.chat_input("Post update...")
    if msg:
        ts = datetime.datetime.now().strftime("%H:%M")
        st.session_state.chat_log.append(f"[{ts}] {msg}")
        
    for log in reversed(st.session_state.chat_log):
        st.markdown(f"<div class='note-box'>{log}</div>", unsafe_allow_html=True)

# --- PAGE: GALLERY ---
elif choice == "📸 Gallery":
    st.header("📸 Photo Vault")
    st.write("Upload Invitations, Menus, or Party Pics.")
    uploaded = st.file_uploader("Choose files", accept_multiple_files=True)
    if uploaded:
        cols = st.columns(3)
        for i, file in enumerate(uploaded):
            cols[i % 3].image(file, use_container_width=True)

# --- PAGE: ARCHIVE (Admin Only) ---
elif choice == "📦 Export Archive":
    st.header("📦 Generate Memento")
    st.write("Click below to download a PDF summary of the event.")
    
    if st.button("Generate PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=15)
        pdf.cell(200, 10, txt=f"Archive: {EVENT_NAME}", ln=1, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Date: Feb 28, 2026 | Loc: {LOCATION}", ln=1, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt="This document certifies the successful completion", ln=1)
        pdf.cell(200, 10, txt="of the double 40th birthday bash!", ln=1)
        
        # Output logic
        html = pdf.output(dest='S').encode('latin-1')
        st.download_button("Download PDF", data=html, file_name="Event_Archive.pdf")

# --- SIDEBAR EXTRAS ---
with st.sidebar:
    st.divider()
    if st.button("Log Out"):
        st.session_state.access = None
        st.rerun()
    st.caption("v2.5 | Collaborative Mode Active")