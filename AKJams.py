import streamlit as st
import pandas as pd
import altair as alt
import folium
import streamlit.components.v1 as components
from folium.plugins import HeatMap
from datetime import datetime
import calendar
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb

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
          
chart_placeholder = st.empty()
chart_placeholder.beta_container()
components.html(
    "This is the output:<br>",
    height=1,
    
)

def comp_c(year,df_counts,scale_domain):
    c = alt.Chart(df_counts).mark_bar().encode(
        alt.X('index:N', axis=alt.Axis(labelOverlap=False)),
        alt.Y('counts:Q', scale=alt.Scale(domain=scale_domain)),
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

year =  st.sidebar.slider("Water Year", min_year, max(df.WY))

#year =  st.sidebar.selectbox("Water Year", range(min_year, max(df.WY)))
focus = st.sidebar.selectbox('Focus Map', ['All','CONUS','Alaska'])
heat_pick = st.sidebar.selectbox('Heatmap Display',['None','All Years','Selected Year'])
month_filter = st.sidebar.checkbox('Filter by Occurrence Chart by Month?')
state_level = st.sidebar.checkbox('Show State Level Occurrence Chart?')
all_jams = st.sidebar.checkbox('Plot all jams? (slow plotting)')
no_jams = st.sidebar.checkbox('Turn Off Jam Markers')


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
    chart_title = 'Ice Jam Occurrences for All Geographic Regions of United States, filtered by events in {}'.format(calendar.month_abbr[month])
    scale_domain = [0,300]
else:
    map_title = 'Location of jams in {}'.format(year)
    chart_title = 'Ice Jam Occurrences for All Geographic Regions of United States'
    df_map = df[(df.WY == year)]
    scale_domain = [0,600]
    
c = comp_c(year,df_counts,scale_domain=scale_domain)
st.text(chart_title)
st.altair_chart(c, use_container_width=True)

if state_level:
    states = list(set(df.State.to_list()))
    states.sort()
    states = states[1:]
    state = st.selectbox('States',states)
    
    if month_filter:
        st.text('Ice Jam Occurrences for {}, filtered by events in {}'.format(state,calendar.month_abbr[month]))
        df_state = df_month[df.State == state]
    else:
        st.text('Ice Jam Occurences for {}'.format(state))
        df_state = df[df.State == state]
    df_counts_state = pd.DataFrame(df_state.WY.value_counts())
    index = range(min_year,max(df.WY))
    df_counts_state = df_counts_state.reindex(index, fill_value=0)
    df_counts_state = df_counts_state.reset_index().rename(columns={"WY":'counts'})
    
    c_state = comp_c(year,df_counts_state,scale_domain=[0,100])
    #st.text('Ice Jam Occurences for {}'.format(state))
    st.altair_chart(c_state, use_container_width=True)


if focus == 'All':
    loc = [55, -110]
    zoom = 3.45
elif focus == 'CONUS':
    loc = [40, -97]
    zoom = 5
elif focus == 'Alaska':
    loc = [64, -155]
    zoom = 5

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

mark_radius = 6
mark_color = 'red'

if all_jams:
    df_map = df
    mark_radius = 6
    mark_color = 'blue'
    map_title = 'Location of all jams in the IJDB'

#if no_jams:
#    all_jams = False
#    df_map = pd.DataFrame(columns=df.columns)
    

map_ak = folium.Map(tiles='cartodbdark_matter',  location=loc, zoom_start=zoom)

color_map = ['']

if no_jams == False:
    for lat, lon, city, jamtype, date, damage in zip(df_map.lat, df_map.lon, df_map.City, df_map['Jam type'], df_map['Jam date'], df_map['Damages']):
        folium.vector_layers.CircleMarker(
            location=[lat, lon],
            tooltip=f'<b>City: </b>{city}'
                    f'<br></br>'
                    f'<b>Date: </b>{date}'
                    f'<br></br>'
                    f'<b>Jam Type </b>{jamtype}'
                    f'<br></br>'
                    f'<b>Damages </b>{damage}',
            radius=mark_radius,
            color=mark_color,
            fill=True,
            fill_color=mark_color        
    ).add_to(map_ak)

if heat_pick == 'All Years':
    do_heatmap(df,map_ak)
elif heat_pick == 'Selected Year':
    do_annual_heatmap(df_map,map_ak)

def folium_static2(fig,width=1200, height=600):
    if isinstance(fig, folium.Map):
        fig = folium.Figure().add_child(fig)

    return components.html(fig.render(), height=(fig.height or height) + 10, width=width)
with chart_placeholder.beta_container():
    st.text(map_title)
    folium_static2(map_ak)

##########
# Footer #                         #  https://discuss.streamlit.io/t/st-footer/6447
##########

def image(src_as_string, **style):
    return img(src=src_as_string, style=styles(**style))

def link(link, text, **style):
    return a(_href=link, _target="_blank", style=styles(**style))(text)


def layout(*args):
    style = """
    <style>
        MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp { bottom: 60px; }
    </style>
    """

    style_div = styles(
        position="fixed",
        right=0,
        bottom=0,
        margin=px(0, 15, 0, 0),
        text_align="center",
        opacity=0.5,
    )

    body = p()
    foot = div(
        style=style_div
    )(
        body
    )

    st.markdown(style, unsafe_allow_html=True)
    for arg in args:
        if isinstance(arg, str):
            body(arg)
        elif isinstance(arg, HtmlElement):
            body(arg)
    st.markdown(str(foot), unsafe_allow_html=True)

def footer():
    myargs = [
        link("jams.iskion.rocks",image('https://raw.githubusercontent.com/ski907/jammap/main/iskionrocks_small.png')),
    ]
    layout(*myargs)

if __name__ == "__main__":
    footer()