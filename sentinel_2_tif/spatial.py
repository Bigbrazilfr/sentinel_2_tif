## imports ##
from shapely.geometry import box
import pandas as pd
from shapely.geometry import box
from math import cos, radians
from collections.abc import Iterable
import numbers

## mbr ##
def mbr(data=None, 
        lat_col='Latitude', 
        lon_col='Longitude', 
        north=None, 
        south=None, 
        east=None, 
        west=None):
    """
    Creates a Minimum Bounding Rectangle (MBR) from one of the following:
        * A DataFrame (default)
        * A dictionary of lat/lon coordinates
        * Explicit boundary coordinates (north, south, east, west)
    
    PARAMETERS
    ----------
    data : pd.DataFrame or dict, optional
        A DataFrame or dictionary containing latitude and longitude
        coordinates.
    
    lat_col : str, default 'Latitude'
        The name of the latitude column or dictionary key.

    lon_col : str, default 'Longitude'
        The name of the longitude column or dictionary key.

    north, south, east, west : float, optional
        Explicitly specified boundary coordinates. If all four are provided,
        `data` is ignored.

    RETURNS
    -------
    shapely.geometry.Polygon
        A rectangular polygon representing the minimum bounding box.

    EXAMPLES
    --------
    >>> mbr(df, lat_col='lat', lon_col='lon')
    >>> mbr({'Latitude': [37, 38], 'Longitude': [-122, -121]})
    >>> mbr(north=38, south=37, east=-121, west=-122)

    SEE ALSO
    --------
    mbr_buffer : creates a symmetric buffer around an MBR.
    mbr_buffers : creates multiple symmetric buffers around an MBR.
    """

    # using explicit boundaries (if provided)
    if None not in (north, south, east, west):
        
        # returning mbr boundaries (explicit)
        return box(minx=west, miny=south, maxx=east, maxy=north)

    # using DataFrame (if provided)
    if isinstance(data, pd.DataFrame):
        
        lat = data[lat_col]
        lon = data[lon_col]

    # using dictionary (if provided)
    elif isinstance(data, dict):
        try:
            lat = data[lat_col]
            lon = data[lon_col]
            
        # throwing error if dict keys format is incorrect
        except KeyError:
            
            raise ValueError(f"Dictionary must contain keys: '{lat_col}' and '{lon_col}'")

    # throwing error if data format is incorrect
    else:
        raise ValueError("Please provide either a DataFrame/dict OR all four boundaries (north, south, east, west)")

    # computing boundaries
    north = max(lat)
    south = min(lat)
    east  = max(lon)
    west  = min(lon)

    # returning mbr boundaries (df or dict)
    return box(minx=west, miny=south, maxx=east, maxy=north)



## mbr buffer ##
def mbr_buffer(mbr, km=1):
    """
    Creates a symmetric buffer (in kilometers) around a bounding box,
    converting km into degrees for both latitude and longitude using local
    approximations.
    
    This is different from shapely.buffer, which expresses buffer size in
    directly in degrees (not ideal for longitudes far away from the Equator).

    PARAMETERS
    ----------
    mbr : shapely.geometry.polygon.Polygon
        A rectangular polygon (typically from the `mbr()` function).
    
    km : float, default 1
        Buffer size in kilometers (non-diagonal, axis-aligned).

    RETURNS
    -------
    shapely.geometry.Polygon
        A new rectangular polygon with expanded bounds.
        
    EXAMPLES
    --------
    >>> mbr = box(minx=-123.0, miny=37.0, maxx=-121.0, maxy=38.5)
    >>> mbr_buffer(mbr, km=10))
    
    SEE ALSO
    --------
    mbr : Creates a minimum bounding rectangle (MBR).
    mbr_buffers : creates multiple symmetric buffers around an MBR.
    """
    
    # extracting bounds
    minx, miny, maxx, maxy = mbr.bounds

    # converting km to degrees latitude (approx. constant)
    lat_buffer_deg = (km * 1000) / 111_320

    # calculating average latitude for local longitude degree conversion
    avg_lat = (miny + maxy) / 2
    lon_buffer_deg = (km * 1000) / (111_320 * cos(radians(avg_lat)))

    # returning buffered bounding box
    return box(
        minx=minx - lon_buffer_deg,
        miny=miny - lat_buffer_deg,
        maxx=maxx + lon_buffer_deg,
        maxy=maxy + lat_buffer_deg
    )


## mbr_buffers ##
def mbr_buffers(mbr, buffers, verbose=False):
    """
    Creates multiple symmetric buffers (in kilometers) around a bounding box.

    This wraps `mbr_buffer()` in a loop to create a list of bounding boxes
    with varying buffer distances.

    PARAMETERS
    ----------
    mbr : shapely.geometry.Polygon
        A rectangular polygon (typically from the `mbr()` function).
    
    buffers : iterable object float or int values
        List, range, or other iterable of buffer distances (in km).
    
    verbose : bool, default False
        If True, prints each buffer level as it's added.

    RETURNS
    -------
    List[shapely.geometry.Polygon]
        A list of buffered rectangles, in the same order as `buffers`.
    
    EXAMPLES
    --------
    >>> mbr = box(minx=-123.0, miny=37.0, maxx=-121.0, maxy=38.5)
    >>> mbr_buffers(mbr, [1, 5, 10])

    SEE ALSO
    --------
    mbr          : Generates a bounding box from coordinates.
    mbr_buffer   : Expands a bounding box by a fixed distance.
    """

    # throwing error if buffers is not iterable
    if not isinstance(buffers, Iterable):
        raise ValueError("`buffers` must be an iterable of numeric values.")
    
    # placeholder list
    buffer_lst = []
    
    # looping over provided buffers
    for b in buffers:
        
        # throwing error if dict keys format is incorrect
        if not isinstance(b, numbers.Real):
            raise ValueError(f"Buffer value '{b}' is not a number.")
        
        # running mbr_buffer and appending results
        buffered_mbr = mbr_buffer(mbr, km=b)
        buffer_lst.append(buffered_mbr)
        
        # optional feedback while processing
        if verbose:
            print(f"Buffer {b} km added.")
            
    # returning list of buffers
    return buffer_lst
