import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from pybaselines import Baseline  # utils unused

# ---------- helpers ----------

def _natural_key(s: str):
    # e.g., "10.csv" > "2.csv" becomes False; sorts numerically where possible
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

def _minutes_from_name(name: str):
    """
    Try to extract minutes from a column/file name.
    Matches e.g. 't12', '12min', '12 m', 'file_12', etc. Returns int or None.
    """
    m = re.search(r'(\d+)\s*(?:min|m)?\b', name, flags=re.I)
    return int(m.group(1)) if m else None

# ---------- core pipeline ----------

def combining_series(csv_dir=None,
                     output_combined_file='combined_raw.csv',
                     output_referenced_file='referenced_raw.csv',
                     skip_first_in_reference=False):
    """
    Combine all 2-column CSVs in `csv_dir` into:
      - combined_raw.csv: first column = Wavenumber, others = raw intensities
      - referenced_raw.csv: each column minus the first file's intensity (reference)
    Assumes every CSV has 2 columns: [wavenumber, intensity].
    """
    if csv_dir is None:
        csv_dir = os.path.join(os.getcwd(), 'raw')

    if not os.path.isdir(csv_dir):
        raise FileNotFoundError(f"Directory does not exist: {csv_dir}")

    csv_files = sorted([f for f in os.listdir(csv_dir) if f.lower().endswith('.csv')],
                       key=_natural_key)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {csv_dir}")

    combined_raw_df = pd.DataFrame()
    referenced_raw_df = pd.DataFrame()

    reference = None
    for idx, file in enumerate(csv_files):
        file_path = os.path.join(csv_dir, file)
        df = pd.read_csv(file_path, header=None)
        if df.shape[1] < 2:
            raise ValueError(f"{file} must have at least 2 columns (wavenumber, intensity)")

        # first file defines x and reference spectrum
        if idx == 0:
            wavenumber = df.iloc[:, 0].astype(float)
            reference = df.iloc[:, 1].astype(float).copy()
            combined_raw_df['Wavenumber'] = wavenumber
            referenced_raw_df['Wavenumber'] = wavenumber

        col_name = os.path.splitext(file)[0]
        y = df.iloc[:, 1].astype(float)

        combined_raw_df[col_name] = y

        if idx == 0 and skip_first_in_reference:
            referenced_raw_df[col_name] = y  # leave as-is if you prefer
        else:
            referenced_raw_df[col_name] = y - reference

    combined_raw_df.to_csv(output_combined_file, index=False)
    referenced_raw_df.to_csv(output_referenced_file, index=False)

    return combined_raw_df, referenced_raw_df


def bkg_fitting(fitter, x, y):
    baseline_fitter = Baseline(x_data=x)

    if fitter == "modpoly":
        bkg, params = baseline_fitter.modpoly(y, poly_order=5)
    elif fitter == "asls":
        bkg, params = baseline_fitter.asls(y, lam=1e7, p=0.02)
    elif fitter == "mor":
        bkg, params = baseline_fitter.mor(y, half_window=30)
    elif fitter == "snip":
        bkg, params = baseline_fitter.snip(y, max_half_window=40, decreasing=True, smooth_half_window=3)
    else:
        raise ValueError(f"Unknown fitter '{fitter}'. Use one of: modpoly, asls, mor, snip.")
    return bkg, params


def bkg_substraction(df, fitter):
    """
    Baseline-subtract all y columns in df (first column must be x).
    Returns a new DataFrame with the same columns.
    """
    df_bkg_subtracted = pd.DataFrame()
    x = df.iloc[:, 0].astype(float)
    df_bkg_subtracted[df.columns[0]] = x

    for col in df.columns[1:]:
        y = df[col].astype(float)
        bkg, _ = bkg_fitting(fitter, x, y)  # fit data with selected fitter
        df_bkg_subtracted[col] = y - bkg

    return df_bkg_subtracted


def columns_selection(df, wave_range, cols):
    """
    Select wavelength range and specific columns by index or name.
    `wave_range`: tuple (xmin, xmax) inclusive; pass None for full range.
    `cols`: list of indices or names (excluding the first x column).
    """
    # select range (inclusive)
    if wave_range is not None:
        x = df.iloc[:, 0]
        mask = (x >= min(wave_range)) & (x <= max(wave_range))
        df_wave = df.loc[mask].copy()
    else:
        df_wave = df.copy()

    df_selected = pd.DataFrame()
    df_selected[df_wave.columns[0]] = df_wave.iloc[:, 0].astype(float)

    for col in cols:
        if isinstance(col, int):
            if col < 0 or col >= df.shape[1]:
                raise IndexError(f"Column index {col} is out of range.")
            df_selected[df_wave.columns[col]] = df_wave.iloc[:, col].astype(float)
        else:
            if col not in df_wave.columns:
                raise KeyError(f"Column '{col}' not found.")
            df_selected[col] = df_wave[col].astype(float)

    # safer filename from range
    fname_range = f"{min(df_selected.iloc[:,0]):.0f}-{max(df_selected.iloc[:,0]):.0f}" if wave_range else "full"
    df_selected.to_csv(f"selected_{fname_range}.csv", index=False)

    return df_selected


def plot_columns(df, xlim=None, ylim=None, reverse_x=True, title=None):
    """
    Plot all y-columns of `df` against the first x-column.
    """
    x = df.iloc[:, 0].astype(float)
    x_label = "Wavenumber (cm$^{-1}$)"

    fig, ax = plt.subplots(figsize=(5, 4))

    ymins, ymaxs = [], []
    for col in df.columns[1:]:
        y = df[col].astype(float)
        # friendly legend: try to derive minutes; fallback to raw name
        maybe_min = _minutes_from_name(str(col))
        label = f"{maybe_min} min" if maybe_min is not None else str(col)
        ax.plot(x, y, label=label)
        ymins.append(y.min()); ymaxs.append(y.max())

    ax.set_xlabel(x_label)
    ax.set_ylabel("Absorbance (A.U.)")
    ax.yaxis.set_tick_params(labelleft=False)  # hide numbers but keep ticks if desired
    ax.legend(frameon=False, ncol=2)

    ax.xaxis.set_minor_locator(AutoMinorLocator(n=2))

    # X range
    if xlim is not None:
        ax.set_xlim(xlim)
    else:
        ax.set_xlim(float(x.min()), float(x.max()))

    # Y range across all series
    if ylim is not None:
        ax.set_ylim(ylim)
    else:
        if ymins and ymaxs:
            ax.set_ylim(min(ymins), max(ymaxs))

    if reverse_x:
        ax.invert_xaxis()

    if title:
        ax.set_title(title)

    plt.tight_layout()

    # build a tidy filename
    x0, x1 = ax.get_xlim()
    out_png = f"spectrum_{int(min(x0, x1))}-{int(max(x0, x1))}.png"
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return out_png


if __name__ == "__main__":
    # Example minimal flow (adjust as needed)
    combined_raw_df, referenced_raw_df = combining_series()
    # e.g., select first 5 spectra across 800–1800 cm^-1 (inclusive)
    sel = columns_selection(referenced_raw_df, wave_range=(800, 1800), cols=list(range(1, 6)))
    sel_bkg = bkg_substraction(sel, fitter="asls")
    plot_columns(sel_bkg, xlim=(800, 1800), reverse_x=True, title="Baseline-corrected (ASLS)")
