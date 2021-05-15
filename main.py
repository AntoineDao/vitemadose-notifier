import requests
from flask import Request, Response


def fetch_availability_data(departement: str = '75') -> dict:
    """Fetch availability data from the vitemadose "database" and return a parsed dict

    Args:
        departement (str, optional): The departement number. Defaults to '75'.

    Returns:
        dict: An availability dict object (check file at `data/75.json` in this folder for an example)
    """
    url = f'https://vitemadose.gitlab.io/vitemadose/{departement}.json'
    return requests.get(url).json()


def get_chronodose_availability_count(data: dict) -> int:
    """Parse the availability data from vitemadose and count the number of available chronodose slots

    Args:
        data (dict): An availability dict object (check file at `data/75.json` in this folder for an example)

    Returns:
        int: The number of available Chronodose slots
    """
    chronodose_count = 0
    for centre in data['centres_disponibles']:
        if 'Pfizer-BioNTech' in centre['vaccine_type']:
            for appointment in centre['appointment_schedules']:
                if appointment['name'] == "chronodose":
                    chronodose_count += appointment['total']

    return chronodose_count


def send_ifttt_webhook(chronodose_count: int, api_key: str, trigger_name: str, departement: str, ):
    """Send a webhook request to IFTTT

    Args:
        chronodose_count (int): the number of available chronodose slots.
        api_key (str, optional): the API key used to authenticate to IFTTT
        trigger_name (str, optional): the IFTTT trigger name to react to this webhook.
        departement (str, optional): the department number where chronodose slots are available.
    """
    url = f'https://maker.ifttt.com/trigger/{trigger_name}/with/key/{api_key}'
    requests.get(url, data={'value1': chronodose_count, 'value2': departement})


def run_script(api_key: str, trigger_name: str, departement: str):
    """Check chronodose availability and send a webhook to IFTTT if there are available slots

    Args:
        api_key (str, optional): the API key used to authenticate to IFTTT
        departement (str, optional): the department number where chronodose slots are available.
        trigger_name (str, optional): the IFTTT trigger name to react to this webhook.
    """
    availability = fetch_availability_data(departement)
    chronodose_count = get_chronodose_availability_count(availability)
    if chronodose_count > 0:
        send_ifttt_webhook(
            chronodose_count=chronodose_count,
            api_key=api_key,
            departement=departement,
            trigger_name=trigger_name
        )


def http(request: Request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    data = request.get_json()
    api_key = data.get('key', None)
    trigger_name = data.get('trigger', None)
    departement = data.get('departement', '75')

    if api_key is None:
        return Response('Cannot ping ifttt without API key', 404)

    if trigger_name is None:
        return Response('Cannot ping ifttt without trigger name', 404)

    run_script(api_key=api_key, trigger_name=trigger_name,
               departement=departement)

    return Response('OK')
