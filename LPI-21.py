import gmaps
import matplotlib.pyplot as plt
import time
import numpy as np
import json
import geopy
import folium
from folium.plugins import HeatMap
import webbrowser
import os
import geojsoncontour
import branca
import scipy as sp
import scipy.ndimage

pint = "test"
fname = "Test Data/pints.txt"
webbrowser.register('chrome',
	None,
	webbrowser.BackgroundBrowser("C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"))

def add_pub(fname,name,lat,lon):
    with open(fname,'r') as f:
        pints = json.load(f)
    pints["test"][f'{name}'] = {}
    pints["test"][f'{name}']['lattitude'] = lat
    pints["test"][f'{name}']['longitude'] = lon
    pints["test"][f'{name}']['prices'] = []
    pints["test"][f'{name}']['times'] = []

    with open(fname,'w') as outfile:
        json.dump(pints,outfile)

def pub_finder(pint = "test",name = None):
    with open(fname,'r') as f:
        pints = json.load(f)
    if name == None:
        name = input("What's the pub called? ").lower()
    city = input("What city is the pub in? ")
    country = input("What country is the pub in? ")

    try:
        test = pints['test'][f'{name}']['prices'] 
        print("Already got it thanks!")
        return
    #geocoding
    except:
        pass

    search = ",".join([name,city,country])
    print(search)
    locator = geopy.Nominatim(user_agent = "Local Pint Index")
    
    try:
        location = locator.geocode(search)
        lat = location.latitude
        lon = location.longitude
        print(f'Latitude = {lat}, Longitude = {lon}')
    except:
        print("Shit, didnt find anything, try again?")
        try_again = input("(y/n)? ")
        if try_again == "y":
            pub_finder()
        
        return

    #map nonsense
    map1 = folium.Map(
        location = [lat,lon],
        tiles = 'cartodbpositron',
        zoom_start = 20)
    folium.Marker(
        [lat,lon], popup="<i>Correct?</i>", tooltip="Is this right?"
        ).add_to(map1)

    path = "map.html"
    map1.save(path)
    webbrowser.get('chrome').open_new_tab('file://'+os.getcwd()+"/" + "map.html")

    correct = input("Does this look right or not (y/n)? ")
    if correct == "n":
        print("oh no, you can try again or give direct longitude and latitude")
        print("1.Try Again\n2.Direct Input")
        choice = input()
        if choice == "1":
            pub_finder()
            return
        else:
            lat = input("Lattitude: ")
            lon = input("Longitude: ")

    add_pub("Test Data/pints.txt",name,lat,lon)

def add_price(name = None,pint = None):

    if pint == None:
        pint = input("What pint? ").lower()
    if name == None:
        name = input("What pub? ").lower()
        
    with open(fname,'r') as f:
        pints = json.load(f)
    #print(pints[f'{pint}'][f'{name}']['prices'])
    try:
        test = pints[f'{pint}'][f'{name}']['prices']
        price = round(float(input("Whats the price? ")),3)
        pints[f'{pint}'][f'{name}']['prices'].append(price)
        pints[f'{pint}'][f'{name}']['times'].append(time.time())
        with open(fname,'w') as outfile:
            json.dump(pints,outfile)
    except:
        print("Need to add a new pub")
        pub_finder(name = name)
        add_price(name = name, pint = pint)
#pub_finder()

def func(x,y,source):
    xi = source[0]
    yi = source[1]
    m = source[2]
    zi = m/np.sqrt((x-xi)**2+(y-yi)**2)
    return(zi)

def rgb(minimum, maximum, value):
    minimum, maximum = float(minimum), float(maximum)
    ratio = 2 * (value-minimum) / (maximum - minimum)
    #print("ratio:", ratio)
    b = int(max(0, 255*(1 - ratio)))
    r = int(max(0, 255*(ratio - 1)))
    g = 255 - b - r
    return [r/255, g/255, b/255]

def map_maker(pint = None):
    "A bit more mathematical"
    with open(fname,'r') as f:
        pints = json.load(f)
    if pint == None:
        pint = input("What pint? ").lower()
    Lat_c = []
    Lon_c = []
    sources = []
    prices = []
    for pub in pints[f'{pint}']:
        Lat = pints[f'{pint}'][pub]['lattitude']
        Lon = pints[f'{pint}'][pub]['longitude']
        P = np.mean(pints[f'{pint}'][pub]['prices'])
        prices.append(P)
        sources.append(np.array([Lat,Lon,P]))
        Lat_c.append(Lat)
        Lon_c.append(Lon)
    
    sources = np.array(sources)
    MLat = max(Lat_c) + 0.01
    mLat = min(Lat_c) -0.01 
    MLon = max(Lon_c) + 0.01
    mLon = min(Lon_c) -0.01
    x = np.linspace(mLat,MLat,40)
    y = np.linspace(mLon,MLon,40)

    
    X,Y = np.meshgrid(x,y)
    Z = func(X,Y,sources[0])
    for s in sources[1:]:
        z = func(X,Y,s)
        Z = np.add(Z,z)
        
    sigma = [1, 1]
    Z = sp.ndimage.filters.gaussian_filter(Z, sigma, mode='constant')
    
    colors = []
    vmin = min(prices) - np.std(prices)
    vmax = max(prices) + np.std(prices)
    
    for l in np.linspace(vmin,vmax,10):
        colors.append(rgb(vmin,vmax,l))
    levels = len(colors)
    cm = branca.colormap.LinearColormap(colors, vmin=vmin, vmax=vmax).to_step(levels)
    contourf = plt.contourf(Y,X,Z,colors = colors, linestyles = 'None',vmin = vmin, alpha = 0.5)
    #plt.show(contourf)
    
    geojson = geojsoncontour.contourf_to_geojson(contourf=contourf,fill_opacity = 0.5)
    
    #print(marker_map)
    Lat_c = np.mean(Lat_c)
    Lon_c = np.mean(Lon_c)
    sources = np.array(sources)
    max_price = np.max(sources,axis = 0)[2]

    
    #Map generation
    base = folium.Map(
        location = [Lat_c,Lon_c],
        zoom_start = 13)
    path = "templates/map.html"
    #HeatMap(data = marker_map,radius = 8,max_zoom = 15).add_to(base)
    
    folium.GeoJson(
        geojson,
        style_function=lambda x: {
            'color':     x['properties']['stroke'],
            'weight':    x['properties']['stroke-width'],
            'fillColor': x['properties']['fill'],
            'opacity':   0.6,
        }).add_to(base)
    cm.caption = 'Prices'
    base.add_child(cm)
    base.save(path)
    #webbrowser.get('chrome').open_new_tab('file://'+os.getcwd()+"/" + "map.html")
    
#####WEBSITE STUFF
from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/')
def map_display():
    return render_template("LocalPintIndex.html")

@app.route('/get_map')
def get_map():
    map_maker("test")
    return render_template("map.html")
if __name__ == "__main__":
    app.run(debug = False)
#gmapskey = "AIzaSyCbDd-Xt_qbOOzlyTe5ROjGUbUmFQIht0E"
#gmaps.configure(api_key = gmapskey)

#vector_map("test")
