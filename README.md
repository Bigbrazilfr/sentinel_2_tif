# sentinel_2_tif

**sentinel_2_tif** is a Python package that simplifies the process of generating georeferenced `.tif` imagery from Sentinel-2 L2A scenes. It provides tools for spatial buffering, time window selection, scene compositing, and automatic `.tif` file generation via Microsoft’s Planetary Computer STAC API.

---

## 🚀 Features

- 🛰️ Access Sentinel-2 L2A imagery via Planetary Computer
- 🗺️ Automatically generate bounding box buffers in kilometers
- 📆 Create symmetric time windows around an event date
- ⚡ Composite scenes using `median` or `mean`
- 🌍 Save georeferenced `.tif` outputs with full metadata
- 🧰 Designed for both notebook and production workflows

---

## 📦 Installation

Clone the repo and install in development mode:

```bash
git clone https://github.com/yourusername/sentinel_2_tif.git
cd sentinel_2_tif
pip install -e .
```

Or create an isolated conda environment:

```bash
conda env create -f environment.yml
conda activate sentinel_2_tif
```

---

## 🧪 Example Usage

```python
from sentinel_2_tif.spatial import mbr_buffer, mbr_buffers
from sentinel_2_tif.temporal import time_wrapper, time_windows
from sentinel_2_tif.search import st_grid
from sentinel_2_tif.pipeline import tif_generator
from shapely.geometry import box

# Define MBR manually or from points
bbox = box(minx=-123.0, miny=37.0, maxx=-121.0, maxy=38.5)

# Generate a grid of spatial + temporal search combinations
scene_search = st_grid(
    mbr=bbox,
    buffers=[0, 5, 10],
    wrap_sizes=[2, 6],
    event_date="2022-08-07",
    as_records=False
)

# Pull scenes, generate composite .tif(s)
summary = tif_generator(
    scene_search=scene_search,
    composite="median",
    out_dir="./Collected TIFF Files"
)
```

---

## 📁 Package Modules

- `spatial`: MBR buffer generation
- `temporal`: Time window utilities
- `search`: Spatial-temporal search grid builder
- `pipeline`: Scene extraction and `.tif` writer

---

## 📝 License

MIT License. See [LICENSE](LICENSE) for details.
