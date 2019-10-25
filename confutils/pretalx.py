import requests
from .constants import headers


def get_from_pretalx_api(url, params=None):
    """
    Helper function to get data from Pretalx API
    :param url:
    :param params: optional filters
    :return: results and next url (if any)
    """
    if not params:
        params = {}
    # print(f'getting more reviews: {url}')
    res = requests.get(url, headers=headers, params=params)
    resj = res.json()
    return resj['results'], resj['next']


def get_all_data_from_pretalx(url, params=None):
    """
    Helper to get paginated data from Pretalx API
    :param url: url to start from
    :param params: optional filters

    """
    api_result = []
    while url:
        chunk, url = get_from_pretalx_api(url, params=params)
        api_result.extend(chunk)
    return api_result
