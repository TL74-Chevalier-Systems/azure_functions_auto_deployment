import logging

from azure.functions import HttpRequest, HttpResponse
from .fha_wrapper import fha_wrapper


def main(req: HttpRequest) -> HttpResponse:
    logging.info("HTTP trigger function processed a request.")

    response_message, status_code = fha_wrapper(req)

    return HttpResponse(response_message, status_code=status_code)
