import pandas as pd
import plotly.express as px
import streamlit as st
import datetime as dt
from db_manager import DBManager

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
st.header("📅 View Reservations")
img_col.image("playa_norte.png")


with st.expander("Campground Plan"):
    st.image("campground.png")


st.subheader("View for Multiple Sites")
_, col11, _, col12, _ = st.columns((1, 4, 1, 8, 1))
s_date = col11.date_input("Select Start Date", dt.datetime.now())
e_date = col11.date_input("Select End Date", dt.datetime.now() + dt.timedelta(days=7))
site_type = col12.selectbox("Select Site Type", ["A", "B", "C", "D", "E", "F"])
site_type_clean = site_type[0]

reservations_df_list = []
for site, reservations in st.session_state["all_reservations"].items():
    if reservations:
        for start, reservation in reservations.items():
            reservations_df_list.append(
                dict(start=start, end=reservation["end"], site=site)
            )
    else:
        reservations_df_list.append(dict(start=s_date, end=s_date, site=site, name=None))

st.session_state["reservation_df"] = pd.DataFrame(reservations_df_list)

df = st.session_state["reservation_df"]
#df["start"] = pd.to_datetime(df["start"], format="%Y-%m-%d")
#df["end"] = pd.to_datetime(df["end"], format="%Y-%m-%d")

df["start"] = pd.to_datetime(df["start"], format="%Y-%m-%d").dt.strftime('%Y-%m-%d')
df["end"] = pd.to_datetime(df["end"], format="%Y-%m-%d").dt.strftime('%Y-%m-%d')

filter_df = df[df["site"].str.contains(site_type)].sort_values("site", ascending=False)
#filter_df = filter_df[filter_df.start.dt.date <= e_date]
#filter_df = filter_df[filter_df.end.dt.date >= s_date]
fig = px.timeline(filter_df, x_start="start", x_end="end", y="site")
fig.update_layout({"xaxis": dict(range=[s_date, e_date])})
st.plotly_chart(fig)
