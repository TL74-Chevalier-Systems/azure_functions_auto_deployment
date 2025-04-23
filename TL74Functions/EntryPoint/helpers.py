import os
import logging
import requests
from azure.cosmos import CosmosClient

def process_filing_request(req):    
    # Retrieve query parameters
    accession_code = req.params.get("accession_code")
    ticker = req.params.get("ticker")
    date = req.params.get("date")
    form = req.params.get("form")

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
            # Add the filing entry to Cosmos DB
            response_message, status_code = add_filing_entry(accession_code, ticker, date, form)
            if status_code != 200:
                return response_message, status_code
            logging.info(f"Filing entry added: {response_message}")

            if form == "10-K" or form == "10-Q":
                logging.info(f"Triggering financial health analysis for {form}.")
                response_message, status_code = call_financial_health_analysis(accession_code, ticker, date, form)
                if status_code != 200:
                    return response_message, status_code
                
                # Call LLM Analysis
                logging.info(f"Triggering LLM analysis for {form}.")
                response_message, status_code = call_llm_analysis(accession_code, ticker, date, form)
                if status_code != 200:
                    return response_message, status_code


            if form == "13F-HR":
                # Call 13F-HR analysis trigger
                print("13F-HR analysis trigger called.")
                response_message, status_code = call_13f_analysis(accession_code, ticker, date, form)
                if status_code != 200:
                    return response_message, status_code

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
    

def add_filing_entry(accession_code, ticker, date, form):
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

        filings_container.upsert_item(filing_entry)

        response_message = (
            f"Received data: Accession Code - {accession_code}, "
            f"Ticker - {ticker}, Date - {date}, Form - {form}."
        )

        return response_message, 200
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return "An error occurred while processing your request.", 500

def call_financial_health_analysis(accession_code, ticker, date, form):
    FINANICAL_HEALTH_ANALYSIS_URL = 'https://tl74functionsapp.azurewebsites.net/api/FinancialHealth'
    TRIGGER_API_KEY = os.getenv("TRIGGER_API_KEY")

    if not TRIGGER_API_KEY:
        error_msg = (
            "Missing TRIGGER_API_KEY configuration. Please ensure 'TRIGGER_API_KEY' is set."
        )
        logging.error(error_msg)
        return error_msg, 500

    payload = {
        "accession_code": accession_code,
        "ticker": ticker,
        "date": date,
        "form": form
    }

    logging.info(f"Payload for financial health analysis: {payload}")
    try:
        finanical_analysis_endpoint = f"{FINANICAL_HEALTH_ANALYSIS_URL}?code={TRIGGER_API_KEY}"
        response = requests.post(finanical_analysis_endpoint, json=payload)

        if response.status_code == 200:
            logging.info("Financial health analysis triggered successfully.")
            return response.text, 200
        else:
            logging.error(f"Failed to trigger financial health analysis: {response.status_code}")
            return f"Error: {response.status_code}", response.status_code
    except Exception as ex:
        logging.error(f"Failed to trigger analysis: {ex}")
        return str(ex), 500
    
def call_llm_analysis(accession_code, ticker, date, form):
    LLM_ANALYSIS_URL = 'https://tl74functionsapp.azurewebsites.net/api/LLMAnalysis'
    TRIGGER_API_KEY = os.getenv("TRIGGER_API_KEY")

    if not TRIGGER_API_KEY:
        error_msg = (
            "Missing TRIGGER_API_KEY configuration. Please ensure 'TRIGGER_API_KEY' is set."
        )
        logging.error(error_msg)
        return error_msg, 500

    payload = {
        "accession_code": accession_code,
        "ticker": ticker,
        "date": date,
        "form": form
    }

    logging.info(f"Payload for LLM analysis: {payload}")
    try:
        llm_analysis_endpoint = f"{LLM_ANALYSIS_URL}?code={TRIGGER_API_KEY}"
        response = requests.post(llm_analysis_endpoint, json=payload)

        if response.status_code == 200:
            logging.info("LLM analysis triggered successfully.")
            return response.text, 200
        else:
            logging.error(f"Failed to trigger LLM analysis: {response.status_code}")
            return f"Error: {response.status_code}", response.status_code
    except Exception as ex:
        logging.error(f"Failed to trigger LLM analysis: {ex}")
        return str(ex), 500
    
def call_13f_analysis(accession_code, ticker, date, form):
    ANALYSIS_13F = 'https://tl74functionsapp.azurewebsites.net/api/ThirteenF'
    TRIGGER_API_KEY = os.getenv("TRIGGER_API_KEY")

    if not TRIGGER_API_KEY:
        error_msg = (
            "Missing TRIGGER_API_KEY configuration. Please ensure 'TRIGGER_API_KEY' is set."
        )
        logging.error(error_msg)
        return error_msg, 500

    payload = {
        "accession_code": accession_code,
        "ticker": ticker,
        "date": date,
        "form": form
    }

    logging.info(f"Payload for 13F analysis: {payload}")
    try:
        thirteenf_analysis_endpoint = f"{ANALYSIS_13F}?code={TRIGGER_API_KEY}"
        response = requests.post(thirteenf_analysis_endpoint, json=payload)

        if response.status_code == 200:
            logging.info("13F analysis triggered successfully.")
            return response.text, 200
        else:
            logging.error(f"Failed to trigger 13F analysis: {response.status_code}")
            return f"Error: {response.status_code}", response.status_code
    except Exception as ex:
        logging.error(f"Failed to trigger 13F analysis: {ex}")
        return str(ex), 500