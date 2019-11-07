# QuantileChecker is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

from logger import logger

import os
import sys
import json
import logging
import numpy as np
from typing import List, Tuple, Dict, Union
from influxdb import InfluxDBClient

class DataGetter:
    """Class for the basic logic of accessing and executing a query to the DB"""
    setting_file = "/db_settings.json"

    def __init__(self):
        """Load the settings file and connect to the DB"""

        # Get the current folder
        current_script_dir = "/".join(__file__.split("/")[:-2])
        
        path = current_script_dir + self.setting_file
        logger.info("Loading the DB settings from [%s]"%path)

        # Load the settings
        with open(path, "r") as f:
            self.settings = json.load(f)

        logger.info("Conneting to the DB on [{host}:{port}] for the database [{database}]".format(**self.settings))
        
        # Create the client passing the settings as kwargs
        self.client = InfluxDBClient(**self.settings)

    def __del__(self):
        """On exit / delation close the client connetion"""
        if "client" in dir(self):
            self.client.close()

    def exec_query(self, query : str):
        """Escape the \ in the query, Execute the query, return the result as list of dictionaries"""
        # Construct the query to workaround the tags distinct constraint
        query = query.replace("\\", "\\\\")
        logger.info(f"Executing query [{query}]")
        result = list(self.client.query(query).get_points())
        logger.debug(f"Result of the query: [{result}]")
        return result