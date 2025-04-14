import logging

from azure.functions import HttpRequest, HttpResponse
from .wrapper_13f import initialize_13f_workflow

def main(req: HttpRequest) -> HttpResponse:
    logging.info("HTTP trigger function processed a request.")

    response_message, status_code = initialize_13f_workflow(req)

    return HttpResponse(response_message, status_code=status_code)
