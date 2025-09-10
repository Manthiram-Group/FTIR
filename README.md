In our lab we use a Thermo Scientific Nicolet iS50 FT-IR spectrometer equipped with PIKE VeeMax III for ATR experiments. We use python scripts for automatic data collection and spectra processing.
## Requirements

- Python 3.8+
- Packages:
  - `pandas`
  - `matplotlib`
  - `pybaselines`

Install:
```bash
pip install pandas matplotlib pybaselines
```
---

## Series spectra collection
spa_series.py is for collecting a series of spectra with fixed intervals.
### Usage
In the folder you want to store the raw data, run:
```bash
python ./spa_series.py
```
It will ask for the interval in seconds and how many times you want to collect. It will generate *.spa files which are the raw data file from collections, and corresponding *.csv files for future data processing.
### How it works
The script will first generate a macro file at every collection, which specify a series actions: collect one spectrum, save it as a processing.spa file, and save it as a processing.csv file.
The script will then start the collection by running the macro, and after it detects the processsing.spa file, it will rename the processsing.spa as "order.spa" and rename "processsing.csv" as order.csv, and enter the next cycle of collection.

---

## Data processing
All data processing functions are contained in the spectra_processing.py
### What it does

- **Combine** a folder of CSVs (assumed format: `wavenumber, intensity`) into:
  - `combined_raw.csv` — all raw intensities side-by-side
  - `referenced_raw.csv` — each intensity minus the **first** file’s intensity
- **Baseline-fit & subtract** using methods from `pybaselines`
- **Select** a wavenumber window and subset of columns
- **Plot** selected columns with cosmetic options and save a PNG

### Folder & data assumptions

- Place your input CSV files in a folder named **`raw/`** in the current working directory.
- Each CSV must have **two columns without headers**:
  1) wavenumber (x), 2) intensity (y).
- The **first CSV** (alphabetical/OS order) is used as the **reference** spectrum for subtraction.

> Tip: If your files have headers or different separators, adjust the `pd.read_csv(..., header=None)` line accordingly.

## Quick start

Run the script directly to generate combined and referenced matrices:

```bash
python spectra_processing.py
```

This calls `combining_series()` with the default `raw/` directory and writes:
- `combined_raw.csv`
- `referenced_raw.csv`



### Functions (API)

#### `combining_series()`
Combines all `.csv` files in `./raw` into two matrices:

- **Inputs:** none.
- **Outputs (files):**
  - `combined_raw.csv` with columns: `Wave number`, `<file1>`, `<file2>`, ...
  - `referenced_raw.csv` with columns: `Wave number`, `<file1_minus_ref>`, ...

#### `bkg_fitting(fitter, x, y)`
Fits a baseline to a single `y` series using `pybaselines`.

- **Parameters:**
  - `fitter`: one of `"modpoly"`, `"asls"`, `"mor"`, `"snip"`
  - `x`: 1D array-like of wavenumbers
  - `y`: 1D array-like of intensities
- **Returns:** `(bkg, params)` where `bkg` is the fitted baseline

#### `bkg_subtraction(df, fitter)`
Fit the background using the fitter specified and baseline-subtracts **all** y-columns in a DataFrame.

- **Parameters:**
  - `df`: DataFrame where first column is x (wavenumber), remaining columns are spectra
  - `fitter`: one of the baseline methods above
- **Returns:** new DataFrame with the same columns where y → `y - baseline`

#### `columns_selection(df, wave_range, cols)`
Extracts a wavenumber window and a subset of columns.

- **Parameters:**
  - `df`: input DataFrame (first column must be wavenumber)
  - `wave_range`: tuple `(xmin, xmax)`; if `None`, uses full range
  - `cols`: list of column **names** or indices
- **Side effect:** writes `selected_(xmin, xmax).csv`
- **Returns:** the filtered DataFrame

#### `plot_columns(df, xlim=None, ylim=None, reverse_x=True)`
Plots all y-columns vs. the first x-column and saves a PNG.

- **Parameters:**
  - `df`: DataFrame (first column is x)
  - `xlim`: `(xmin, xmax)` or `None` for full
  - `ylim`: `(ymin, ymax)` or `None`
  - `reverse_x`: `True` to invert the x-axis (common for wavenumber)
- **Outputs:**
  - Displays the plot
  - Saves `spectrum_(xlim).png`

### Example workflow (interactive)

```python
import pandas as pd

# 1) Combine and reference-correct
combining_series()
combined = pd.read_csv('combined_raw.csv')
referenced = pd.read_csv('referenced_raw.csv')

# 2) Select a region and subset of columns (e.g., columns 1..5)
sel = columns_selection(referenced, wave_range=(800, 1800), cols=[1,2,3,4,5])

# 3) Baseline subtract the selected region
sel_bkg = bkg_substraction(sel, fitter="asls")

# 4) Plot (Raman-style: decreasing wavenumber to the right)
plot_columns(sel_bkg, xlim=(800, 1800), reverse_x=True)
```

---

### Common pitfalls & tips

- **Column labels in plots:**  
  Legend label logic expects integer column names. Adjust if using filenames.
- **Wavelength window save name:**  
  `columns_selection` writes `selected_(xmin, xmax).csv`; edit code for cleaner naming.
- **Baseline parameters:**  
  The defaults (`lam`, `p`, `poly_order`, etc.) are generic. Tweak for your data.

---

### Acknowledgments

Baseline fitting uses the excellent [`pybaselines`](https://github.com/derb12/pybaselines) library.
