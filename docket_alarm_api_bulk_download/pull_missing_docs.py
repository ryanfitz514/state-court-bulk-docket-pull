import requests
import get_json
import login


def search_direct(docketnum, court):
    """ Takes in the name of a party and the docket number as a parameter,
        returns the Docket Alarm search results. You can make calls to the
        /getdocket endpoint with these results to get more detailed information
        on the docket you are looking for.
    """
    searchdirect_url = "https://www.docketalarm.com/api/v1/searchdirect/"

    user = login.Credentials()
    

    data = {
        'login_token': user.authenticate(),
        'client_matter':"",
        # 'party_name':party_name,
        'docketnum':docketnum,
        'court': court,
        # 'case_type':'CF',

    }
    
    result = requests.post(searchdirect_url, data)

    result_json = result.json()

    return result_json

def search_pacer(docketnum, court):
    url = "https://www.docketalarm.com/api/v1/searchpacer/"

    user = login.Credentials()


    data = {
        'login_token': user.authenticate(),
        'client_matter':"",
        # 'party_name':party_name,
        'docket_num':docketnum,
        'court_region': court,
        # 'case_type':'CF',

    }
    
    result = requests.get(url, data)

    result_json = result.json()

    return result_json

def loop_and_search(state_court=False,federal_court=False)
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

        if state_court == True:
            search_direct(caseNo, caseCourt)
        
        if federal_court == True:
            search_pacer(caseNo) # Didnt include region because it wont be the same as court



print(search_direct("2013-CF-000124", "Florida State, Duval County, Fourth Circuit Court"))