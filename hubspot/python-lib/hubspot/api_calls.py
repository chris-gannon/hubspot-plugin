import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
import json, time, requests
from hubspot.constants import Constants
import logging

def get_properties(apikey, object_name):
    url = "https://api.hubapi.com/properties/v1/" + object_name + "/properties?"
    try:
        r = requests.get(url, params = {'hapikey': apikey})
    except Exception as e:
        logging.exception("API exception when calling %s ".format(url), e)
        raise Exception("API exception when calling %s ".format(url))

    if r.status_code != 200:
        logging.error("API error when calling {}, error code {}. Returned response : {}".format(r.url, r.status_code, r.json()))
        raise Exception('API error when calling {}, error code {}. Returned response : {}'.format(r.url, r.status_code, r.json()))
    response_dict = r.json()
    list_properties = [x[u'name'] for x in response_dict]
    return list_properties

def get_values(apikey, properties_type, list_input, object_name):
    if object_name == 'contacts':
        limit = Constants.CONTACTS_LIMIT
        url_feat = "https://api.hubapi.com/contacts/v1/lists/all/contacts/all?"
        if properties_type == 'Standard':
            parameter_dict = {'hapikey': apikey, 'count': limit}
        elif properties_type == 'All':
            properties = get_properties(apikey, object_name)
            parameter_dict = {'hapikey': apikey, 'count': limit, 'property': properties}
        elif properties_type == 'Custom':
            properties = list_input
            parameter_dict = {'hapikey': apikey, 'count': limit, 'property': properties} 
    elif object_name == 'companies':
        limit = Constants.COMPANIES_LIMIT
        url_feat = "https://api.hubapi.com/companies/v2/companies/paged?"
        if properties_type == 'Standard':
            parameter_dict = {'hapikey': apikey, 'count': limit}
        elif properties_type == 'All':
            properties = get_properties(apikey, object_name)
            parameter_dict = {'hapikey': apikey, 'count': limit, 'properties': properties}
        elif properties_type == 'Custom':
            properties = list_input
            parameter_dict = {'hapikey': apikey, 'count': limit, 'properties': properties} 
    has_more = True
    counter = 0
    while has_more:
        try:
            r = requests.get(url_feat, params=parameter_dict)
        except Exception as e:
            logging.exception("API exception when calling %s ".format(url_feat), e)
            raise Exception("API exception when calling %s ".format(url_feat))

        if r.status_code != 200:
            logging.error(
                "API error when calling {}, error code {}. Returned response : {}".format(r.url, r.status_code,
                                                                                          r.json()))
            raise Exception(
                'API error when calling {}, error code {}. Returned response : {}'.format(r.url, r.status_code,
                                                                                          r.json()))
        counter += 1
        response_dict = r.json()
        has_more = response_dict['has-more']
        yield response_dict[object_name]
        if object_name == 'contacts':
            parameter_dict['vidOffset']= response_dict['vid-offset']
        elif object_name == 'companies':
            parameter_dict['offset']= response_dict['offset']
        if counter >= 95:
            time.sleep(10)
            counter = 0