import logging

from azure.functions import HttpRequest, HttpResponse
from .llm_analy_wrapper import initialize_llm_workflow


def main(req: HttpRequest) -> HttpResponse:
    logging.info("HTTP trigger function processed a request.")

    response_message, status_code = initialize_llm_workflow(req)

    return HttpResponse(response_message, status_code=status_code)
