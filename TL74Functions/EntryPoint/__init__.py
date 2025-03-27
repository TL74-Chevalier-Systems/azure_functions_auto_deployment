import logging

from azure.functions import HttpRequest, HttpResponse
from .helpers import process_filing_request


def main(req: HttpRequest) -> HttpResponse:
    logging.info("HTTP trigger function processed a request.")

    response_message, status_code = process_filing_request(req)

    return func.HttpResponse(response_message, status_code=status_code)
