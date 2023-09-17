import streamlit as st
import datetime as dt
import time
from db_manager import DBManager 
from utils import get_reservable_sites

if "db" not in st.session_state.keys():
    db = DBManager()
    st.session_state["db"] = db

if "authenticated" not in st.session_state.keys():
    st.session_state["authenticated"] = False 

st.sidebar.title("Reservation System")
refresh = st.sidebar.button("Refresh Data")
if refresh:
    st.session_state["db"] = DBManager()
st.sidebar.header("Administrators Login")

if not st.session_state['authenticated']:
    user = st.sidebar.text_input("User")
    password = st.sidebar.text_input("Password")
    login = st.sidebar.button("Login")
    if login:
        if user.lower() == " " and password.lower() == " ":
            st.session_state['authenticated'] = True
            st.experimental_rerun()
        else:
            st.sidebar.error("Incorrect credentials.")
else:
    st.sidebar.success("Logged in as administrator.") 

if "all_reservations" not in st.session_state.keys() or refresh:
    with st.spinner("Loading database ..."):
        st.session_state["db"] = DBManager()
        st.session_state["all_reservations"] = st.session_state["db"].get_all_reservations()

_, img_col, _ = st.columns((1, 2, 1))
st.header("📩 Submit Reservation")
st.warning("This section is still under development, and not functional.")
img_col.image("playa_norte.png")

with st.expander("Campground Plan"):
    st.image("campground.png")

daily_prices_dict = st.session_state["db"].get_all_daily_prices()
monthly_prices_dict = st.session_state["db"].get_all_monthly_prices()

st.subheader("Reservation Details")
_, col11, _, col12, _ = st.columns((1, 4, 1, 8, 1))
s_date = col11.date_input("Select Start Date", dt.datetime.now())
e_date = col11.date_input("Select End Date", dt.datetime.now() + dt.timedelta(days=7))
site_type = col12.selectbox("Select Site Type", ["A", "B", "C", "D", "E", "F"])
with col12:
    st.write("✅ Site available.")
    st.write(f"Daily price: ", daily_prices_dict[site_type], "Pesos.")
    st.write(f"Monthly price: ", monthly_prices_dict[site_type], "Pesos.")
    #st.write(f"Required deposit: ", 400, "USD.")
site_type_clean = site_type[0]

_, col21 = st.columns((1, 16))
submit_reservation = col21.button("Submit reservation and pay deposit")