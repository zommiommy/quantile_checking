# QuantileChecker is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

from logger import logger, setLevel
from data_getter import DataGetter

import os
import sys
import logging
import argparse
import numpy as np
from typing import Dict, Union, List

import warnings
warnings.filterwarnings("ignore")



class MyParser(argparse.ArgumentParser):
    """Custom parser to ensure that the exit code on error is 1
        and that the error messages are printed on the stderr 
        so that the stdout is only for sucessfull data analysis"""

    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(file=sys.stderr)
        sys.exit(1)


class MainClass:

    copyrights = """QuantileChecker is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License."""

    def __init__(self):
        # Define the possible settings

        self.parser = MyParser(description=self.copyrights)

        query_settings_r = self.parser.add_argument_group('query settings (required)')
        query_settings_r.add_argument("-H", "--hostname",       help="The hostname to select", type=str, required=True)
        query_settings_r.add_argument("-S", "--service",        help="The service to select", type=str, required=True)
        query_settings_r.add_argument("-M", "--measurement",    help="Measurement where the data will be queried.", type=str, required=True)
        query_settings_r.add_argument("-I", "--input",             help="The name of the input bandwith",  type=str, default="inBandwith")
        query_settings_r.add_argument("-O", "--output",            help="The name of the output bandwith", type=str, default="outBandwith")

        thresholds_settings = self.parser.add_argument_group('Fee settings')
        thresholds_settings.add_argument("-m", "--max",         help="The maxiumum ammount of Bandwith usable", type=int, required=True)
        thresholds_settings.add_argument("-p", "--penalty",     help="The fee in euros inc ase of the threshold is exceded", type=float, required=True)
        thresholds_settings.add_argument("-q", "--quantile",    help="The quantile to confront with the threshold", type=float, default=0.95)

        verbosity_settings= self.parser.add_argument_group('verbosity settings (optional)')
        verbosity_settings.add_argument("-v", "--verbosity", help="set the logging verbosity, 0 == CRITICAL, 1 == INFO, 2 == DEBUG it defaults to ERROR.",  type=int, choices=[0,1,2], default=0)

        self.args = self.parser.parse_args()

        if self.args.verbosity == 1:
            setLevel(logging.INFO)
        elif  self.args.verbosity == 2:
            setLevel(logging.DEBUG)
        else:
            setLevel(logging.CRITICAL)
        
    def construct_query(self, metric):
        dic =  {k: self.args.__getattribute__(k) for k in dir(self.args)}
        dic["metric"] = metric
        return """SELECT value FROM {measurement} WHERE "hostname" = '{hostname}' AND "service" = '{service}' AND "matric" = '{metric}' """.format(**dic) # AND "time" > (now() - 24h) 

    def run(self):
        logger.info("Going to connect to the DB")
        dg = DataGetter()
        logger.info("Gathering the data for the input Bandwith")
        _input  = dg.exec_query(self.construct_query(self.args.input))
        logger.info("Gathering the data for the output Bandwith")
        _output = dg.exec_query(self.construct_query(self.args.output))

        # Convert to numpy arrays
        _input  = np.array([x["value"] for x in _input ], dtype=np.float)
        _output = np.array([x["value"] for x in _output], dtype=np.float)

        logger.debug("Input  Values [%s]", _input)
        logger.debug("Output Values [%s]", _output)

        # Convert from bytes to Mib
        _input  /= (1024*1024)
        _output /= (1024*1024)

        logger.info("Calculating the quantile and the other metrics")
        self.quantile = np.quantile([_input, _output], self.args.quantile)
        self.max = max(max(_input), max(_output))
        self.input = np.mean(_input)
        self.output = np.mean(_output)

        # TODO check metric
        self.precision = 1
        self.burst = 1

        logger.info("Formatting the formatted results:")

        result = f"""Il {self.args.quantile * 100:.0f}th percentile calcolato e' {self.quantile:.0f}Mib"""
        result += " | "
        result += ", ".join([
            f"""bandwith_stats_95th={self.quantile:.0f}Mib""",
            f"""bandwith_stats_max={self.max:.0f}Mib""",
            f"""bandwith_stats_in={self.input:.0f}Mib""",
            f"""bandwith_stats_out={self.output:.0f}Mib""",
            f"""bandwith_stats_precision={self.precision:.0f}%""",
            f"""bandwith_stats_burst={self.burst}""",
            ])
        logger.info("Printing the results")
        print(result)

if __name__ == "__main__":
    MainClass().run()