
import streamlit as st
import chardet
#import numpy as np
import pandas as pd
import altair as alt
#import pydeck as pdk
import folium
#from streamlit_folium import folium_static
import streamlit.components.v1 as components
from folium.plugins import HeatMap

st.set_page_config(layout="wide")

#@st.cache(persist=True)
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

#@st.cache
def lat_lon_check(df):
    for index, row in df.iterrows():
        if row.lat < 0:
            lon = row.lat
            lat = row.lon
            df.loc[index,'lon'] = lon
            df.loc[index, 'lat'] = lat
      
file_name = 'IJDB_dump_4JUNE2021.csv'
df = get_ice_jam_csv(file_name)       
          

def comp_c(year):
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
    month = st.slider("Month",1,12, value = 1)
    df_map = df[(df.WY == year) & (df.month == month)]
    df_month = df[df.month == month]
    df_counts = pd.DataFrame(df_month.WY.value_counts())
    index = range(min_year,max(df.WY))
    df_counts = df_counts.reindex(index, fill_value=0)
    df_counts = df_counts.reset_index().rename(columns={"WY":'counts'})
else:
    df_map = df[(df.WY == year)]
    
c = comp_c(year)
st.altair_chart(c, use_container_width=True)

map_ak = folium.Map(tiles='cartodbdark_matter',  location=[55, -110], zoom_start=4)

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
    

# folium.vector_layers.CircleMarker(
#     location=[df_map["lat"], df_map["lon"]],
#     tooltip=f'<b>City: </b>{str(df_map.City)}'
#             f'<br></br>'
#             f'<b>Date: </b>{str(df_map["Jam date"])}'
#             f'<br></br>'
#             f'<b>Jam Type </b>{str(df_map["Jam type"])}',
#     radius=10,
#     color='#3186cc',
#     fill=True,
#     fill_color='#3186cc'        
# ).add_to(map_ak)    

def do_heatmap(df,map_ak):
    lat = df.lat.tolist()
    lon = df.lon.tolist()

    HeatMap(list(zip(lat, lon)),radius=10, blur=5).add_to(folium.FeatureGroup(name='All Time Heat Map').add_to(map_ak))
    #folium.LayerControl().add_to(map_ak)

do_heatmap(df,map_ak)


def do_annual_heatmap(df_map,map_ak):
    lat = df_map.lat.tolist()
    lon = df_map.lon.tolist()

    HeatMap(list(zip(lat, lon)),radius=20, blur=15).add_to(folium.FeatureGroup(name='Annual Heat Map').add_to(map_ak))
    folium.LayerControl().add_to(map_ak)
    
do_annual_heatmap(df_map,map_ak)
    

def folium_static2(fig,width=1500, height=900):
    if isinstance(fig, folium.Map):
        fig = folium.Figure().add_child(fig)

    return components.html(fig.render(), height=(fig.height or height) + 10, width=width)


folium_static2(map_ak)

#st.pydeck_chart(pdk.Deck(
#        map_style='mapbox://styles/mapbox/dark-v9',
#        initial_view_state=pdk.ViewState(
#                latitude=65,
#                longitude=-153,
#                zoom=3.5,
#                pitch=0,
#            ),
#    layers=[
#          pdk.Layer('ScatterplotLayer', 
#          data=df_map, 
#          get_position='[lon, lat]', 
#          get_color='[200, 30, 0, 160]', 
#          get_radius=6000,
#          )
#     ],
#    tooltip={
#        'html': '<b>Stuff:</b> {City}',
#        'style': {
#            'color': 'white'
#        }
#    },
#    ))
#
#from vega_datasets import data
#states = alt.topo_feature(data.us_10m.url, feature='states')
#background = alt.Chart(states).mark_geoshape(
#    fill='lightgray',
#    stroke='white'
#).properties(
#    width=3*500,
#    height=3*300
#).project('albersUsa')

# airport positions on background
#points = alt.Chart(df_map).mark_circle().encode(
#    longitude='lon:Q',
#    latitude='lat:Q',
#    size=alt.Size('lat:Q', title='TEST'),
#    color=alt.value('steelblue'),
#    tooltip=['City:N','State:N']
#).properties(
#    title='Alaska Ice Jams'
#)

#c2 = background + points

#st.altair_chart(c2, use_container_width=True)