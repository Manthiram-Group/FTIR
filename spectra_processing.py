import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from pybaselines import Baseline, utils

def combining_series():
    # Set the directory containing your CSV files

    #csv_dir = 'path/to/your/csv_files'
    csv_dir = os.getcwd()+'/raw'
    output_combined_file = 'combined_raw.csv'
    output_referenced_file = 'referenced_raw.csv'

    # Get list of all CSV files in the directory
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    csv_files.sort()  # Optional: ensure consistent order

    combined_raw_df = pd.DataFrame()
    referenced_raw_df = pd.DataFrame()

    for idx, file in enumerate(csv_files):
        file_path = os.path.join(csv_dir, file)
        df = pd.read_csv(file_path, header=None)

        # For the first file, take both columns: wave number and intensity
        if idx == 0:
            wavenumber = df.iloc[:, 0]
            reference = df.iloc[:, 1]
            combined_raw_df['Wave number'] = wavenumber
            #combined_bkg_subtracted_df['wave number'] = wavenumber
            referenced_raw_df['Wave number'] = wavenumber
            #referenced_bkg_subtracted_df['wave number'] = wavenumber

        combined_raw_df[file.replace('.csv', '')] = df.iloc[:, 1]

        # Use the first file as the reference for substracting others
        referenced_raw_df[file.replace('.csv', '')] = df.iloc[:, 1] - reference

    # Write combined dataframe to a new CSV
    combined_raw_df.to_csv('combined_raw.csv', index=False)
    referenced_raw_df.to_csv('referenced_raw.csv', index=False)


def bkg_fitting(fitter,x,y):
    baseline_fitter = Baseline(x_data=x)

    if fitter == "modpoly":
        bkg, params = baseline_fitter.modpoly(y, poly_order=5)
    elif fitter == "asls":
        bkg, params = baseline_fitter.asls(y, lam=1e7, p=0.02)
    elif fitter == "mor":
        bkg, params = baseline_fitter.mor(y, half_window=30)
    elif fitter == "snip":
        bkg, params = baseline_fitter.snip(y, max_half_window=40, decreasing=True, smooth_half_window=3)
    return bkg, params

def bkg_subtraction(df,fitter):

    df_bkg_subtracted = pd.DataFrame()
    x = df.iloc[:,0]
    df_bkg_subtracted['Wave number'] = x

    for col in df.columns[1:]:
        y = df[col]
        bkg, params = bkg_fitting(fitter,x,y) # fit data with selected fitter
        df_bkg_subtracted[col] = y - bkg
    #df_bkg_subtracted.to_csv(f"selected_bkg_subtracted.csv", index=False)
    return df_bkg_subtracted

def columns_selection(df,wave_range,cols):
    # Select specific columns to perform the baseline correction

    #select proper range of wave number
    if wave_range is not None:
        df_wave_selected = df[(df["Wave number"] > wave_range[0]) & (df["Wave number"] < wave_range[1]) ]
    else:
        df_wave_selected = df

    df_selected = pd.DataFrame()
    x = df_wave_selected.iloc[:,0]
    df_selected['Wave number'] = x

    for col in cols:
        if isinstance(col, int):
            if col < 0 or col >= df.shape[1]:
                raise IndexError(f"Column index {col} is out of range.")
            df_selected[df_wave_selected.columns[col]] = df_wave_selected.iloc[:, col]

        else:
            if col not in df.columns:
                raise KeyError(f"Column '{col}' not found in DataFrame.")
            df_selected[col] = df_wave_selected[col]

    df_selected.to_csv(f"selected_{wave_range}.csv", index=False)

    return df_selected

def plot_columns(df, xlim=None, ylim=None, reverse_x=True):
    """
    Plot selected columns of a DataFrame against the first column.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame; the first column is used as x-axis.
    cols : list[str|int]
        Column names or indices to plot as y-series.
    xlim : tuple[float,float] | None
        (xmin, xmax) range. Defaults to full range of x.
    reverse_x : bool
        If True, reverse the x-axis direction.

     Returns
    -------
    matplotlib.axes.Axes
        The Axes object of the plot.
    """

    x = df.iloc[:, 0]
    x_label = "Wavenumber (cm$^{-1}$)" #df.columns[0]

    fig, ax = plt.subplots(figsize=(5,4))

    # Plot each requested column
    for col in df.columns[1:]:
        y = df[col]
        label = "%d min" %(int(col)*10) # 10 min interval
        ax.plot(x, y, label=label)

    # Labels & legend
    ax.set_xlabel(x_label)
    ax.set_ylabel("Absorbance (A.U.)")  # empty since you don't want y numbers; title can be set outside
    ax.set_yticklabels([]) # Remove y-axis numbers
    ax.legend(frameon=False)

    # Minor ticks on x only (cleaner than ax.minorticks_on for both axes)
    ax.xaxis.set_minor_locator(AutoMinorLocator(n=2))

    # X range (default to full)
    if xlim is not None:
        ax.set_xlim(xlim)
    else:
        ax.set_xlim(float(x.min()), float(x.max()))

    # y range (default to full)
    if ylim is not None:
        ax.set_ylim(ylim)
    else:
        ax.set_ylim(float(y.min()), float(y.max()))

    # Reverse x direction if requested
    if reverse_x:
        ax.invert_xaxis()

    plt.tight_layout()
    plt.show()

    fig.savefig(f"spectrum_{xlim}.png", dpi=300, bbox_inches="tight")
    # return ax

if __name__ == "__main__":
    combining_series()
