import streamlit as st
import pandas as pd
import altair as alt
import folium
import streamlit.components.v1 as components
from folium.plugins import HeatMap
from datetime import datetime
import calendar

st.set_page_config(layout="wide")

@st.cache(persist=True)
def get_ice_jam_csv(file_name):
    df = pd.read_csv(file_name)
    df = df.rename(columns={"Latitude" : "lat", "Longitude" : "lon", "Water year" : "WY"})
    df.lon = pd.to_numeric(df.lon,errors="coerce")
    df.lat = pd.to_numeric(df.lat,errors="coerce")
    df = df[df.lat.notna()]
    df = df[df.lon.notna()]
    lat_lon_check(df)
    df = df[df.lat>10]
    df['month'] = pd.DatetimeIndex(df['Jam date']).month
    #df = df[df.lon<-10]

    return df

@st.cache
def lat_lon_check(df):
    for index, row in df.iterrows():
        if row.lat < 0:
            lon = row.lat
            lat = row.lon
            df.loc[index,'lon'] = lon
            df.loc[index, 'lat'] = lat
      
file_name = r'https://raw.githubusercontent.com/ski907/jammap/main/IJDB_dump_4JUNE2021_pandas.csv'
df = get_ice_jam_csv(file_name)       
          

def comp_c(year,df_counts):
    c = alt.Chart(df_counts).mark_bar().encode(
        alt.X('index:N', axis=alt.Axis(labelOverlap=False)),
        y='counts',
        color=alt.condition(
            alt.datum.index == year,  
            alt.value('orange'),     
            alt.value('steelblue')   
        )
        )
    return c

min_year = min(df.WY)
if min_year <1880:
    min_year = 1880

df_counts = pd.DataFrame(df.WY.value_counts())
index = range(min_year,max(df.WY))
df_counts = df_counts.reindex(index, fill_value=0)
df_counts = df_counts.reset_index().rename(columns={"WY":'counts'})

year =  st.slider("Water Year", min_year, max(df.WY))

month_filter = st.checkbox('Filter by Month?')

if month_filter:
    #month = st.slider("Month",1,12, value = 1)
    month = st.slider("Month",
                      min_value=datetime(2019,10,2),
                      max_value=datetime(2020,9,2),
                      value=datetime(2019, 11, 2),
                      format="MMM")
    month = month.month
    
    df_map = df[(df.WY == year) & (df.month == month)]
    df_month = df[df.month == month]
    df_counts = pd.DataFrame(df_month.WY.value_counts())
    index = range(min_year,max(df.WY))
    df_counts = df_counts.reindex(index, fill_value=0)
    df_counts = df_counts.reset_index().rename(columns={"WY":'counts'})
    map_title = 'Location of jams in {}, filtered by events in {}'.format(year,calendar.month_abbr[month])
    chart_title = 'Ice Jam Occurences for All Geographic Regions of United States, filtered by events in {}'.format(calendar.month_abbr[month])
else:
    map_title = 'Location of jams in {}'.format(year)
    chart_title = 'Ice Jam Occurences for All Geographic Regions of United States'
    df_map = df[(df.WY == year)]
    
c = comp_c(year,df_counts)
st.text(chart_title)
st.altair_chart(c, use_container_width=True)

state_level = st.checkbox('Show State Level Chart?')

if state_level:
    states = list(set(df.State.to_list()))
    states.sort()
    states = states[1:]
    state = st.selectbox('States',states)
    
    if month_filter:
        st.text('Ice Jam Occurences for {}, filtered by events in {}'.format(state,calendar.month_abbr[month]))
        df_state = df_month[df.State == state]
    else:
        st.text('Ice Jam Occurences for {}'.format(state))
        df_state = df[df.State == state]
    df_counts_state = pd.DataFrame(df_state.WY.value_counts())
    index = range(min_year,max(df.WY))
    df_counts_state = df_counts_state.reindex(index, fill_value=0)
    df_counts_state = df_counts_state.reset_index().rename(columns={"WY":'counts'})
    
    c_state = comp_c(year,df_counts_state)
    #st.text('Ice Jam Occurences for {}'.format(state))
    st.altair_chart(c_state, use_container_width=True)

focus = st.sidebar.selectbox('Focus Map', ['All','CONUS','Alaska'])
heat_pick = st.sidebar.selectbox('Heatmap Display',['None','All Years','Selected Year'])

if focus == 'All':
    loc = [55, -110]
    zoom = 4
elif focus == 'CONUS':
    loc = [40, -97]
    zoom = 5
elif focus == 'Alaska':
    loc = [64, -155]
    zoom = 5

st.text(map_title)
map_ak = folium.Map(tiles='cartodbdark_matter',  location=loc, zoom_start=zoom)

color_map = ['']

for lat, lon, city, jamtype, date in zip(df_map.lat, df_map.lon, df_map.City, df_map['Jam type'], df_map['Jam date']):
    folium.vector_layers.CircleMarker(
        location=[lat, lon],
        tooltip=f'<b>City: </b>{city}'
                f'<br></br>'
                f'<b>Date: </b>{date}'
                f'<br></br>'
                f'<b>Jam Type </b>{jamtype}',
        radius=10,
        color='red',
        fill=True,
        fill_color='red'        
    ).add_to(map_ak)
    

def do_heatmap(df,map_ak):
    lat = df.lat.tolist()
    lon = df.lon.tolist()

    HeatMap(list(zip(lat, lon)),radius=10, blur=5).add_to(folium.FeatureGroup(name='All Time Heat Map').add_to(map_ak))
    #folium.LayerControl().add_to(map_ak)

def do_annual_heatmap(df_map,map_ak):
    lat = df_map.lat.tolist()
    lon = df_map.lon.tolist()

    HeatMap(list(zip(lat, lon)),radius=20, blur=15).add_to(folium.FeatureGroup(name='Annual Heat Map').add_to(map_ak))
    #folium.LayerControl().add_to(map_ak)

if heat_pick == 'All Years':
    do_heatmap(df,map_ak)
elif heat_pick == 'Selected Year':
    do_annual_heatmap(df_map,map_ak)

def folium_static2(fig,width=1500, height=900):
    if isinstance(fig, folium.Map):
        fig = folium.Figure().add_child(fig)

    return components.html(fig.render(), height=(fig.height or height) + 10, width=width)

folium_static2(map_ak)
