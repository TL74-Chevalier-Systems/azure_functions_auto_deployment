import os
import logging
import subprocess
import json
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "13F-Analysis"))

from commands.extraction import extract_13f_from_accession

MAX_DOC_SIZE = 1.9 * 1024 * 1024

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

            data = extract_13f_from_accession(accession_code)

            try:
                # Parse the JSON output into a Python list
                # data = json.loads(extraction_result.stdout)
                if not isinstance(data, list):
                    raise ValueError("Extraction output is not a list.")
                logging.info(f"Extraction successful: {data}")
            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"Failed to parse extraction output as a list: {e}")
                return "Failed to parse extraction output.", 500

            # Connect to Cosmos DB
            client = CosmosClient(COSMOS_DB_URL, COSMOS_DB_KEY)
            database = client.get_database_client(COSMOS_DB_DATABASE)
            container = database.get_container_client(COSMOS_DB_CONTAINER_FILINGS)

            # Try to read existing document
            try:
                filing = container.read_item(item=accession_code, partition_key=ticker)
            except CosmosResourceNotFoundError:
                return f"No existing filing for {accession_code}", 404

            chunks = []
            current_chunk = []
            current_size = 0

            for entry in data:
                entry_str = json.dumps(entry)
                entry_size = len(entry_str.encode("utf-8"))

                if current_size + entry_size > MAX_DOC_SIZE:
                    chunks.append(current_chunk)
                    current_chunk = [entry]
                    current_size = entry_size
                else:
                    current_chunk.append(entry)
                    current_size += entry_size

            if current_chunk:
                chunks.append(current_chunk)

            chunk_refs = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{accession_code}::chunk_{i}"
                container.upsert_item({
                    "id": chunk_id,
                    "accession_code": accession_code,
                    "ticker": ticker,
                    "chunk_index": i,
                    "13f_chunk": chunk,
                })
                chunk_refs.append(chunk_id)

            filing.setdefault("analyses", []).append({
                "13f_chunks": chunk_refs,
                "chunk_count": len(chunk_refs)
            })

            container.replace_item(item=accession_code, body=filing)

            return f"Stored {len(chunk_refs)} chunk(s) for {accession_code}.", 200
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
