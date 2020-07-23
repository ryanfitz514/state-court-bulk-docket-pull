import user_tools
import os
import login
import json
import threading
import requests
import global_variables
import pandas as pd
import time
import concurrent.futures
from tqdm import tqdm
import log_errors_to_table
from retrying import retry
import datetime

CURRENT_DIR = os.path.dirname(__file__)

lock = threading.Lock()

errorTable = log_errors_to_table.ErrorTable()

@retry
def download(link_list, getPDFs=True):
    

    try:
        caseName, caseNo, caseCourt, output_path, client_matter = link_list
    except Exception as error:
        errorTable.append_error_table(error=error)
        return
        
    try:
        user = login.Credentials()
    except Exception as error:
        errorTable.append_error_table(error=error)
        return

    try:
        myDocket = user_tools.Docket((user.username, user.password), caseNo, caseCourt)
    except Exception as error:
        errorTable.append_error_table(error=error)
        return

    if myDocket.all['success'] != True:
        return

    try:
        savePath = os.path.join(output_path, f"{caseName} - {caseNo}", f"{caseName} - {caseNo}.json")
    except Exception as error:
        errorTable.append_error_table(error=error, name=caseName, docketNumber=caseNo, court=caseCourt)
        return

            # If the directory for the docket doesn't yet exist...
    if not os.path.exists(os.path.join(output_path, f"{caseName} - {caseNo}")):
                # Then, create it!

        with lock:
            try:
                os.makedirs(os.path.join(output_path, f"{caseName} - {caseNo}"))
            except Exception as error:
                errorTable.append_error_table(error=error, name=caseName, docketNumber=caseNo, court=caseCourt)
                return
       
        # We use a lock so this code won't be executed by multiple threads simultaneously, this way we don't get errors.
    with lock:
        # When 'opening' a file that doesn't yet exist, we create that file.
        # Here, we create the json file we'll be saving the data to.
        try:
            with open(savePath, 'w') as fp:
                # Then we write the data to the newly created .json file.
                json.dump(myDocket.all,fp, indent=3)
        except Exception as error:
            errorTable.append_error_table(error=error, name=caseName, docketNumber=caseNo, court=caseCourt)
            return
        
    # except Exception as error:
    #     errorTable.append_error_table(error, caseName, "JSON")
    #     return
    with lock:
        tupleArgs = []

    if getPDFs == True:
        
        try:
            pdfList = myDocket.links()
        except Exception as error:
            errorTable.append_error_table(error=error, name=caseName, docketNumber=caseNo, court=caseCourt)
            return

        
        

        for item in pdfList:

            try:
                number = item['number']
                name = item['name']
                link = item['link']
                exhibit = f"Exhibit {item['exhibit']} - " if item['exhibit'] != None else ""

                fileName = f"{exhibit}{number} - {name}"

                
                pdfSavePath = os.path.join(output_path, f"{caseName} - {caseNo}", f"{fileName}.pdf")
                
                individualTupleArg = (link, pdfSavePath, number, name, exhibit, client_matter)
            except:
                continue
            with lock:
                tupleArgs.append(individualTupleArg)

        

                

                

            # except Exception as error:
            #     errorTable.append_error_table(error=error, name=caseName, docketNumber=caseNo, court=caseCourt, document=f"{exhibit}{number} - {name}")
            #     continue

            # print(f"{caseName} - {caseNo}\n{number} - {name}")


            
                # except Exception as error:
                #     errorTable.append_error_table(error=error, name=caseName, docketNumber=caseNo, court=caseCourt, document=f"{exhibit}{number} - {name}")
                #     continue
    def download_pdf(tuple_args):

        link, pdfSavePath, number, name, exhibit, client_matter = tuple_args
        
        params = {
                "login_token": user.authenticate(),
                "client_matter": client_matter,
                }
        
        try:
            result = requests.get(link, stream=True, params=params)
            result.raise_for_status()
        except:
            return


        with lock:
            try:
                with open(pdfSavePath, "wb") as e:

                    e.write(result.content)
            except:
                return

    # except Exception as error:
    #     errorTable.append_error_table(error, caseName, name)
    #     pass
        return

    def thread_download_pdf():
        with concurrent.futures.ThreadPoolExecutor() as executor:
        # We start concurrent.futures to have every line of code within the block get passed to its own sepreate thread.
            results = executor.map(download_pdf, tupleArgs, timeout=300)
        return results

    thread_download_pdf()
    return

def thread_download():
    """
    Wrapper function for download_json_from_list_of_tuples
    and table_to_list_of_tuples().
    table_to_list_of_tuples() is called, and it's return values are stored in a variable and passed as arguments
    to individual calls of download_json_from_list_of_tuples() within individual threads, speeding up the download.
    """

    # We call table_to_list_of_tuples() and store the results in a variable.
    tuples_from_table = table_to_list_of_tuples()
    # We get the amount of iterations the program will make, this will be used to tell the loading bar when it will be done.
    maximum = len(tuples_from_table)
    print("Downloading files...")
    # We start a counter, so at the end we can calculate how long the downloads took.
    start = time.perf_counter()

    with concurrent.futures.ProcessPoolExecutor() as executor:
    # We start concurrent.futures to have every line of code within the block get passed to its own sepreate thread.
        results = list(tqdm(executor.map(download, tuples_from_table), total=maximum))
        # We use executor.map to use threading, it takes the function and a list of arguments to pass as arguments.
        # tdqm starts a progress bar, and we specify the max value it needs to reach to finish.

    # We store the time again when it is over.
    finish = time.perf_counter()
    # We subtract the start time from the finish time to let the user know how long the download took.
    print(f"Finished downloading files in {round(finish-start)} seconds.")
    try:
        # If the users operating system permits, we open the download directory where the desired output files were downloaded to.
        os.startfile(global_variables.JSON_INPUT_OUTPUT_PATH)
    except:
        pass
    currentDateTime = datetime.datetime.now().strftime("%I%M%p %B %d, %Y")
    errorTable.error_excel_save(os.path.join(CURRENT_DIR, 'log', f"LogTable - {currentDateTime}.xlsx"))
    return results



def table_to_list_of_tuples():
    """
    Grabs the csv from the CSV_INPUT_PATH variable that the user specified in the main menu,
    and returns a list of tuples. Each tuple in the list is a set of arguments ready to be passed to
    the download_json_from_list_of_tuples() function within the thread_download_json() function
    that wraps both of these funtions to use threading to download more quickly.
    """

    # The path to the input spreadsheet is the path that the user specified in the main menu.
    spreadsheet_path = global_variables.CSV_INPUT_PATH

    # The path where the JSON files will be downloaded to is the path that the user specified in the main menu.
    JSON_INPUT_OUTPUT_PATH = global_variables.JSON_INPUT_OUTPUT_PATH

    # The client matter is the string that the user specified in the main menu.
    CLIENT_MATTER = global_variables.CLIENT_MATTER

    # This list starts out empty, gets a tuple appended to it with every iteration of the loop below, and will eventually
    # be the value returned by this function.
    output_list_of_tuples = []

    try:
        # We try to open the csv as a pandas dataframe. Pandas dataframes make working with tabular data in python faster and easier.
        df = pd.read_csv(spreadsheet_path)

    except Exception as e:
        # If there are any errors with opening the dataframe, we print the data to the console to alert the user.
        print(f"{e}")
        input()
    
    # We loop through every row of the input spreadsheet, the row value allows us to access each value in each row through indexing.
    for index, row in df.iterrows():
        # We use indexing to store each value in the appropriate variables so they are more human-readable.
        caseName = row[0]
        caseNo = row[1]
        caseCourt = row[2]
        # We place the values into a tuple that will serve as parameters for download_json_from_list_of_tuples()
        # when we call it inside the thread_download_json() wrapper.
        row_tuple = (caseName, caseNo, caseCourt, JSON_INPUT_OUTPUT_PATH, CLIENT_MATTER)
        # We append each tuple to the list at the top of the function.
        output_list_of_tuples.append(row_tuple)
    # We return the list after it is populated with tuples during each iteration over every row in the spreadsheet.
    return output_list_of_tuples