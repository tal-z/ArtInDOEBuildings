import folium
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from sodapy import Socrata
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    client = Socrata("data.cityofnewyork.us",
                     'odQdEcIxnATZPym3KySwgWw27',
                     username=os.getenv('socrata_username'),
                     password=os.getenv('socrata_password'))
    results = client.get("8a4n-zmpj",
                         content_type='json',
                         limit=3000)
    doe_art = pd.DataFrame(results)

    doe_locations = gpd.read_file(
        r'C:\Users\PC\PycharmProjects\ArtInDOEBuildings\Public_School_Locations\Public_Schools_Points_2011-2012A.shp')

    doe_art = doe_art.merge(doe_locations, left_on='bldgid', right_on='LOC_CODE')
    doe_art['artwork_year'] = doe_art['artwork_year'].apply(lambda x: str(x)[:4])
    # print(doe_art.loc[0])
    doe_art_json = gpd.GeoDataFrame(doe_art).to_crs(epsg=4326).to_json()
    # doe_art.plot()
    # plt.show()

    geolocator = Nominatim(user_agent='ArtInDOEBuildings')
    loc = geolocator.geocode("New York, NY").raw

    # Create the map
    my_map = folium.Map(location=[loc['lat'], loc['lon']], zoom_start=10, control_scale=True)
    itm_txt = "Art in DOE Buildings test text"
    legend_html = """
         <style>
            #div-to-toggle{
                z-index: 1;
                position: relative;
                border: 1px solid Black;
                padding: 15px 15px 15px 15px;
                margin: 20px auto;
                width: 30%;
                background: #fff;
                overflow: visible;
                box-shadow: 3px 3px 8px #555;
            }
            #close-btn{
                position: absolute;
                background: #fff;
                border: 2px solid #999;
                color: #555;
                border-radius: 12px;
                height:25px;
                width:25px;
                padding: 1px;
                top: -10px;
                right: -10px;
                box-shadow: 2px 2px 10px #555;
                font-weight: bold;
                cursor: pointer;
            }
            .btn-container{
                width: 300px;
                margin: 10px auto;
                text-align: center;
                clear: both;
            }
            .btn-container button{
                height: 35px;
            }
        </style>
<div id="div-to-toggle">
    <button id="close-btn">X</button> 
    <h1>Art in DOE Buildings</h1>
    <p>Artwork data is sourced from <a href="https://data.cityofnewyork.us/Education/Art-in-DOE-buildings/8a4n-zmpj">Art in DOE Buildings on NYC Open Data</a>.
    <br>
    School location data is sourced from <a href="https://data.cityofnewyork.us/Education/School-Point-Locations/jfju-ynrr">School Point Locations on NYC Open Data</a>.
    
    </p>
</div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
<script>
    $('body, #close-btn').click(function() {
        $('#div-to-toggle').hide();
        event.stopPropagation();
    })
</script>"""
    my_map.get_root().html.add_child(folium.Element(legend_html))
    popups = folium.features.GeoJsonPopup(fields=['artwork_title', 'artist_firstname', 'artist_lastname',
                                                  'artwork_year', 'medium', 'school_name', ],
                                          aliases=['Artwork Title', 'Artist First Name', 'Artist Last Name',
                                                   'Year', 'Medium', 'School', ])

    points = folium.features.GeoJson(doe_art_json, popup=popups)  # .add_to(my_map)
    points.add_to(my_map)
    # Display the map
    my_map.save('DOEArt.html')
