import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Event Master (Cloud)", layout="wide", page_icon="☁️")

# Custom CSS
st.markdown("""
    <style>
    .stMetric { background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    div.stButton > button:first-child { background-color: #007BFF; color: white; font-weight: bold; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECT TO GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("⚠️ Connection Error: Please ensure your .streamlit/secrets.toml file contains the 'gsheet_url'.")
    st.stop()

# Helper function to load data without caching (so we see updates instantly)
def load_data(tab_name):
    return conn.read(spreadsheet=st.secrets["gsheet_url"], worksheet=tab_name, ttl=0)

# Helper function to save data
def save_data(tab_name, data):
    conn.update(spreadsheet=st.secrets["gsheet_url"], worksheet=tab_name, data=data)
    st.toast(f"Saved to {tab_name}!", icon="✅")

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("📋 Cloud Planner")
menu = st.sidebar.radio("Go to:", 
    ["Event", "Budget", "Guests", "Food & Drinks", "Games", "Decoration", "Gallery", "Invitations", "Feedback"]
)

# --- 4. PAGE LOGIC ---

# ==========================
# 📍 EVENT SECTION (Static Info)
# ==========================
if menu == "Event":
    st.header("📍 Event Details")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Logistics")
        st.info(f"**Date:** Feb 28, 2026 @ 12:00 PM")
        st.write("**Primary Location:** Rocky Island, Balmoral Beach")
        st.write("**Rain Plan:** Balmoral Rotunda")
        st.write("**Parking:** Bathers Pavilion ($12/hr)")
    with c2:
        st.subheader("Map")
        st.map(pd.DataFrame({'lat': [-33.8245], 'lon': [151.2505]}))

# ==========================
# 💰 BUDGET SECTION (The Brain)
# ==========================
elif menu == "Budget":
    st.header("💰 Budget Master Tracker")
    
    # 1. Load Live Data from other tabs
    try:
        df_food = load_data("Food")
        df_decor = load_data("Decor")
        df_limits = load_data("Budget_Config") # Stores your targets
    except:
        st.error("Error loading budget data. Check Sheet tabs.")
        st.stop()

    # Calculate Actuals from tabs
    real_food_cost = df_food['Total'].sum() if not df_food.empty else 0
    real_decor_cost = df_decor['Cost'].sum() if not df_decor.empty else 0
    
    # Get Targets/Manual Costs from Budget_Config Tab
    # Structure: Category | Limit | Actual_Manual
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Set Limits & Manual Costs")
        edited_limits = st.data_editor(df_limits, num_rows="dynamic", key="budget_editor")
        if st.button("Save Budget Config"):
            save_data("Budget_Config", edited_limits)

    with col2:
        st.subheader("Financial Overview")
        
        # Extract limits/manuals safely
        def get_val(cat, col):
            row = edited_limits[edited_limits['Category'] == cat]
            return float(row[col].iloc[0]) if not row.empty else 0.0

        limit_food = get_val("Food", "Limit")
        limit_decor = get_val("Decor", "Limit")
        limit_venue = get_val("Venue", "Limit")
        actual_venue = get_val("Venue", "Actual_Manual") # Manual entry for venue cost

        # Progress Bars
        def show_bar(label, current, limit):
            ratio = min(current / limit, 1.0) if limit > 0 else 0
            st.write(f"**{label}** (${current:.2f} / ${limit:.2f})")
            st.progress(ratio)

        show_bar("Food & Drinks (Linked)", real_food_cost, limit_food)
        show_bar("Decoration (Linked)", real_decor_cost, limit_decor)
        show_bar("Venue (Manual)", actual_venue, limit_venue)

        st.divider()
        total_spent = real_food_cost + real_decor_cost + actual_venue
        total_limit = limit_food + limit_decor + limit_venue
        rem = total_limit - total_spent
        
        st.metric("Total Remaining Budget", f"${rem:.2f}", delta=f"{rem:.2f}")

# ==========================
# 👥 GUESTS SECTION (Persistent)
# ==========================
elif menu == "Guests":
    st.header("👥 Guest Management")
    
    # Load from Cloud
    df_guests = load_data("Guests")
    
    # Edit
    edited_guests = st.data_editor(
        df_guests,
        num_rows="dynamic",
        use_container_width=True
    )
    
    # Save Button
    if st.button("Sync Guests to Cloud"):
        save_data("Guests", edited_guests)
    
    # Stats
    try:
        total = edited_guests["Adults"].sum() + edited_guests["Children"].sum()
        st.info(f"Total Headcount: {total}")
    except:
        st.warning("Enter guest numbers to see totals.")

# ==========================
# 🍕 FOOD & DRINKS (Persistent)
# ==========================
elif menu == "Food & Drinks":
    st.header("🍕 Food & Drinks Logistics")
    
    # Load
    df_food = load_data("Food")
    
    # Edit
    edited_food = st.data_editor(
        df_food,
        num_rows="dynamic",
        column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Total": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True
    )
    
    # Logic: Auto-calc Total if Qty & Price exist
    # Note: We do this calc in Python before saving to ensure data integrity
    if st.button("Calculate Totals & Save"):
        for index, row in edited_food.iterrows():
            if row["Quantity"] > 0 and row["Price"] > 0:
                # Only update if user didn't enter a specific bulk total
                # Use a small threshold or logic to check if Total is missing
                 edited_food.at[index, "Total"] = row["Quantity"] * row["Price"]
        
        save_data("Food", edited_food)
        st.success("Calculated and Saved!")

    total_cost = edited_food["Total"].sum()
    st.metric("Total Food Cost", f"${total_cost:.2f}")

# ==========================
# 🎨 DECORATION (Persistent)
# ==========================
elif menu == "Decoration":
    st.header("🎨 Decoration & Themes")
    
    df_decor = load_data("Decor")
    
    edited_decor = st.data_editor(
        df_decor,
        num_rows="dynamic",
        column_config={
            "Cost": st.column_config.NumberColumn(format="$%.2f"),
            "Status": st.column_config.SelectboxColumn(options=["To Buy", "Purchased", "Owned"])
        },
        use_container_width=True
    )
    
    if st.button("Save Decor Updates"):
        save_data("Decor", edited_decor)

    st.metric("Total Decor Cost", f"${edited_decor['Cost'].sum():.2f}")

# ==========================
# 🎲 GAMES (Static for now)
# ==========================
elif menu == "Games":
    st.header("🎲 Party Games")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Decibel Meter")
        st.write("Who has the loudest laugh?")
        st.subheader("2. Yoga Pose-Off")
        st.write("Last person standing in Tree Pose.")
    with c2:
        st.subheader("3. Shark Net Volleyball")
        st.write("Volleyball inside the swimming enclosure.")
        st.subheader("4. Pass the Parcel")
        st.write("Classic beach edition.")

# ==========================
# 📸 GALLERY & INVITATIONS
# ==========================
elif menu in ["Gallery", "Invitations"]:
    st.header(f"{menu}")
    st.warning("⚠️ Note: File uploads in this version are temporary (Session only).")
    st.info("For permanent photo storage, we would need to connect a Google Drive API or AWS S3 bucket, as Google Sheets cannot store images efficiently.")
    
    uploaded = st.file_uploader("Upload Files", accept_multiple_files=True)
    if uploaded:
        cols = st.columns(4)
        for i, f in enumerate(uploaded):
            cols[i%4].image(f, use_container_width=True)

# ==========================
# 🗣️ FEEDBACK (Persistent)
# ==========================
elif menu == "Feedback":
    st.header("🗣️ Guest Feedback")
    
    with st.form("feedback_form"):
        name = st.text_input("Name")
        rating = st.slider("Rating", 1, 5, 5)
        comments = st.text_area("Comments")
        if st.form_submit_button("Submit"):
            # Load current feedback, append new row, save back
            try:
                current_feedback = load_data("Feedback")
                new_entry = pd.DataFrame([{"Name": name, "Rating": rating, "Comments": comments}])
                updated_feedback = pd.concat([current_feedback, new_entry], ignore_index=True)
                save_data("Feedback", updated_feedback)
            except:
                # If sheet is empty/new
                new_entry = pd.DataFrame([{"Name": name, "Rating": rating, "Comments": comments}])
                save_data("Feedback", new_entry)