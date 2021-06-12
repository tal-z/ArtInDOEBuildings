import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib

def scrape_art():
    """Combs through the NYC School Construction Authority website, and gathers links for images of artwork in schools.
    Returns a dataframe with the link formatted as an html image tag."""
    count = 0
    art_links_df = pd.DataFrame(columns=['artist', 'borough', 'school', 'title', 'image'])
    for page_num in range(1, 24):
        html_data = requests.get(
            f"http://www.nycsca.org/Community/Public-Art-for-Public-Schools/Collection/pageindex2506/{page_num}").text

        soup = BeautifulSoup(html_data, 'html.parser')
        for photo, info in zip(soup.find_all("div", {"class": "gallery_photo"})[:10],
                               soup.find_all("div", {"class": "gallery_info"})[:10]):
            info_summary = info.findChildren("div", {"class": "item_summary"}, recursive=False)
            artist = info.h3.getText().strip().upper()
            title = info_summary[0].p.i.getText().strip().upper()
            school = str(info_summary[0].p).split("<br/>")[-3].strip().upper()
            borough = info.findChildren("div", {"class": "item_category"}, recursive=False)[0].a.getText().upper()
            photo_link = 'http://www.nycsca.org' + photo.findChildren('a', recursive=False)[0].img['src']
            urllib.request.urlretrieve(photo_link, f"ArtImages/{artist}_{title}.jpg")
            photo_tag = f"<img src='/static/maps/ArtImages/{artist}_{title}.jpg'/>"
            count += 1
            print(count)
            print(artist, borough, school, title, photo_tag, sep='\n')
            art_links_df = art_links_df.append(
                {'artist': artist, 'borough': borough, 'school': school, 'title': title, 'image': photo_tag},
                ignore_index=True)
    return art_links_df


