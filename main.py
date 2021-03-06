from ArtImgScrape import scrape_art
import folium
from folium.plugins import MarkerCluster
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from sodapy import Socrata
import os
from dotenv import load_dotenv

load_dotenv()


def create_popup(row, columns=list):
    """Creates a folium popup object for each marker,
    for use in adding to a marker cluster."""
    popup = ''
    for col, item in zip(columns, row):
        if col not in ['geometry', 'title']:
            popup = popup + rf"<b>{str(col).title()}</b><br>{str(item)}<br>"
    return folium.Popup(popup, min_width=350, max_width=350)


if __name__ == '__main__':
    # 1. Get DOE Artwork data from NYC Open Data, and store it in a dataframe
    client = Socrata("data.cityofnewyork.us",
                     'odQdEcIxnATZPym3KySwgWw27',
                     username=os.getenv('socrata_username'),
                     password=os.getenv('socrata_password'))
    results = client.get("8a4n-zmpj",
                         content_type='json',
                         limit=3000)
    doe_art = pd.DataFrame(results)

    # 2. Read DOE School location data from a shapefile provided by NYC DCP.
    doe_locations = gpd.read_file(
        r'C:\Users\PC\PycharmProjects\ArtInDOEBuildings\Public_School_Locations\Public_Schools_Points_2011-2012A.shp')

    # 3. Merge the artwork data with the schools location data, and clean up artwork data fields.
    doe_art = doe_art.merge(doe_locations, left_on='bldgid', right_on='LOC_CODE')
    doe_art['artwork_year'] = doe_art['artwork_year'].apply(lambda x: str(x)[:4])
    doe_art_titles_media = doe_art.groupby('artwork_title')['medium'].apply(list)
    doe_art_titles_media = doe_art_titles_media.apply(lambda x: ", ".join(map(str, x)))
    doe_art = doe_art.drop_duplicates(subset=['artwork_title'])
    doe_art = doe_art.merge(doe_art_titles_media, on='artwork_title', how='outer')
    doe_art['Artist Name'] = doe_art['artist_firstname'] + " " + doe_art['artist_lastname']
    doe_art = doe_art[['artwork_title', 'Artist Name', 'medium_y', 'artwork_year', 'school_name', 'geometry']]
    doe_art.columns = ['Artwork Title', 'Artist Name', 'Media', 'Year', 'School Name', 'geometry']
    doe_art = gpd.GeoDataFrame(doe_art).to_crs(epsg=4326)

    # 4. Scrape image links of artwork into a dataframe from the NYC School Construction Authority website,
    #    and merge them with doe_art dataframe.
    art_links_df = scrape_art()
    doe_art = doe_art.merge(art_links_df[['title', 'image']], how='left', left_on='Artwork Title', right_on='title')

    # 5. Create a Folium map from the doe_art dataframe created in the previous step.
    geolocator = Nominatim(user_agent='ArtInDOEBuildings')
    loc = geolocator.geocode("New York, NY").raw
    my_map = folium.Map(location=[loc['lat'], loc['lon']], zoom_start=10, control_scale=True)
    marker_cluster = MarkerCluster().add_to(my_map)
    for idx, row in doe_art.iterrows():
        if type(row.image) != float:
            folium.Marker(location=[row.geometry.y, row.geometry.x],
                          icon=folium.Icon(color="green", icon="fa-paint-brush", prefix='fa'),
                          popup=create_popup(row,  doe_art.columns)).add_to(marker_cluster)
        else:
            folium.Marker(location=[row.geometry.y, row.geometry.x],
                          icon=folium.Icon(color="blue"),
                          popup=create_popup(row[:-1], doe_art.columns[:-1])).add_to(marker_cluster)

    # 6. Add a custom legend to the map, which disappears upon click.
    legend_html = """
         <style>
            #div-to-toggle{
                z-index: 1;
                position: relative;
                border: 1px solid Black;
                padding: 15px 15px 15px 15px;
                margin: 20px auto;
                width: 90vw;
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
                width: 30vh;
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
            <br>
            Images of artwork were lovingly scraped from <a href="http://www.nycsca.org/Community/Public-Art-for-Public-Schools/Collection">the School Construction Authority</a>.
            </p>
            Created by <a href="https://talzaken.pythonanywhere.com" target="_blank">Tal Zaken</a>
        </div>
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
        <script>
            $('body, #close-btn').click(function() {
                $('#div-to-toggle').hide();
                event.stopPropagation();
            })
        </script>"""
    my_map.get_root().html.add_child(folium.Element(legend_html))

    # 7. Save the map to an HTML file
    my_map.save('DOEArt.html')
