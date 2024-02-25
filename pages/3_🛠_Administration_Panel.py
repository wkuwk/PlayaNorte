import streamlit as st
import datetime as dt
import time
import plotly.express as px
from db_manager import DBManager
from utils import get_reservable_sites
import pandas as pd

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

if not st.session_state["authenticated"]:
    user = st.sidebar.text_input("User")
    password = st.sidebar.text_input("Password")
    login = st.sidebar.button("Login")
    if login:
        if user.lower() == " " and password.lower() == " ":
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.sidebar.error("Incorrect credentials.")
else:
    st.sidebar.success("Logged in as administrator.")

if "all_reservations" not in st.session_state.keys() or refresh:
    with st.spinner("Loading database ..."):
        st.session_state["db"] = DBManager()
        st.session_state["all_reservations"] = st.session_state[
            "db"
        ].get_all_reservations()

_, img_col, _ = st.columns((1, 2, 1))
st.header("🛠 Administration Panel")
img_col.image("playa_norte.png")

if st.session_state["authenticated"]:
    sites = get_reservable_sites()
    all_sites = []
    for v in sites.values():
        all_sites += list(v)

    # CREATE USER DICT TO FILTER BY NAME
    user_dict = {}
    for site, reservations in st.session_state["all_reservations"].items():
        for reservation_details in reservations.values():
            name = reservation_details["name"].lower()

            # Add name key if not present
            if name not in user_dict.keys():
                user_dict[name] = []

            # Add reservation details to list
            user_dict[name].append(
                (site, reservation_details["start"], reservation_details["end"])
            )

    st.subheader("Current Reservations")
    st.info("Blue bars represent occupied periods.")
    _, col11, _, col12, _ = st.columns((1, 4, 1, 8, 1))
    s_date = col11.date_input("Select Start Date", dt.datetime.now())
    e_date = col11.date_input(
        "Select End Date", dt.datetime.now() + dt.timedelta(days=365)
    )
    site_type = col12.selectbox(
        "Select Site Type", ["A", "B", "C", "D", "E", "F", "Others"]
    )
    site_type_clean = site_type[0]

    reservations_df_list = []
    for site, reservations in st.session_state["all_reservations"].items():
        if reservations:
            for start, reservation in reservations.items():
                reservations_df_list.append(
                    dict(
                        start=start,
                        end=reservation["end"],
                        site=site,
                        name=reservation["name"],
                    )
                )
        else:
            reservations_df_list.append(
                dict(start=s_date, end=s_date, site=site, name=None)
            )
    st.session_state["reservation_df"] = pd.DataFrame(reservations_df_list)

    df = st.session_state["reservation_df"]
    df["start"] = pd.to_datetime(df["start"], format="%Y-%m-%d")
    df["end"] = pd.to_datetime(df["end"], format="%Y-%m-%d")
    filter_df = df[df["site"].str.contains(site_type)].sort_values(
        "site", ascending=False
    )
    # filter_df = filter_df[filter_df.start.dt.date <= e_date]
    # filter_df = filter_df[filter_df.end.dt.date >= s_date]
    fig = px.timeline(
        filter_df, x_start="start", x_end="end", y="site", hover_name="name"
    )
    fig.update_layout({"xaxis": dict(range=[s_date, e_date])})
    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True
    st.plotly_chart(fig)

    st.divider()
    st.subheader("Find Reservation by Name")
    # Order user_dict keys by alphabetical order
    user_keys_ordered = sorted(user_dict.keys())
    filter_name_col, _ = st.columns(2)
    user = filter_name_col.selectbox("Select User", user_keys_ordered)
    for reservation_details in user_dict[user]:
        st.write(
            "User",
            user,
            "has a reservation at site",
            reservation_details[0],
            "from",
            reservation_details[1],
            "to",
            reservation_details[2],
        )

    st.divider()
    st.subheader("Create New Reservation")
    with st.form("New Reservation", clear_on_submit=True):
        _, col11, _, col12, _ = st.columns((1, 4, 1, 8, 2))
        s_date = col11.date_input("Select Start Date", dt.datetime.now())
        e_date = col11.date_input(
            "Select End Date", dt.datetime.now() + dt.timedelta(7)
        )
        name = col12.text_input("Input Name")
        site = col12.selectbox("Select Site", all_sites)
        submitted = st.form_submit_button("Verify")
        if submitted:
            st.session_state["pending_submission"] = True

    if (
        "pending_submission" in st.session_state
        and st.session_state["pending_submission"]
    ):
        reservation = {
            s_date.strftime("%Y-%m-%d"): {
                "name": name,
                "start": s_date.strftime("%Y-%m-%d"),
                "end": e_date.strftime("%Y-%m-%d"),
                "duration": (e_date - s_date).days,
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
                st.write(
                    "✅ Site ",
                    site,
                    " available from ",
                    s_date,
                    " to ",
                    e_date,
                    " for ",
                    name,
                    ".",
                )
                if col21.button("Add new reservation"):
                    try:
                        db.add_reservation_to_site(site, reservation)
                        st.success("Reservation successfuly added !")
                    except:
                        st.error("Failure - Unable to add reservation")
                    with st.spinner("Refreshing database ..."):
                        try:
                            st.session_state["db"] = DBManager()
                            st.session_state["all_reservations"] = st.session_state[
                                "db"
                            ].get_all_reservations()
                        except:
                            pass
                    st.session_state["pending_submission"] = False
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
                        "❌ Invalid dates, end date must be later than start date."
                    )

    st.divider()
    st.subheader("Cancel Reservation")
    _, col21, _ = st.columns((1, 12, 2))

    with col21:
        reservations = st.session_state["all_reservations"]

        site = st.selectbox("Select Site", all_sites)
        reservation_date_name_dict = {}
        for k, v in reservations[site].items():
            reservation_date_name_dict[k] = k + " (" + v["name"] + ")"
        reservation_date_name_dict = dict(sorted(reservation_date_name_dict.items()))

        reservation_nice = st.selectbox(
            "Select Reservation", list(reservation_date_name_dict.values())
        )
        key_to_delete = [
            k for k, v in reservation_date_name_dict.items() if v == reservation_nice
        ]
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
                st.session_state["all_reservations"] = st.session_state[
                    "db"
                ].get_all_reservations()
                st.experimental_rerun()

    st.divider()
    st.subheader("Modify Site Prices")
    daily_prices_dict = st.session_state["db"].get_all_daily_prices()
    monthly_prices_dict = st.session_state["db"].get_all_monthly_prices()
    _, price_col_day, _, price_col_month, _ = st.columns((1, 4, 2, 4, 1))

    price_col_day.write("##### Daily prices (Pesos)")
    for k, v in sorted(daily_prices_dict.items()):
        daily_prices_dict[k] = price_col_day.number_input(k, value=v, step=10)

    price_col_month.write("##### Monthly prices (Pesos)")
    for k, v in sorted(monthly_prices_dict.items()):
        monthly_prices_dict[k] = price_col_month.number_input(k, value=v, step=500)

    if price_col_day.button("Update Daily Prices"):
        try:
            if len(daily_prices_dict) == 7:
                st.session_state["db"].update_sites_daily_prices(daily_prices_dict)
                price_col_day.success("Daily prices updated !")
            else:
                price_col_day.error("Error - Could not update prices.")
        except:
            price_col_day.error("Error - Could not update prices.")
        time.sleep(2)
        st.experimental_rerun()

    if price_col_month.button("Update Monthly Prices"):
        try:
            if len(monthly_prices_dict) == 7:
                st.session_state["db"].update_sites_monthly_prices(monthly_prices_dict)
                price_col_month.success("Monthly prices updated !")
            else:
                price_col_month.error("Error - Could not update prices.")
        except:
            price_col_month.error("Error - Could not update prices.")
        time.sleep(2)
        st.experimental_rerun()

else:
    st.warning("Restricted access. Please login as administrator.")
