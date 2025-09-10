In our lab we used a Thermo Scientific Nicolet iS50 FT-IR spectrometer equipped with PIKE VeeMax III for ATR experiments.

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

## Data processing
