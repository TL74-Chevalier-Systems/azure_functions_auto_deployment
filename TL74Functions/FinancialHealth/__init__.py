import logging

from azure.functions import HttpRequest, HttpResponse
from .fha import process_fha


def main(req: HttpRequest) -> HttpResponse:
    logging.info("HTTP trigger function processed a request.")

    response_message, status_code = process_fha(req)

    return HttpResponse(response_message, status_code=status_code)
