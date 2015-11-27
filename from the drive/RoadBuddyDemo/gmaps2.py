import numpy as np
from IPython import display
from bokeh.embed import file_html
from bokeh.models.glyphs import Circle
from bokeh.models import (
    GMapPlot, Range1d, ColumnDataSource,
    PanTool, WheelZoomTool, BoxSelectTool,
    BoxSelectionOverlay, GMapOptions)
from bokeh.resources import INLINE

def drawMap(title, datas, point_size=6, alpha=0.5):
    """
    color : [(lat, lon)]
    """ 
    lat = []
    lon = []
    c = []
    
    for color in datas:
        c_lat, c_lon = zip(*datas[color])
        #print (c_lat)
        lat.extend(map(float, c_lat))
        lon.extend(map(float, c_lon))
        c.extend([color]*len(datas[color]))
        
    center_lat = np.median(lat)
    center_lon = np.median(lon)

    x_range = Range1d()
    y_range = Range1d()
    
    source = ColumnDataSource(
        data=dict(
            lat=lat,
            lon=lon,
            fill=c
        )
    )

    map_options = GMapOptions(lat=center_lat, lng=center_lon, map_type="roadmap", zoom=13)
    plot = GMapPlot(
        x_range=x_range, y_range=y_range,
        map_options=map_options,
        title=title
    )

    # Glyphs (dots on graph)
    circle = Circle(x="lon", y="lat", size=point_size, line_width=0, fill_color="fill", fill_alpha=alpha, line_alpha=0.0)
    plot.add_glyph(source, circle)

    #Navigation
    pan = PanTool()
    wheel_zoom = WheelZoomTool()
    box_select = BoxSelectTool()

    plot.add_tools(pan, wheel_zoom, box_select)
    overlay = BoxSelectionOverlay(tool=box_select)
    plot.add_layout(overlay)

    return display.HTML(file_html(plot, INLINE, "Google Maps Example"))