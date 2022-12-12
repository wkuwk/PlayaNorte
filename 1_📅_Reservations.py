import pandas as pd
import plotly.express as px
import streamlit as st
import datetime as dt
from db_utils import (
    connect_to_firebase_db_and_authenticate,
    get_all_reservations
)

st.sidebar.title("Reservation System")
_, img_col, _ = st.columns((1, 2, 1))
st.header("Reservation System")
img_col.image("playa_norte.png")

with st.expander("Campground Plan"):
    st.image("campground.png")

st.subheader("View Reservations")
_, col11, _, col12, _ = st.columns((1, 4, 1, 10, 1))
s_date = col11.date_input(
    "Select Start Date", dt.datetime.now())
e_date = col11.date_input(
    "Sekect End Date", dt.datetime.now() + dt.timedelta(days=7))
site_type = col12.selectbox(
    "Select Site Type", ["A", "B", "C", "D", "E"])
site_type_clean = site_type[0]


db = connect_to_firebase_db_and_authenticate()
st.session_state['db'] = db

with st.spinner("Loading database ..."):
    st.session_state['all_reservations'] = get_all_reservations(db)

reservations_df_list = []
for site, reservations in st.session_state['all_reservations'].items():
    if reservations:
        for start, reservation in reservations.items():
            reservations_df_list.append(dict(
                start=start,
                end=reservation['end'],
                site=site))
    else:
        reservations_df_list.append(dict(
            start=s_date, end=s_date, site=site))

st.session_state['reservation_df'] = pd.DataFrame(reservations_df_list)


df = st.session_state['reservation_df']
df['start'] = pd.to_datetime(df['start'], format="%Y-%m-%d")
df['end'] = pd.to_datetime(df['end'], format="%Y-%m-%d")
filter_df = df[df['site'].str.contains(
    site_type)].sort_values('site', ascending=False)
filter_df = filter_df[filter_df.start.dt.date <= e_date]
filter_df = filter_df[filter_df.end.dt.date >= s_date]
fig = px.timeline(filter_df,
                  x_start="start", x_end="end", y="site")
st.plotly_chart(fig)
