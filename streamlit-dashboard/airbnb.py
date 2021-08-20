import streamlit as st
import pandas as pd
import numpy as np
import pymysql
import mysql.connector
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from PIL import Image

## GLOBAL SETTING
st.set_page_config(page_title="AirBnB Analytics", 
                   page_icon= ':hotel:', 
                   layout='wide')
cola, colb, colc = st.beta_columns([1,10,1])
with cola:
    st.write("")
with colb:
    title_image = Image.open("assets/title2.png")
    st.image(title_image)
with colc:
    st.write("")

## CONNECTION TO DATABASE
conn =  mysql.connector.connect( 
        host = "localhost",
        port = 3306,
        user = "root",
        password = "",
        database = "airbnb_data"
        ) 
# -------------------------------------------------------------------------------------
## TAB OVERVIEW
# value box number of listings
number_listing = pd.read_sql_query("SELECT COUNT(*) AS freq FROM listing", conn)
number_listing = number_listing['freq'][0]

# value box number of listings
number_host = pd.read_sql_query("SELECT COUNT(*) AS freq FROM host_info", conn)
number_host = number_host['freq'][0]

# value box number of listings
number_review = pd.read_sql_query("SELECT SUM(number_of_reviews) as num_review FROM listing", conn)
number_review = number_review['num_review'][0]

def price_distribution():
    price_distribution = pd.read_sql_query(
    '''
    SELECT name, SUM(price) AS price, longitude, latitude
    FROM listing
    GROUP BY name, longitude, latitude
    '''
    ,conn)

    map_sg = folium.Map(location=[price_distribution.latitude.mean(), price_distribution.longitude.mean()], zoom_start=5)
    marker_cluster = folium.plugins.MarkerCluster().add_to(map_sg)
    for name, lat, lon, price in zip(price_distribution['name'],price_distribution['latitude'], price_distribution['longitude'], price_distribution['price']):
        popup = folium.Html("<b>"  + name + "</b><br>" +\
                        "Price: {:,}".format(price) + "<br>", script = True)
        popup = folium.Popup(popup, max_width=2650)
        folium.Marker(location = [lat, lon],
                  popup = popup
                 ).add_to(marker_cluster)
    folium_static(map_sg)
    return map_sg

# -------------------------------------------------------------------------------------
## TAB LISTING
def property_type():
    property_type = pd.read_sql_query(
    '''
    SELECT property_type, COUNT(property_type) AS frequency
    FROM listing
    GROUP BY property_type
    ORDER BY frequency DESC
    LIMIT 10
    '''
    ,conn)
    property_type = property_type.sort_values(by='frequency', ascending=True)
    fig = px.bar(property_type, x='frequency', y='property_type', 
             title="Top Property Type in Listings",
             orientation='h',
             #color = '#29b6f6',
            labels={
                'property_type' : 'Property Type',
                'frequency' : 'Frequency'
            },
            )
            
    return fig

def room_type():
    top_avg_roomtype = pd.read_sql_query(
    '''
    SELECT room_type, average_price, frequency
    FROM 
        ( SELECT room_type, AVG(price) AS average_price, COUNT(*) as frequency
          FROM listing
          GROUP BY room_type
          ) as new_data
    WHERE frequency >=20
    ORDER BY average_price DESC
    ''',conn)
    fig = go.Figure(data=[go.Pie(labels=top_avg_roomtype['room_type'], values=top_avg_roomtype['average_price'], hole=.4)])
    fig.update_traces(hole=.4, marker=dict(colors=['#e57373', '#f06292', '#4db6ac','#81c784']))
    fig.update_layout(
        title_text="Room Type by Average Price")
    return fig

def top_bot_10():
    #top 10 property type based on average price
    top_avg_proptype = pd.read_sql_query(
    '''
    SELECT property_type, average_price, frequency
    FROM 
        ( SELECT property_type, AVG(price) AS average_price, COUNT(*) as frequency
          FROM listing
          GROUP BY property_type
          ) as new_data
    WHERE frequency >=20
    ORDER BY average_price DESC
    LIMIT 10
    ''',conn)
    top_avg_proptype = top_avg_proptype.sort_values(by='average_price', ascending=True)
    plot_top = go.Bar(x=top_avg_proptype['average_price'], 
               y=top_avg_proptype['property_type'],
               name='Top 10',
               orientation='h',
               marker=dict(
                   color = '#29b6f6'
               )
              )

    #bottom 10 property type based on average price
    bot_avg_proptype = pd.read_sql_query(
    '''
    SELECT property_type, average_price, frequency
    FROM 
        ( SELECT property_type, AVG(price) AS average_price, COUNT(*) as frequency
          FROM listing
          GROUP BY property_type
          ) as new_data
    WHERE frequency >=20
    ORDER BY average_price
    LIMIT 10
    ''',conn)
    bot_avg_proptype.sort_values(by='average_price', inplace=True)
    plot_bottom = go.Bar(x=bot_avg_proptype['average_price'], y=bot_avg_proptype['property_type'],
                orientation='h',
               name='Bottom 10',
               marker=dict(
                   color = '#ef5350'
               )
              )
    # make a subplots
    sub = make_subplots(rows=2, cols=1)
    sub.append_trace(plot_top, 1,1)
    sub.append_trace(plot_bottom, 2, 1)
    sub.update_layout(height=600, width=800, title_text="Top and Bottom 10 Property based on Average Price",xaxis2=dict(range=[0,270]))

    return sub

# Sub menu Amenities
query = '''
    SELECT amenities, price
    FROM listing
    '''
df_query = pd.read_sql_query(query, conn)

def most_amenities ():
    # most amenities
    most_amenities = df_query['amenities'].str.split(', ', expand=True).stack().value_counts().to_frame("Total").head(10)
    most_amenities.sort_values(by='Total',ascending=True, inplace=True)
    fig = px.bar(most_amenities, x='Total', y=most_amenities.index, 
             title="Top Amenities",
            orientation='h',
            labels={
                'index' : 'Amenities',
                'Total' : 'Frequency'
            })
    return fig

def cor():
    # correlation between amenities and price
    df_query['count_amenities'] = df_query.amenities.str.strip().str.split(',').apply(len)
    scatter = px.scatter(df_query,
           x = np.log10(df_query['price']),
           y = df_query['count_amenities'],
           title='Correlation Between Amenities and Price',
           opacity=0.5,
           labels={
                'x' : 'Price',
                'count_amenities' : 'Count Amenities'
            })

    return scatter
# -------------------------------------------------------------------------------------
## TAB HOST
# value box number of superhost
n_superhost = pd.read_sql_query(
    '''
    SELECT COUNT(*) as freq
    FROM host_info
    WHERE host_is_superhost = 1
    '''
    , conn)
n_superhost = n_superhost['freq'][0]

# value box number of verified host
n_verified = pd.read_sql_query(
    """
    SELECT COUNT(*) as freq
    FROM host_info
    WHERE host_identity_verified = 1
    """, conn)
n_verified = n_verified['freq'][0]

# value box number of unverified host 
n_non_verified = pd.read_sql_query(
    """
    SELECT COUNT(*) as freq
    FROM host_info
    WHERE host_identity_verified = 0
    """,conn)
n_non_verified = n_non_verified['freq'][0]

def include_superhost_ () :
    q_include = pd.read_sql_query(
        '''
        SELECT listing.host_id, host_info.host_name, host_info.host_since,  host_info.host_is_superhost, host_info.host_identity_verified, 
        COUNT(*) as number_of_listing, SUM( price * number_of_reviews * minimum_nights ) as earning, host_info.host_url
        FROM listing
        LEFT JOIN host_info
        ON listing.host_id = host_info.host_id
        WHERE host_info.host_since IS NOT NULL
        GROUP BY listing.host_id
        ORDER BY earning DESC
        LIMIT 10
        ''', conn
    )
    return q_include

def not_include_superhost():
    q_not_include = pd.read_sql_query(
        '''
        SELECT listing.host_id, host_info.host_name, host_info.host_since,  host_info.host_is_superhost, host_info.host_identity_verified, COUNT(*) as number_of_listing, SUM( price * number_of_reviews * minimum_nights ) as earning, host_info.host_url
        FROM listing
        LEFT JOIN host_info
        ON listing.host_id = host_info.host_id
        WHERE host_info.host_is_superhost = 0 AND host_info.host_since IS NOT NULL
        GROUP BY listing.host_id
        ORDER BY earning DESC
        LIMIT 10
        ''', conn

    )
    return q_not_include

# -------------------------------------------------------------------------------------
## MAIN FUNCTION
def main():
    side_col1, side_col2, side_col3 = st.sidebar.beta_columns([2,6,1])
    with side_col1:
        image = Image.open('assets/airbnb-logo.jpg')
        st.image(image, width=None)
    with side_col2:
        st.title("Airbnb Analytics")

    menu = ["Overview","Listings","Hosts"]
    choice = st.sidebar.selectbox("", menu, index=0)
    
# -------------------------------------------------------------------------------------
## OVERVIEW

    if choice == "Overview":
        st.markdown("Airbnb, Inc. is an American company that operates an online marketplace for lodging, primarily homestays for vacation rentals, and tourism activities.\
                    On this dashboard you can explore information regarding the host and room listings available in Singapore.\
                    All data is sourced from publicly available information from the [Airbnb site](http://insideairbnb.com/get-the-data.html).")
        # row value box
        vbox1, vbox2, vbox3, vbox4, vbox5, vbox6 = st.beta_columns([2,5,2,5,2,5])
        with vbox1 :
            image = Image.open('assets/hotel.png')
            st.image(image, width=None)
        with vbox2 :
            st.markdown( "**{:,}".format(int(number_listing)) + "**\n\n Number of Listing")
        with vbox3 :
            image = Image.open('assets/owner.png')
            st.image(image, width=None)
        with vbox4 :
             st.markdown( "**{:,}".format(int(number_host)) + "**\n\n Number of Host")
        with vbox5 :
            image = Image.open('assets/evaluate.png')
            st.image(image, width=None)
        with vbox6 :
             st.markdown( "**{:,}".format(int(number_review)) + "**\n\n Total Reviews")

        # row map
        cola, colb, colc = st.beta_columns([1,5,1])
        with cola:
            st.write("")
        with colb:
            map = price_distribution()
            st.write(map)
        with colc:
            st.write("")
# -------------------------------------------------------------------------------------
# # LISTINGS
   
    elif choice == "Listings":
        #st.subheader("Listing Analysis")
        st.markdown("""
            Airbnb hosts can list entire homes/apartments, private or shared rooms. 
            Airbnb provides [detailed guides](https://www.airbnb.com/help/topic/1424/preparing-to-host) on how hosts could set up their places.\n\n
            The most common listing available is either entire home or apartment, followed by hotel room. Some hotels are also listing their room in Airbnb apparently.
            """
            )
        st.subheader("Select the information you want to perform :")
        info_plot = st.radio("",('Room and Property', 'Amenities'))

        if info_plot == 'Room and Property' :
            # row 1
            r_type = room_type()
            st.write(r_type)
            # row 2
            prop_type = property_type()
            col1, col2 = st.beta_columns((1,1))
            col1.write(prop_type)     
            #row 3
            top_bot = top_bot_10()
            st.write(top_bot)

        else :
            # row 1
            amenities = most_amenities()
            st.write(amenities)
            # row 2
            correlation = cor()
            st.write(correlation)

        
        
# -------------------------------------------------------------------------------------
## HOST
    elif choice == "Hosts":
        #st.subheader("Hosts Analysis")
        st.markdown("""
            Airbnb hosts are required to [confirm their identity](https://www.airbnb.com/help/article/1237/verifying-your-identity) such as their name, address, phone, etc. 
            [Superhosts](https://www.airbnb.com/help/article/828/what-is-a-superhost) are experienced hosts who provide a shining example for other hosts, and extraordinary experiences for their guests.
            """)
        
         # Valuebox --------
        vbox1, vbox2, vbox3, vbox4, vbox5, vbox6 = st.beta_columns([2.5, 6 , 2.5, 6 , 2.5, 6])
        with vbox1 :
            image = Image.open('assets/star.png')
            st.image(image, width=None)
        with vbox2 :
           st.markdown( "**{:,}".format(int(n_superhost)) + "**\n\n Superhost")
        with vbox3 :
            image = Image.open('assets/check.png')
            st.image(image, width=None)
        with vbox4 :
            st.markdown( "**{:,}".format(int(n_verified)) + "**\n\n Verified Host")
        with vbox5 :
            image = Image.open('assets/wrong.png')
            st.image(image, width=None)
        with vbox6 :
            st.markdown( "**{:,}".format(int(n_non_verified)) + "**\n\n Unverified Host")
        
        st.markdown("""
        ## Top 10 Host by Total Earning
        **Total earning** gained by hosts are calculated by the total product of their **listing price**, 
        **number of reviews** to represent the number of customers, and  the **minimun night** to represent the number of night stays.
        """)

        include_superhost = st.checkbox("Include Superhost")

        if include_superhost:
            df_top_host = include_superhost_()
        else:
            df_top_host = not_include_superhost()
    

        df_top_host.replace({'host_is_superhost': {1:'\u2714', 0:'\u274c'}, 'host_identity_verified': {1:'\u2714', 0:'\u274c'}}, inplace = True)
        df_top_host.columns = ['Host ID', 'Host Name', 'Host Since', 'Superhost', 'Identity Verified', 'Listing Count', 'Total Earning', 'Host URL']
        st.table(df_top_host)
    
if __name__ == '__main__':
    main()