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
st.header("🛠 Administration Panel")
img_col.image("playa_norte.png")

if st.session_state['authenticated']:
    sites = get_reservable_sites()
    all_sites = []
    for v in sites.values():
        all_sites += list(v)

    st.subheader("Create New Reservation")
    with st.form("New Reservation", clear_on_submit=True):
        _, col11, _, col12, _ = st.columns((1, 4, 1, 8, 2))
        s_date = col11.date_input(
            "Select Start Date", dt.datetime.now())
        e_date = col11.date_input(
            "Sekect End Date", dt.datetime.now() + dt.timedelta(7))
        name = col12.text_input("Input Name")
        site = col12.selectbox("Select Site", all_sites)
        submitted = st.form_submit_button("Verify")
        if submitted:
            st.session_state['pending_submission'] = True

    if 'pending_submission' in st.session_state and st.session_state['pending_submission']:

        reservation = {
            s_date.strftime("%Y-%m-%d"): {
                "name": name,
                "start": s_date.strftime("%Y-%m-%d"),
                "end": e_date.strftime("%Y-%m-%d"),
                "duration": (e_date - s_date).days
            }
        }
        db = st.session_state["db"]
        site_available = db.validate_reservation_is_possible(site, reservation)
        if name != "" and site_available and e_date > s_date:
            reservation_available = True
        else:
            reservation_available = False

        _, col21, _ = st.columns((1, 14, 2))
        if reservation_available:
            with col21:
                st.write("✅ Site ", site, " available from ",
                        s_date, " to ", e_date, " for ", name, ".")
                if col21.button("Add new reservation"):
                    try:
                        db.add_reservation_to_site(site, reservation)
                        st.success("Reservation successfuly added !")
                    except:
                        st.error("Failure - Unable to add reservation")
                    with st.spinner("Refreshing database ..."):
                        try:
                            st.session_state["db"] = DBManager()
                            st.session_state["all_reservations"] = st.session_state["db"].get_all_reservations()
                        except:
                            pass
                    st.session_state['pending_submission'] = False
                    time.sleep(1)
                    st.experimental_rerun()
        else:
            with col21:
                if name == "":
                    st.write("❌ Missing reservation name.")
                elif not site_available:
                    st.write("❌ Invalid dates, this site is already busy.")
                elif e_date <= s_date:
                    st.write(
                        "❌ Invalid dates, end date must be later than start date.")

    st.subheader("Cancel Reservation")
    _, col21, _ = st.columns((1, 12, 2))

    with col21:
        reservations = st.session_state['all_reservations']

        site = st.selectbox("Select Site", all_sites)
        reservation_date_name_dict = {}
        for k, v in reservations[site].items():
            reservation_date_name_dict[k] = k + " (" + v["name"] + ")"
        reservation_date_name_dict = dict(
            sorted(reservation_date_name_dict.items()))

        reservation_nice = st.selectbox("Select Reservation", list(
            reservation_date_name_dict.values()))
        key_to_delete = [k for k, v in reservation_date_name_dict.items()
                        if v == reservation_nice]
        if key_to_delete:
            if st.button("Cancel Reservation"):
                try:
                    db = st.session_state["db"]
                    db.delete_reservation(site, key_to_delete[0])
                    st.warning("Reservation cancelled.")
                except:
                    st.error("Error - Could not cancel reservation.")
                time.sleep(1)
                st.session_state["db"] = DBManager()
                st.session_state["all_reservations"] = st.session_state["db"].get_all_reservations()
                st.experimental_rerun()
else:
    st.warning("Restricted access. Please login as administrator.")
