import logging

from azure.functions import HttpRequest, HttpResponse


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Testing deploument trigger.")

    return HttpResponse("Testing Deployment", status_code=200)
