from dataiku import pandasutils as pdu
import pandas as pd, numpy as np
import re
import dataiku
import dataikuapi
from dataiku import api_client as client
from dataiku.core.sql import SQLExecutor2
import json, time, requests
import logging
from dataiku.customrecipe import get_output_names_for_role, get_recipe_config
import urllib
from pandas.io.json import json_normalize
from hubspot import write_data_json, write_data_columns, get_values

logger = logging.getLogger(__name__)

output_names = get_output_names_for_role('output')
output_name = output_names[0]
output = dataiku.Dataset(output_name) 

api_key = get_recipe_config()['hapikey']
object_name = get_recipe_config()['object_name']
format_output = get_recipe_config()['format']
properties_type = get_recipe_config()['properties_to_retrieve']
list_input = get_recipe_config()['custom_properties_list']
counter = 0

if format_output == 'JSON':
    writer = output.get_writer()
    logger.info( "Writer opened")
    for item in get_values(api_key, properties_type, list_input, object_name):
        write_data_json(writer, item, output, format_output)
        counter += 1
    writer.close()
    logger.info( "Writer closed")
    
elif format_output == 'Readable with columns':    
    for item in get_values(api_key, properties_type, list_input, object_name):
        write_data_columns(item, output, format_output)
        counter += 1

logger.info(str(counter) + " " + object_name + " downloaded")