# QuantileChecker
Script che legge i dati **delle ultime 24 ore** di input ed output e calcola il 95-esimo percentile dei dati e altre statistiche.

### Schema aspettato:
```
time  hostname  service  metric  value  unit
----  --------  -------  ------  -----  ----
```
## Descrizione Utilizzo
```bash
$./bin/quantile_checker -h
usage: main.py [-h] -H HOSTNAME -S SERVICE -M MEASUREMENT [-I INPUT]
               [-O OUTPUT] [-rc] [-rcp REPORT_CSV_PATH] -m MAX -p PENALTY
               [-q QUANTILE] [-t TIME] [-qt {max,common}] [-v {0,1,2}]

QuantileChecker is a free software developed by Tommaso Fontana for Wurth
Phoenix S.r.l. under GPL-2 License.

optional arguments:
  -h, --help            show this help message and exit

query settings (required):
  -H HOSTNAME, --hostname HOSTNAME
                        The hostname to select
  -S SERVICE, --service SERVICE
                        The service to select
  -M MEASUREMENT, --measurement MEASUREMENT
                        Measurement where the data will be queried.
  -I INPUT, --input INPUT
                        The name of the input bandwith
  -O OUTPUT, --output OUTPUT
                        The name of the output bandwith
  -rc, --report-csv     Flag, if enabled the data read from the DB are dumped
                        as a CSV
  -rcp REPORT_CSV_PATH, --report-csv-path REPORT_CSV_PATH
                        Path where to save the data used

Fee settings:
  -m MAX, --max MAX     The maxiumum ammount of Bandwith usable
  -p PENALTY, --penalty PENALTY
                        The fee in euros inc ase of the threshold is exceded
  -q QUANTILE, --quantile QUANTILE
                        The quantile to confront with the threshold
  -t TIME, --time TIME  The timewindow to calculate the percentile
  -qt {max,common}, --quantile-type {max,common}
                        How the quantilie is going to be calculated 'merging'
                        the input and output traffic

verbosity settings (optional):
  -v {0,1,2}, --verbosity {0,1,2}
                        set the logging verbosity, 0 , 2
                        == DEBUG it defaults to ERROR.
```

## Esempio di utilizzo
Chiamamando lo script direttamente:
```bash
$ python src/main.py -M disk -S Diskspace -H test.local.it -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwith_stats_95th=261745Mib, bandwith_stats_max=261749Mib, bandwith_stats_in=128200Mib, bandwith_stats_out=128200Mib, bandwith_stats_precision=1%, bandwith_stats_burst=1
```
Oppure usando il wrapper che va ad usare l'environment `quantile_env`:
```bash
$ ./bin/quantile_checker -M disk -S Diskspace -H test.local.it -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwith_stats_95th=261745Mib, bandwith_stats_max=261749Mib, bandwith_stats_in=128200Mib, bandwith_stats_out=128200Mib, bandwith_stats_precision=1%, bandwith_stats_burst=1
```
### Modalita' di calcolo del 95-th percentile
Poiche' Input ed Output sono metriche diverse bisogna aggregare il calcolo per avere una unica threshold.
Esistono varie modalita' di aggregazione, quelle implementate sono:
- `max` il quale setta la threshold al quantile massimo tra quello di Input e di Output
- `common` il quale calcola il quantile "unendo" i dati di input ed output.

## Descrizione delle metrics
- `bandwith_stats_95th` il percentile della banda
- `bandwith_stats_max` il massimo valore della banda
- `bandwith_stats_in`  media della banda in input
- `bandwith_stats_out` media della banda in output 
- `bandwith_stats_burst` penale calcolata sul traffico in eccesso
- `bandwith_stats_precision`