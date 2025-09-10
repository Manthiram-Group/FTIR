import os
import glob
import win32com.client
import win32api
import time

def generate_macro(sample_name: str):
    content = f"""OmnicMacroFile Version 10.0,
caption,Macros\\Basic - collect.mac
>pName,collect.mac
>pComments,
>pAuthor,Haochen Zhang
>pReset,true
>pFormat,?
§
send updateReadout "Open Experiment", 1
send executeOmnic "[LoadParameters " & getRTSFN("C:\\my documents\\omnic\\Param\\Haochen_Default.exp") & "]"
send updateReadout "Collect Sample", 2
send enableApp false
send executeOmnic "[Invoke CollectSample ""spectrum_{sample_name}"" AUTO POLLING]"
send waitOnInvoke "CollectSample"
send updateReadout "Save As", 3
send executeOmnic "[Export " & getRTSFN("processing.csv") & "]"
send updateReadout "Save As", 4
send executeOmnic "[Export " & getRTSFN("processing.spa") & "]"
sysError = "ok"
send updateReadout
§
false
§
Button,Open Experiment
strokeColor,240,50,100
>pTaskType,3
>pAlias,LoadParameters
>pParamList,"C:\\my documents\\omnic\\Param\\Haochen_Default.exp",false,1,1,1,1
¡endTask!
Button,Collect Sample
strokeColor,240,50,100
>pTaskType,3
>pAlias,CollectSample
>pParamList,"spectrum_{sample_name}",true,false,false
¡endTask!
Button,Save As
strokeColor,240,50,100
>pTaskType,3
>pAlias,SaveAs
>pParamList,"processing.csv",false
¡endTask!
Button,Save As
strokeColor,240,50,100
>pTaskType,3
>pAlias,SaveAs
>pParamList,"processing.spa",false
¡endTask!
§
"""
    with open("collect.mac", "w", encoding="ansi") as f:
        f.write(content)

    print(f"Macro file “collect.mac” generated with sample name: spectrum_{sample_name}")


def run_omnic_macro():
    try:
        # Connect to Omnic using the correct COM interface
        OmApp = win32com.client.Dispatch("OmnicApp.OmnicApp")
        collect_path = os.path.abspath("collect.mac")
        short_path = win32api.GetShortPathName(collect_path)
        # print(short_path)
        OmApp.ExecuteCommand(f"RunMacro {short_path}")
        # print("Collecting the spectrum...")
        return True
    except Exception as e:
        print(f"ERROR running macro: {e}")
        return False

def rename_spa(i):
    # Get all .SPA files in the current directory
    spa_files = glob.glob("processing.spa")
    if not spa_files:
        print("WARNING: No processing.spa file found in the current directory")
        return
    # Process each .SPA file
    try:
        #name = str(i) + ".SPA"
        name = "%04d" %i + ".spa"
        os.rename("processing.spa", name)
        #time.sleep(2)
        print(f"Completed processing {name}")

    except FileNotFoundError as e:
        print(f"ERROR: File not found - {e}")
    except PermissionError as e:
        print(f"ERROR: Permission denied - {e}")
    except Exception as e:
        print(f"ERROR processing {spa_files}: {e}")

def rename_csv(i):
    # Get all .SPA files in the current directory
    csv_files = glob.glob("processing.csv")

    if not csv_files:
        print("WARNING: No processing.csv file found in the current directory")
        return
    # Process each .csv file
    try:
        name = "%04d" %i + ".csv"
        os.rename("processing.csv", name)
        #time.sleep(2)
        print(f"Completed processing {name}")

    except FileNotFoundError as e:
        print(f"ERROR: File not found - {e}")
    except PermissionError as e:
        print(f"ERROR: Permission denied - {e}")
    except Exception as e:
        print(f"ERROR processing {csv_files}: {e}")

def countdown(total_seconds: int):
    while total_seconds >= 0:
        mins, secs = divmod(total_seconds, 60)
        print(f"Waiting {mins:02}:{secs:02} for next collection...", end="\r", flush=True)
        time.sleep(1)
        total_seconds -= 1
    print(" " * 62, end="\r", flush=True)

def time_formatting(total_seconds):
        hrs, remainder = divmod(round(total_seconds), 3600)
        mins, secs = divmod(remainder, 60)
        return (hrs,mins,secs)

def run_series():
    try:
        #print("Must run within a folder containing collect.mac")
        # Get user input
        interval_seconds = float(input("Enter the interval between each collection in seconds: "))
        times = int(input("Enter how many spectra to acquire in total: "))

        # Validate input
        #if interval_seconds < 60:
        #    print("ERROR: Interval must be greater than 60 s")
        #    return
        if times <= 0:
            print("ERROR: Number of times must be greater than 0")
            return

        # Convert interval seconds to mins+secs
        hrs, mins, secs = time_formatting(interval_seconds)
        # Convert total amount of time to hrs+mins+secs
        thrs, tmins, tsecs = time_formatting(interval_seconds*(times-1))

        print(f"\nStarting spectrum collection:")
        print(f"Interval: {mins} minutes {secs} seconds")
        print(f"Total collection number: {times}")
        print(f"Estimated total time: {thrs} hours {tmins} minutes {tsecs} seconds")
        print("-" * 68)

        next_start_time = time.time()
        # Run the function the specified number of times
        for i in range(times):
            # Double confirm that the start time
            now = time.time()
            if now < next_start_time:
                time.sleep(next_start_time - now)

            print(f"\nCollection {i + 1}/{times}:")

            #generate the macro file with order name
            generate_macro("%04d" %i)

            run_omnic_macro()

            # Wait until file output processing.spa is detected (macro finish)
            while True:
                for dots in range(4):  # 0 to 3 dots, check the existence of processing.spa every 2s
                    print(f"Collecting the spectrum{'.' * dots}   ", end="\r", flush=True)
                    time.sleep(0.66666667)
                # time.sleep(2)
                if os.path.exists("processing.spa"):
                    print(f"Output file processing.spa detected,the collection has finished")
                    time.sleep(1) #just to be safe that all the files are generated.
                    rename_spa(i)
                    rename_csv(i)
                    break

            if i < (times-1): #before the last collection, prepare for the next run after each collection.
                duration_of_one_run = time.time()-next_start_time

                # Calculate how much time remaining
                remaining_time=(times-i-1)*interval
                rhrs, rmins, rsecs = time_formatting(remaining_time)
                print(f"Estimated remaining time: {rhrs} hours {rmins} minutes {rsecs} seconds")

                if interval_seconds- duration_of_one_run > 0:
                # Counting down how much time is left by susctracting the time elapsed from time interval
                # Stop counting at 00:01, so that the time interval is not controlled by the counting down
                    countdown(int(interval_seconds-duration_of_one_run)-1)
                else:
                    print("WARNING: Single collection time is longer than the set interval")
                    #setting the new interval as the measured time interval:
                    interval_seconds =  duration_of_one_run
                    print(f"Time interval now is {round(interval_seconds)} seconds")

                # Schedule next start time based on fixed interval
                next_start_time += interval_seconds

        print(f"\nCompleted all {times} collections!")

    except ValueError:
        print("ERROR: Please enter valid numbers")
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    run_series()
