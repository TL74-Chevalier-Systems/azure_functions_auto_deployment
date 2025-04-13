import os
import logging
from azure.cosmos import CosmosClient
from .fha import fha

def fha_wrapper(req):
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
            fha_json = fha(accession_code)

            # Ensure return is not NULL
            if fha_json is None:
                logging.warning(f"Skipping update: No valid Financial analyses for {accession_code}")
                return f"No valid Financial analysis to append for {accession_code}.", 204
            
            # Connect to Cosmos DB
            client = CosmosClient(COSMOS_DB_URL, COSMOS_DB_KEY)
            database = client.get_database_client(COSMOS_DB_DATABASE)
            filings_container = database.get_container_client(COSMOS_DB_CONTAINER_FILINGS)

            try:
                existing_item = filings_container.read_item(
                    item=accession_code,
                    partition_key=ticker
                )
                logging.info(f"Found existing item for {accession_code}")
            except Exception as e:
                logging.warning(f"Error {e} No existing filing found for {accession_code}. Skipping update.")
                return f"No existing filing found for {accession_code}.", 404

            # Append the new analysis as a single entry
            new_analysis = {
                "fha": fha_json,
            }
            existing_item.setdefault("analyses", []).append(new_analysis)

            # Attempt to find fiscal year and quarter details
            fiscal_period = None
            fiscal_year = None  
            if "raw" in fha_json and fha_json["raw"]:
                # Get the first key in the raw dictionary
                first_key = next(iter(fha_json["raw"]))
                raw_data = fha_json["raw"][first_key]
                
                # Extract fiscal period and year if available
                if "fp" in raw_data:
                    fiscal_period = raw_data.get("fp")
                if "fy" in raw_data:
                    fiscal_year = raw_data.get("fy")
                
            # Add fiscal period and year to the existing item if found
            if fiscal_period:
                existing_item["fiscal_period"] = fiscal_period
                logging.info(f"Added fiscal period: {fiscal_period}")
            
            if fiscal_year:
                existing_item["fiscal_year"] = fiscal_year
                logging.info(f"Added fiscal year: {fiscal_year}")         


            # Replace the document in the DB
            filings_container.replace_item(item=accession_code, body=existing_item)

            
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
    
