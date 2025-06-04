import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
import json
import logging
from pandas.io.json import json_normalize

logger = logging.getLogger(__name__)

def write_data_json(writer, json_line, output_dataset, format_output):  
    output_dataset.write_schema([{"name": "object","type": "string"}])
    for list_objects in json_line:
        logger.info("Writing to output as JSON")
        writer.write_row_array([json.dumps(list_objects)])   
             
def write_data_columns(json_line, output_dataset, format_output):
        output_result = json_normalize(json_line)
        logger.info("Writing to output")
        output_dataset.write_with_schema(output_result)