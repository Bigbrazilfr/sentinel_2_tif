## imports ##
from itertools import product
from math import cos, radians

## st_grid ##
def st_grid(mbr, buffers, wrap_sizes, event_date, as_records=False, compute_area=False, verbose=False):
    """
    Creates a spaciotemporal list of bounding box-time window combinations
    around an event date using a Cartesian product.

    PARAMETERS
    ----------
    mbr : shapely.geometry.Polygon
        A rectangular polygon (typically from the `mbr()` function).
    
    buffers : list, range, or similar iterable object
        Buffer sizes (in km) to expand around the MBR.
    
    wrap_sizes : list, range, or similar iterable object
        Time window sizes (in weeks) to wrap around the event date. For
        example, a value of 2 will generate a window from two weeks before to
        two weeks after the event (total of four weeks).
    
    event_date : datetime-like or str
        The central event date. See pd.to_datetime() for more details on
        acceptable formats.
    
    as_records : bool, default True
        If True, return a list of dictionaries with metadata.
        If False, return a list of (Polygon, time_window) tuples.
    
    compute_area : bool, default False
        If True, also compute an approximate area in km² for each bounding box.
    
    verbose : bool, default False
        If True, prints a summary of how many combinations were created.

    RETURNS
    -------
    List
        Either a list of dicts (if as_records=True) or a list of tuples.
    
    SEE ALSO
    --------
    mbr_buffers : Creates multiple buffered bounding boxes.
    time_windows : Creates multiple time windows.
    tif_generator : Generates .tif files based on the results of bw_grid.
    """

    # instantiating bounding boxes and time windows
    bbox_list = mbr_buffers(mbr=mbr, buffers=buffers)
    window_list = time_windows(event_date=event_date, wrap_sizes=wrap_sizes)
    
    # placeholder list
    results = []
    
    # running cross (Cartesian) product (might revert back to my loop)
    for poly, window in product(bbox_list, window_list):
        if as_records:
            record = {
                "buffer_km": buffers[bbox_list.index(poly)],
                "weeks": wrap_sizes[window_list.index(window)],
                "bbox": poly,
                "time_window": window
            }

            if compute_area:
                minx, miny, maxx, maxy = poly.bounds
                mid_lat = (miny + maxy) / 2
                m_per_deg_lat = 111_320
                m_per_deg_lon = 111_320 * cos(radians(mid_lat))
                width_m = (maxx - minx) * m_per_deg_lon
                height_m = (maxy - miny) * m_per_deg_lat
                record["area_km2"] = (width_m * height_m) / 1_000_000

            results.append(record)
        else:
            results.append((poly, window))
            
    # optional feedback while processing
    if verbose:
        print(f"{len(results)} bounding box–time window combinations created "
              f"({len(buffers)} buffers × {len(wrap_sizes)} windows).")
        
    # returning results
    return results