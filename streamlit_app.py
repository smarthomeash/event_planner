import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Event Master Planner", layout="wide", page_icon="📅")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .stMetric { background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    div.stButton > button:first-child { background-color: #007BFF; color: white; font-weight: bold; border-radius: 8px;}
    .main-header { font-size: 2.5rem; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GOOGLE SHEETS CONNECTION ---
# We wrap this in a try-except to handle the "Sheet Not Found" error gracefully
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ Secrets Error: Please check your .streamlit/secrets.toml file.")
    st.stop()

# Helper: Load Data with Error Handling
def load_data(tab_name, required_columns):
    try:
        df = conn.read(spreadsheet=st.secrets["gsheet_url"], worksheet=tab_name, ttl=0)
        # If sheet is empty/new, return an empty dataframe with correct columns
        if df.empty:
            return pd.DataFrame(columns=required_columns)
        # Ensure all required columns exist (fill missing ones)
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception as e:
        # If the tab doesn't exist, we return None to trigger the Setup Guide
        return None

# Helper: Save Data
def save_data(tab_name, df):
    try:
        conn.update(spreadsheet=st.secrets["gsheet_url"], worksheet=tab_name, data=df)
        st.toast(f"Saved to {tab_name}!", icon="✅")
    except Exception as e:
        st.error(f"Save failed: {e}")

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("📋 Menu")
menu = st.sidebar.radio("Go to:", 
    ["Event", "Budget", "Guests", "Food & Drinks", "Games", "Decoration", "Gallery", "Invitations", "Feedback"]
)

# --- 4. MAIN LOGIC ---

# ---------------------------------------------------------
# 📍 EVENT
# ---------------------------------------------------------
if menu == "Event":
    st.header("📍 Event Details")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Logistics")
        st.date_input("Event Date", value=datetime.date(2026, 2, 28))
        st.time_input("Start Time", value=datetime.time(12, 00))
        st.text_input("Location", "Rocky Island, Balmoral Beach")
        st.text_input("Alternative (Rain)", "Balmoral Rotunda")
        st.text_area("Parking Info", "Paid parking at Bathers Pavilion ($12/hr) or street parking on The Esplanade.")
    with c2:
        st.subheader("Map & Weather")
        st.map(pd.DataFrame({'lat': [-33.8245], 'lon': [151.2505]}))
        st.info("☀️ **Forecast:** Check 3 days prior. Avg temp: 26°C.")

# ---------------------------------------------------------
# 💰 BUDGET
# ---------------------------------------------------------
elif menu == "Budget":
    st.header("💰 Budget Master Tracker")
    
    # 1. LOAD DATA
    df_food = load_data("Food", ["Total"])
    df_decor = load_data("Decor", ["Cost"])
    df_budget = load_data("Budget_Config", ["Category", "Limit", "Manual_Cost"])
    
    if df_food is None or df_budget is None:
        st.error("🚨 Critical Error: Tabs missing. Please create 'Food', 'Decor', and 'Budget_Config' tabs in Google Sheets.")
        st.stop()

    # 2. CALCULATE ACTUALS FROM OTHER TABS
    real_food_cost = df_food['Total'].sum() if not df_food.empty else 0.0
    real_decor_cost = df_decor['Cost'].sum() if not df_decor.empty else 0.0

    # 3. BUDGET CONFIGURATION
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Set Limits")
        st.caption("Edit your budget goals here.")
        
        # Ensure Budget Config has rows. If empty, seed it.
        if df_budget.empty:
            df_budget = pd.DataFrame([
                {"Category": "Food & Drinks", "Limit": 800.0, "Manual_Cost": 0.0},
                {"Category": "Venue", "Limit": 500.0, "Manual_Cost": 0.0},
                {"Category": "Decoration", "Limit": 300.0, "Manual_Cost": 0.0},
                {"Category": "Games", "Limit": 100.0, "Manual_Cost": 0.0},
                {"Category": "Invitations", "Limit": 50.0, "Manual_Cost": 0.0}
            ])
            
        edited_budget = st.data_editor(df_budget, num_rows="dynamic", key="budget_edit")
        if st.button("Save Limits"):
            save_data("Budget_Config", edited_budget)

    with col2:
        st.subheader("Financial Overview")
        
        # Helper to extract limits safely
        def get_limit(cat):
            row = edited_budget[edited_budget['Category'] == cat]
            return float(row['Limit'].iloc[0]) if not row.empty else 0.0
        
        def get_manual(cat):
            row = edited_budget[edited_budget['Category'] == cat]
            return float(row['Manual_Cost'].iloc[0]) if not row.empty else 0.0

        # Progress Bars
        def show_bar(label, current, limit):
            ratio = min(current / limit, 1.0) if limit > 0 else 0
            st.write(f"**{label}** (${current:.2f} / ${limit:.2f})")
            st.progress(ratio)
            if current > limit:
                st.warning(f"Over budget by ${current - limit:.2f}")

        # Display
        show_bar("Food & Drinks (Linked to Tab)", real_food_cost, get_limit("Food & Drinks"))
        show_bar("Decoration (Linked to Tab)", real_decor_cost, get_limit("Decoration"))
        
        # Venue (Manual entry via Budget Config tab)
        venue_cost = get_manual("Venue")
        show_bar("Venue/Parking (Manual Entry)", venue_cost, get_limit("Venue"))

        st.divider()
        
        # Total Logic
        total_limit = edited_budget['Limit'].sum()
        # Sum of linked tabs + manual entries for categories NOT linked
        # (Simplified: We assume Food and Decor are the only linked ones for now)
        total_spent = real_food_cost + real_decor_cost + venue_cost + get_manual("Games") + get_manual("Invitations")
        
        rem = total_limit - total_spent
        st.metric("Total Remaining Budget", f"${rem:.2f}", delta=f"{rem:.2f}")

# ---------------------------------------------------------
# 👥 GUESTS
# ---------------------------------------------------------
elif menu == "Guests":
    st.header("👥 Guest List")
    
    required_cols = ["Family Name", "Adults", "Children", "Ages", "Dietary", "RSVP"]
    df = load_data("Guests", required_cols)
    
    if df is None:
        st.error("Missing 'Guests' tab in Google Sheets.")
        st.stop()

    edited_guests = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("Sync Guests"):
        save_data("Guests", edited_guests)
        
    # Stats
    try:
        adults = pd.to_numeric(edited_guests['Adults'], errors='coerce').fillna(0).sum()
        kids = pd.to_numeric(edited_guests['Children'], errors='coerce').fillna(0).sum()
        st.info(f"**Headcount:** {int(adults)} Adults + {int(kids)} Kids = {int(adults+kids)} Total")
    except:
        pass

# ---------------------------------------------------------
# 🍕 FOOD & DRINKS
# ---------------------------------------------------------
elif menu == "Food & Drinks":
    st.header("🍕 Food & Drinks Tracker")
    st.caption("Total Cost flows automatically to the Budget tab.")
    
    cols = ["Item", "Owner", "Sourcing", "Price", "Quantity", "Total"]
    df = load_data("Food", cols)
    
    if df is None: 
        st.error("Missing 'Food' tab.") 
        st.stop()

    edited_food = st.data_editor(
        df, 
        num_rows="dynamic",
        column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Total": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True
    )
    
    # Calculation Logic
    if st.button("Calculate Totals & Save"):
        # Iterate and calculate if Quantity/Price exist
        for i, row in edited_food.iterrows():
            q = pd.to_numeric(row.get("Quantity", 0), errors='coerce')
            p = pd.to_numeric(row.get("Price", 0), errors='coerce')
            t = pd.to_numeric(row.get("Total", 0), errors='coerce')
            
            # If user entered Qty and Price, but Total is 0/NaN, calculate it
            if q > 0 and p > 0:
                 edited_food.at[i, "Total"] = q * p
        
        save_data("Food", edited_food)

    total_food = pd.to_numeric(edited_food['Total'], errors='coerce').sum()
    st.metric("Total Food Cost", f"${total_food:.2f}")

# ---------------------------------------------------------
# 🎲 GAMES
# ---------------------------------------------------------
elif menu == "Games":
    st.header("🎲 Party Games")
    st.caption("Customizable Game Plan")
    
    cols = ["Game Name", "Rules", "Props Needed", "Winner"]
    df = load_data("Games", cols)
    
    if df is None: st.error("Missing 'Games' tab."); st.stop()
    
    edited_games = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("Save Games"):
        save_data("Games", edited_games)

# ---------------------------------------------------------
# 🎨 DECORATION
# ---------------------------------------------------------
elif menu == "Decoration":
    st.header("🎨 Decoration & Props")
    
    cols = ["Item", "Theme", "Status", "Cost"]
    df = load_data("Decor", cols)
    
    if df is None: st.error("Missing 'Decor' tab."); st.stop()
    
    edited_decor = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "Cost": st.column_config.NumberColumn(format="$%.2f"),
            "Status": st.column_config.SelectboxColumn(options=["To Buy", "Purchased", "Owned"])
        },
        use_container_width=True
    )
    
    if st.button("Save Decor"):
        save_data("Decor", edited_decor)
        
    total_decor = pd.to_numeric(edited_decor['Cost'], errors='coerce').sum()
    st.metric("Total Decor Cost", f"${total_decor:.2f}")

# ---------------------------------------------------------
# 📸 GALLERY & INVITATIONS
# ---------------------------------------------------------
elif menu in ["Gallery", "Invitations"]:
    st.header(f"{menu}")
    st.warning("⚠️ Note: Images uploaded here are temporary (Session Only) due to Google Sheets limitations.")
    
    uploaded = st.file_uploader("Upload Files", accept_multiple_files=True)
    if uploaded:
        cols = st.columns(4)
        for i, f in enumerate(uploaded):
            cols[i%4].image(f, use_container_width=True)

# ---------------------------------------------------------
# 🗣️ FEEDBACK
# ---------------------------------------------------------
elif menu == "Feedback":
    st.header("🗣️ Guest Feedback")
    
    # Load existing feedback to show admins
    df_feed = load_data("Feedback", ["Name", "Rating", "Comments"])
    
    with st.form("feedback_form"):
        name = st.text_input("Name (Optional)")
        rating = st.slider("Rating", 1, 5, 5)
        comments = st.text_area("Comments")
        
        if st.form_submit_button("Submit Feedback"):
            if df_feed is not None:
                new_data = pd.DataFrame([{"Name": name if name else "Anonymous", "Rating": rating, "Comments": comments}])
                updated_df = pd.concat([df_feed, new_data], ignore_index=True)
                save_data("Feedback", updated_df)
            else:
                st.error("Feedback tab missing.")

    if df_feed is not None and not df_feed.empty:
        st.divider()
        st.subheader("Recent Feedback")
        st.dataframe(df_feed)