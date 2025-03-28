import os
import logging
from azure.cosmos import CosmosClient

import sys
from edgar import *
import pandas as pd
import json

def retrieve_value_full(company, accn, fact_name):
    try:
        filtered_df = company[(company['namespace'] == 'us-gaap') & (company['accn'] == str(accn)) & (company['fact'] == str(fact_name))]
        filtered_df = filtered_df.loc[filtered_df['timestamp'].idxmax()]
        value = filtered_df['val']
        return value
    except Exception as e:
        print(f"{fact_name} - retrieval error: {e}")
        return "N/A"

def process_fha(req):
    COSMOS_DB_URL = os.getenv("COSMOS_DB_URL")
    COSMOS_DB_KEY = os.getenv("COSMOS_DB_KEY")
    COSMOS_DB_DATABASE = os.getenv("COSMOS_DB_DATABASE")
    COSMOS_DB_CONTAINER_FILINGS = os.getenv("COSMOS_DB_CONTAINER_FILINGS")

    if not all([COSMOS_DB_URL, COSMOS_DB_KEY, COSMOS_DB_DATABASE, COSMOS_DB_CONTAINER_FILINGS]):
        error_msg = (
            "Missing Cosmos DB configuration. Please ensure 'COSMOS_DB_URL', "
            "'COSMOS_DB_KEY', 'COSMOS_DB_DATABASE', and 'COSMOS_DB_CONTAINER_FILINGS' are set."
        )
        logging.error(error_msg)
        return error_msg, 500

    # Retrieve query parameters
    accession_code = req.params.get("accession_code")
    ticker = req.params.get("ticker")
    date = req.params.get("date")
    form = req.params.get("form")

    logging.info("Params loaded")
    # ADDED START

    set_identity("dowang10@student.ubc.ca")
    logging.info("EDGAR identity set")

    try:
        filing = get_by_accession_number(str(accession_code))
        logging.info(filing)
    except Exception as e:
        logging.info("FHA Error: unable to find filing with accession number " + str(accession_code))
        exit()

    try:
        company = Company(str(filing.cik)).get_facts().to_pandas()
    except Exception as e:
        logging.info("FHA Error: unable to generate pandas dataframe for company with CIK " + str(filing.cik))
        exit()

    try:
        company_accn_subset = company[(company['namespace'] == 'us-gaap') & (company['accn'] == str(accession_code))]
        logging.info(f"Extracted {len(company_accn_subset)} rows for accession number {accession_code}")
    except Exception as e:
        logging.info(f"FHA Error extracting rows for accession number {accession_code}: {e}")
        exit()

    try:
        subset_json_dict = {} # Convert the dataframe to a JSON-serializable dictionary, keyed by the row index
        company_accn_subset = company_accn_subset.reset_index()
        for idx, row in company_accn_subset.iterrows():
            row_data = row.to_dict()  # Convert each row to a dictionary
            subset_json_dict[str(idx)] = row_data  # Use the dataframe index as the key, convert to string for JSON compatibility

        # Convert the dictionary to a JSON string with indentation for readability
        subset_json_str = json.dumps(subset_json_dict, indent=4, default=str)  # default=str converts Timestamp to string

    except Exception as e:
        logging.info(f"FHA Error converting dataframe subset to JSON: {e}")
        exit()

    try:
        company['end'] = pd.to_datetime(company['end'])
        company['timestamp'] = company['end'].astype('int64')
    except Exception as e:
        logging.info("FHA Error: unable to parse/organize date format")
        exit()

    test_value = retrieve_value_full(company, accession_code, "Assets")

    # ADDED END    
    

    # Parse JSON body if needed
    if not (accession_code and ticker and date and form):
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        accession_code = accession_code or req_body.get("accession_code")
        ticker = ticker or req_body.get("ticker")
        date = date or req_body.get("date")
        form = form or req_body.get("form")

    # Proceed if all required parameters are available
    if accession_code and ticker and date and form:
        try:
            client = CosmosClient(COSMOS_DB_URL, COSMOS_DB_KEY)
            database = client.get_database_client(COSMOS_DB_DATABASE)
            filings_container = database.get_container_client(COSMOS_DB_CONTAINER_FILINGS)

            filing_entry = {
                "id": accession_code,
                "ticker": ticker,
                "date": date,
                "form": form,
                "analyses": [],
            }

            # ADDED START

            temp = {
                "type": test_value
            }

            filing_entry["analyses"].append({"fna": temp})

            # ADDED END

            filings_container.upsert_item(filing_entry)

            response_message = (
                f"Received data: Accession Code - {accession_code}, "
                f"Ticker - {ticker}, Date - {date}, Form - {form}."
            )
            return response_message, 200
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return "An error occurred while processing your request.", 500
    else:
        error_msg = (
            "Missing parameters. Please provide 'accession_code', 'ticker', 'date', and 'form' "
            "in the query string or request body."
        )
        logging.error(error_msg)
        return error_msg, 400