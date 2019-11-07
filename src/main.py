# QuantileChecker is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

from logger import logger, setLevel
from data_getter import DataGetter

import os
import sys
import logging
import argparse
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
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
        """Initialization of the class and parisng of the arguments"""
        # Define the possible settings

        self.parser = MyParser(description=self.copyrights)

        required_settings = self.parser.add_argument_group('required settings')
        required_settings.add_argument("-M", "--measurement",           help="Measurement where the data will be queried.", type=str, required=True)
        required_settings.add_argument("-HS", "--hostname-service",     help="The hostname and service to select, those must be passed as HOSTNAME|SERVICE. One can use this argument multiple times to select multiple hosts and services", type=str, required=True, action="append", default=[])

        query_settings_r = self.parser.add_argument_group('query settings')
        query_settings_r.add_argument("-I", "--input",                 help="The name of the input bandwith metric, default-value='inBandwidth'",  type=str, default="inBandwidth")
        query_settings_r.add_argument("-O", "--output",                help="The name of the output bandwith metric, default-value='outBandwidth'", type=str, default="outBandwidth")
        query_settings_r.add_argument("-rc", "--report-csv",           help="Flag, if enabled the data read from the DB are dumped as a CSV", default=False, action="store_true")
        query_settings_r.add_argument("-rcp", "--report-csv-path",     help="Path where to save the data used, default-value='./'", type=str, default="./")

        thresholds_settings = self.parser.add_argument_group('Fee settings')
        thresholds_settings.add_argument("-m", "--max",         help="The maxiumum ammount of Bandwith usable in Mbit/s ", type=int, required=True)
        thresholds_settings.add_argument("-p", "--penalty",     help="The fee in euros/(Mbit/s) in case of the threshold is exceded", type=float, required=True)
        thresholds_settings.add_argument("-q", "--quantile",    help="The quantile to confront with the threshold. it must be between 0 and 1. The default value is 0.95 so the 95th percentile", type=float, default=0.95)
        thresholds_settings.add_argument("-t", "--time",        help="The timewindow to calculate the percentile, if not specified it's considered the time from the first day of the current month.", type=str, default=None)

        verbosity_settings= self.parser.add_argument_group('verbosity settings (optional)')
        verbosity_settings.add_argument("-v", "--verbosity", help="set the logging verbosity, 0 == CRITICAL, 1 == INFO, 2 == DEBUG it defaults to ERROR.",  type=int, choices=[0,1,2], default=0)

        self.args = self.parser.parse_args()

        if self.args.verbosity == 1:
            setLevel(logging.INFO)
        elif  self.args.verbosity == 2:
            setLevel(logging.DEBUG)
        else:
            setLevel(logging.CRITICAL)

        self.parse_hosts_and_services()

    def parse_hosts_and_services(self):
        """Split and validate the data from HOST|SERVICE"""
        splitted = [x.split("|") for x in self.args.hostname_service]
        errored = [x for x in splitted if len(x) != 2]
        if len(errored):
            logger.error(f"Error parsing hostname and service, the values [{errored}] cannot be parsed as HOSTNAME|SERVICE")
            sys.exit(1)

        self.host_and_services = splitted

    def construct_query(self, metric, hostname, service):
        """Costruct the query needed in order to select the wanted data"""
        dic =  {k: self.args.__getattribute__(k) for k in dir(self.args)}
        dic["metric"] = metric
        dic["hostname"] = hostname
        dic["service"] = service

        if dic["time"] == None:
            dic["time"] = f"{self.get_seconds_from_first_of_month()}s"

        return """SELECT time, hostname, service, metric, value, unit FROM {measurement} WHERE "hostname" = '{hostname}' AND "service" = '{service}' AND "metric" = '{metric}' AND "time" > (now() - {time}) """.format(**dic)

    def export_to_csv(self, host, service, _input, _output):
        """Export the data to csv"""
        path = self.args.report_csv_path
        if not path.endswith("/"):
            path += "/"

        date = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        pd.DataFrame(_input ).to_csv(path +  f"input-{host}-{service}-{date}.csv")
        pd.DataFrame(_output).to_csv(path + f"output-{host}-{service}-{date}.csv")

    def get_first_of_month(self):
        """Get the first day of this month"""
        today = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        first = "-".join(today.split("-")[:2]) + "-01-00:00:00"
        logger.info("Today is %s the first of the month is %s", today, first)
        return datetime.fromisoformat(first)

    def get_seconds_from_first_of_month(self):
        """Return how many seconds have passed form the first of the month"""
        first = self.get_first_of_month()
        logger.info(datetime.today())
        delta = datetime.today() - first
        return delta.total_seconds()

    def get_time_grid(self):
        """Return the array of timestamps from the 00:00 of the first of the month using steps of 5 minutes.
        e.g. [2019/10/01-00:00:00, 2019/10/01-00:05:00, 2019/10/01-00:10:00] but in timestamp.""" 
        start = self.get_first_of_month()
        # Rounding the values to the LAST multiple of 5 minutes. 18:28 will be rounded to 18:25
        n_of_points = int(self.get_seconds_from_first_of_month() / (5 * 60)) 
        return [
            datetime.timestamp(start + timedelta(minutes=5*i))
            for i in range(n_of_points)
        ]

    def get_closest_points(self, values, timestamp):
        """Find the two closest point to the timestamp, a[i-1] < v <= a[i]"""
        times = np.array([x[0] for x in values])
        # ASSUMPTION the values must be sorted, this should not be a problem since INFLUX should sort them for us
        # ASSUMPTION the value ar sorted from the smallest to the biggest
        # Chosen the left so a[i-1] < v <= a[i] so it can works if the point has the same timestamp of the analysis
        idx = np.searchsorted(times, timestamp, side="left")
        if idx == 0:
            # IF the data it's the first, consider it starting from 0
            return (-1, 0), values[0]
        elif idx == len(values) - 1:
            # IF recent data miss, consider it 0 because it might be off
            return values[-1], (len(values), 0)
        else:
            # Else return the two values
            return values[idx - 1], values[idx]

    def interpolate(self, values, timestamp):
        """Linear inerpolation of the values https://en.wikipedia.org/wiki/Linear_interpolation"""
        t_0, v_0 = values[0][0], values[0][1]
        t_1, v_1 = values[1][0], values[1][1]
        result = v_0 * (t_1 - t_0) + v_1 * (timestamp - t_0)
        return result / (t_1 - t_0)

    def value_aligner(self, values):
        """Interpolate data so that we have aligned data at each 5 minutes"""
        time = self.get_time_grid()
        closest = [
            self.get_closest_points(values, t) for t in time
        ]
        return [
            self.interpolate(values, timestamp) for timestamp, values in zip(time, closest)
        ]


    def calculate_statistics(self, _input, _output, _value, total_precision):
        """Calculate all the metrics for the values"""
        # Calculate the quantile
        index = int(len(_value) * self.args.quantile)
        _value.sort()
        cutted_values = _value[:index]
        self.quantile = np.max(cutted_values)
        # Alternative method
        # self.quantile  = np.quantile(_value,  self.args.quantile)

        self.max    = max(_value)
        self.input  = np.mean(_input)
        self.output = np.mean(_output)

        # The difference between the quantile and the bandwith  converted to a fee
        self.burst = self.args.penalty * (self.quantile - self.args.max) 
        
        self.precision = total_precision / len(self.host_and_services)

    def format_result(self):
        """Print in the standard way the metrics so that telegraph can parse them"""
        result = f"""Il {self.args.quantile * 100:.0f}th percentile calcolato e' {self.quantile:.0f}Mbit"""
        result += " | "
        result += ", ".join([
            f"""bandwith_stats_95th={self.quantile:.0f}Mbit""",
            f"""bandwith_stats_max={self.max:.0f}Mbit""",
            f"""bandwith_stats_in={self.input:.0f}Mbit""",
            f"""bandwith_stats_out={self.output:.0f}Mbit""",
            f"""bandwith_stats_precision={self.precision:.0f}%""",
            f"""bandwith_stats_burst={self.burst:.2f}""",
            ])
        return result

    def parse_UTC_time(self, time):
        """Parse an UTC time to epoch"""
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").timestamp()

    def normalize_data(self, value):
        """Convert the list of dictionaries to a list of (time, value) and convert the value from bytes to bits"""
        byte_to_bit_coeff = 8
        return  [
            (
                self.parse_UTC_time(point["time"]),
                point["value"] * byte_to_bit_coeff
            )
            for point in value
        ]

    def run(self):
        """Main routine, it gather the data from all the host and services and it calculate the statistics on them"""
        logger.info("Going to connect to the DB")
        dg = DataGetter()

        n_of_points = len(self.get_time_grid())

        total_input_bandwith  = np.zeros(n_of_points)
        total_output_bandwith = np.zeros(n_of_points)
        total_bandwith_value  = np.zeros(n_of_points)
        total_precision       = 0

        for host, service in self.host_and_services:
            logger.info(f"Analyzing {host}:{service}")
            logger.info("Gathering the data for the input Bandwith")
            _input  = dg.exec_query(self.construct_query(self.args.input, host, service))
            logger.info("Gathering the data for the output Bandwith")
            _output = dg.exec_query(self.construct_query(self.args.output, host, service))

            if self.args.report_csv:
                self.export_to_csv(host, service, _input, _output)

            # Calculate the precision
            total_precision += (min(len(_input), len(_output)) / n_of_points)
            
            # Create two lists for the values of input and output in the form of [(t, v), ...]
            _input = self.normalize_data(_input)
            _output = self.normalize_data(_output)
            

            pd.DataFrame(_input).to_csv(f"./test.csv")

            # Aling data aligning it to 5-minutes interpolating the data
            logger.info(f"Aligning the data to setp of 5 minutes from the first day of the month")
            _input  = np.array(self.value_aligner(_input))
            _output = np.array(self.value_aligner(_output))

            pd.DataFrame(_input).to_csv(f"./test_aligned.csv")

            # Convert from bytes to Mbit
            bit_to_Mbit_coeff = (1024*1024)
            _input  /= bit_to_Mbit_coeff
            _output /= bit_to_Mbit_coeff

            # Update the total_input bandwith by summing all the traffic
            total_input_bandwith  += _input
            total_output_bandwith += _output

            # Select the puntual maximum
            _value = np.array(
                [max(i, o) for i, o in zip(_input, _output)],
                dtype=np.float)
            # Update the total puntual maximum
            total_bandwith_value += _value


        logger.info("Calculating the quantile and the other metrics")
        self.calculate_statistics(total_input_bandwith, total_output_bandwith, total_bandwith_value, total_precision)

        # Print the results
        logger.info("Formatting the formatted results:")
        result = self.format_result()
        logger.info("Printing the results")
        print(result)

if __name__ == "__main__":
    MainClass().run()
