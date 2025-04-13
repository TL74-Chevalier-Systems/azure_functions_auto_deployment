import os
import logging
import subprocess
from azure.cosmos import CosmosClient

def initialize_13f_workflow(req):
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
        logging.info(f"Edgar Identity used from env: {os.getenv('EDGAR_IDENTITY')}")

        try:
            extraction_command = [
                "python",
                "main.py",
                "extract-13f",
                accession_code
            ]
            extraction_result = subprocess.run(
                extraction_command,
                capture_output=True,
                text=True,
                cwd=os.path.join(os.path.dirname(__file__), "13F-Analysis")
            )

            if extraction_result.returncode != 0:
                logging.error(f"Extraction failed: {extraction_result.stderr}")
                return f"Extraction failed for {accession_code}.", 500

            logging.info(extraction_result.stdout)

            # Connect to Cosmos DB
            client = CosmosClient(COSMOS_DB_URL, COSMOS_DB_KEY)
            database = client.get_database_client(COSMOS_DB_DATABASE)
            filings_container = database.get_container_client(COSMOS_DB_CONTAINER_FILINGS)

            # Try to read existing document
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
            # new_analysis = {
            #     "comp_analysis": comp_analy,
            #     "risk_analysis": risk_analy
            # }
            # existing_item.setdefault("analyses", []).append(new_analysis)

            # # Replace the document in the DB
            # filings_container.replace_item(item=accession_code, body=existing_item)

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
