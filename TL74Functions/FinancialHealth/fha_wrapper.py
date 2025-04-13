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

            logging.info(f"Starting fiscal period/year extraction for accession_code: {accession_code}")

            if "raw" not in fha_json:
                logging.warning(f"'raw' key missing in fha_json for {accession_code}")
            elif not fha_json["raw"]:
                logging.warning(f"'raw' dictionary is empty for {accession_code}")
            else:
                logging.info(f"Found 'raw' data in fha_json for {accession_code}")
                
                try:
                    # Get the first key in the raw dictionary
                    if len(fha_json["raw"]) == 0:
                        logging.warning(f"'raw' dictionary has no keys for {accession_code}")
                    else:
                        first_key = next(iter(fha_json["raw"]))
                        logging.info(f"First key in raw data: {first_key}")
                        
                        raw_data = fha_json["raw"][first_key]
                        logging.info(f"Raw data structure for first key: {list(raw_data.keys())}")
                        
                        # Extract fiscal period and year if available
                        if "fp" in raw_data:
                            fiscal_period = raw_data.get("fp")
                            logging.info(f"Found fiscal period: {fiscal_period}")
                        else:
                            logging.warning(f"'fp' key not found in raw_data for {accession_code}")
                            
                        if "fy" in raw_data:
                            fiscal_year = raw_data.get("fy")
                            logging.info(f"Found fiscal year: {fiscal_year}")
                        else:
                            logging.warning(f"'fy' key not found in raw_data for {accession_code}")
                except Exception as e:
                    logging.error(f"Error extracting fiscal data: {str(e)}")

            # Add fiscal period and year to the existing item if found
            if fiscal_period:
                existing_item["fiscal_period"] = fiscal_period
                logging.info(f"Added fiscal period '{fiscal_period}' to document for {accession_code}")
            else:
                logging.warning(f"No fiscal period to add for {accession_code}")

            if fiscal_year:
                existing_item["fiscal_year"] = fiscal_year
                logging.info(f"Added fiscal year '{fiscal_year}' to document for {accession_code}")
            else:
                logging.warning(f"No fiscal year to add for {accession_code}")
                
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
    
