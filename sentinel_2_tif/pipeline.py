## imports ##
from datetime import datetime
from time import sleep
import os
import warnings
import pandas as pd
import numpy as np
import planetary_computer
import pystac_client
from   odc.stac import stac_load
import rioxarray as rxr
from rasterio.errors import NotGeoreferencedWarning, RasterioIOError, WarpOperationError
from tqdm.auto import tqdm


## tif_generator ##
def tif_generator(
    scene_search,                           # iterable of (bbox_polygon, "YYYY-MM-DD/YYYY-MM-DD")
    out_dir="./Collected TIFF Files",       # where to write GeoTIFFs
    stac_url="https://planetarycomputer.microsoft.com/api/stac/v1",
    collection="sentinel-2-l2a",
    cloud_lt=30,                            # max cloud cover %
    resolution_m=10,                        # meters-per-pixel
    crs="EPSG:4326",
    dtype="uint16",
    chunks={"x": 2048, "y": 2048},
    composite="median",                     # 'median' or 'mean'
    sign_items=True,                        # sign items explicitly (stac_load also supports patch_url)
    sleep_sec=0.0,                          # pause between requests to avoid rate limiting
    stop_after_first=False,                 # mimic your prior `break` after first successful write
    suppress_notgeo=True,                   # silence NotGeoreferencedWarning
    progress=True):                         # show tqdm progress
    """
    Pulls Sentinel-2 scenes (via Planetary Computer STAC) for each (bbox, time_window),
    composites them (median or mean), writes GeoTIFFs, and returns a summary.

    Parameters
    ----------
    scene_search : iterable of (Polygon, str)
        Each item is (bbox_polygon, "YYYY-MM-DD/YYYY-MM-DD").
    out_dir : str
        Output directory for GeoTIFF files.
    stac_url : str
        STAC endpoint (default: Planetary Computer).
    collection : str
        STAC collection (default: 'sentinel-2-l2a').
    cloud_lt : int
        Cloud cover threshold (percent).
    resolution_m : float
        Meters per pixel to scale (converted to degrees for EPSG:4326).
    crs : str
        Target CRS used for stac_load and for writing CRS metadata.
    dtype : str
        Dtype for the xarray.
    chunks : dict
        Dask chunking for xarray (stackstac).
    composite : str
        'median' or 'mean' compositing across time.
    sign_items : bool
        If True, sign items with planetary_computer.sign for robustness.
    sleep_sec : float
        Sleep between iterations to reduce rate limiting.
    stop_after_first : bool
        Stop after first successful write (mirrors your earlier behavior with `break`).
    suppress_notgeo : bool
        Suppress NotGeoreferencedWarning messages during write.
    progress : bool
        Show a tqdm progress bar.

    Returns
    -------
    dict
        {
          "written": [list of output file paths],
          "failed":  [(bbox, time_window, error_message), ...],
          "n_attempted": int,
          "n_written": int,
          "n_failed": int
        }
    """

    # --- setup ---
    os.makedirs(out_dir, exist_ok=True)

    if suppress_notgeo:
        warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

    # degrees per pixel for EPSG:4326
    scale_deg = resolution_m / 111_320.0

    stac = pystac_client.Client.open(url=stac_url)

    written = []
    failed = []

    iterable = list(scene_search)
    pbar = tqdm(iterable, desc="Scene pulls", unit="combo", disable=not progress)

    for idx, (bbox, time_window) in enumerate(pbar, start=1):
        bounds = bbox.bounds  # (minx, miny, maxx, maxy)
        pbar.set_postfix_str(f"window={time_window}")

        # STAC search
        search = stac.search(
            bbox=bounds,
            datetime=time_window,
            collections=[collection],
            query={"eo:cloud_cover": {"lt": cloud_lt}},
        )

        # .get_items() is deprecated
        scenes = list(search.items())

        # Quick progress line (non-intrusive with tqdm)
        tqdm.write(f"({idx}/{len(iterable)}) Found {len(scenes)} scenes for {time_window}")

        if len(scenes) == 0:
            failed.append((bbox, time_window, "No scenes found"))
            if sleep_sec:
                sleep(sleep_sec)
            continue

        # Load scenes → xarray
        try:
            data = stac_load(
                items=scenes,
                crs=crs,
                resolution=scale_deg,
                chunks=chunks,
                dtype=dtype,
                patch_url=planetary_computer.sign,  # implicit signing
                bbox=bounds,
            )
        except Exception as e:
            failed.append((bbox, time_window, f"stac_load error: {e}"))
            if sleep_sec:
                sleep(sleep_sec)
            continue

        # Optional explicit signing (belt & suspenders)
        if sign_items:
            try:
                scenes = [planetary_computer.sign(item) for item in scenes]
            except Exception as e:
                # proceed; usually patch_url handles this
                tqdm.write(f"Warning: signing failed ({e}); continuing.")

        # Composite
        try:
            if composite == "median":
                comp = data.median(dim="time")
            elif composite == "mean":
                comp = data.mean(dim="time")
            else:
                raise ValueError("composite must be 'median' or 'mean'")
        except Exception as e:
            failed.append((bbox, time_window, f"composite error: {e}"))
            if sleep_sec:
                sleep(sleep_sec)
            continue

        # Timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sentinel_{timestamp}.tif"
        out_path = os.path.join(out_dir, filename)

        # Attach some metadata
        comp.attrs["n_scenes"] = len(scenes)
        comp.attrs["t_window"] = time_window
        comp.attrs["c_method"] = composite
        comp.attrs["res_meters"] = resolution_m
        comp.attrs["res_degrees"] = scale_deg
        comp.attrs["timestamp"] = timestamp

        # Geo metadata + write
        try:
            tqdm.write("\tWriting CRS...")
            comp.rio.write_crs(input_crs=crs, inplace=True)

            tqdm.write("\tWriting transform (from loaded data)...")
            comp.rio.write_transform(data.rio.transform(), inplace=True)

            tqdm.write("\tSaving GeoTIFF...")
            comp.rio.to_raster(out_path)

            written.append(out_path)
            tqdm.write(f"\tDone: {out_path}")

            # Optional sanity check (silent if suppressed)
            is_geo = comp.rio.crs is not None and not comp.rio.transform().is_identity
            if not is_geo:
                tqdm.write(f"\tNote: {os.path.basename(out_path)} may not be georeferenced.")

            if stop_after_first:
                break

        except (RasterioIOError) as e:
            failed.append((bbox, time_window, f"raster write error: {e}"))
            # continue to next combo
        except Exception as e:
            failed.append((bbox, time_window, f"unexpected write error: {e}"))
            # continue

        # Rate-limit politeness
        if sleep_sec:
            sleep(sleep_sec)

    summary = {
        "written": written,
        "failed": failed,
        "n_attempted": len(iterable),
        "n_written": len(written),
        "n_failed": len(failed),
    }

    if progress:
        tqdm.write(
            f"Complete: {summary['n_written']} written, {summary['n_failed']} failed "
            f"out of {summary['n_attempted']}."
        )

    return summary