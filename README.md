# QuantileChecker
Script che legge i dati **dal primo del mese a questo istante** di input ed output e calcola il 95-esimo percentile dei dati e altre statistiche. Si possono anche fare calcoli aggregati nel caso uno o piu' servizi su uno o piu' host siano associati.

### Schema aspettato:
```
time  hostname  service  metric  value  unit
----  --------  -------  ------  -----  ----
```
Inoltre **attualmente** ci aspettiamo che unit sia sempre `bytes`.

Il valore di `time` dovra' essere una epoch espressa in nanosecondi come standard InfluxDB.
## Descrizione Utilizzo
```bash
$ ./bin/quantile_checker -h
usage: main.py [-h] -M MEASUREMENT -HS HOSTNAME_SERVICE [-I INPUT] [-O OUTPUT]
               [-rc] [-rcp REPORT_CSV_PATH] -m MAX -p PENALTY [-q QUANTILE]
               [-t TIME] [-v {0,1,2}]

QuantileChecker is a free software developed by Tommaso Fontana for Wurth
Phoenix S.r.l. under GPL-2 License.

optional arguments:
  -h, --help            show this help message and exit

required settings:
  -M MEASUREMENT, --measurement MEASUREMENT
                        Measurement where the data will be queried.
  -HS HOSTNAME_SERVICE, --hostname-service HOSTNAME_SERVICE
                        The hostname and service to select, those must be
                        passed as HOSTNAME:SERVICE. One can use this argument
                        multiple times to select multiple hosts and services

query settings:
  -I INPUT, --input INPUT
                        The name of the input bandwith metric, default-
                        value='inBandwidth'
  -O OUTPUT, --output OUTPUT
                        The name of the output bandwith metric, default-
                        value='outBandwidth'
  -rc, --report-csv     Flag, if enabled the data read from the DB are dumped
                        as a CSV
  -rcp REPORT_CSV_PATH, --report-csv-path REPORT_CSV_PATH
                        Path where to save the data used, default-value='./'

Fee settings:
  -m MAX, --max MAX     The maxiumum ammount of Bandwith usable in Mbit/s
  -p PENALTY, --penalty PENALTY
                        The fee in euros/(Mbit/s) in case of the threshold is
                        exceded
  -q QUANTILE, --quantile QUANTILE
                        The quantile to confront with the threshold. it must
                        be between 0 and 1. The default value is 0.95 so the
                        95th percentile
  -t TIME, --time TIME  The timewindow to calculate the percentile, if not
                        specified it is considered the time from the first day
                        of the current month.

verbosity settings (optional):
  -v {0,1,2}, --verbosity {0,1,2}
                        set the logging verbosity, 0 == CRITICAL, 1 == INFO, 2
                        == DEBUG it defaults to ERROR.
```

## Esempio di utilizzo
Chiamamando lo script direttamente:
```bash
$ python src/main.py -M disk -HS test.local.it:Diskspace -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwith_stats_95th=261745Mib, bandwith_stats_max=261749Mib, bandwith_stats_in=128200Mib, bandwith_stats_out=128200Mib, bandwith_stats_precision=1%, bandwith_stats_burst=1
```
Oppure usando il wrapper che va ad usare l'environment `quantile_env`:
```bash
$ ./bin/quantile_checker -M disk -HS test.local.it:Diskspace  -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwith_stats_95th=261745Mib, bandwith_stats_max=261749Mib, bandwith_stats_in=128200Mib, bandwith_stats_out=128200Mib, bandwith_stats_precision=1%, bandwith_stats_burst=1
```

Inoltre e' possibile specificare piu' host e servizi:
```bash
$ ./bin/quantile_checker -M disk -HS test1.local.it:Diskspace -HS test1.local.it:CpuUsage -HS test2.local.it:Diskspace -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwith_stats_95th=261745Mib, bandwith_stats_max=261749Mib, bandwith_stats_in=128200Mib, bandwith_stats_out=128200Mib, bandwith_stats_precision=1%, bandwith_stats_burst=1
```

## Dettagli di calcolo
Lo script scarica i dati singolarmente per ogni coppia host-servizio.

Lo script si aspetta un punto ogni 5 minuti.

Calcola la precisione come il rapporto tra il numero di punti aspettati e quelli attuali.
Per ogni coppia host-servizio viene tenuta la precisione minima tra input ed output.

I dati successivamente vengono "normalizzati" allineandoli sui 5-minuti. (Quindi dopo questo passaggio avremo punti sempre e solo su orari come 8:00, 8:05, 8:10).
Questo allineamento e' fatto [interpolando linearmente](https://en.wikipedia.org/wiki/Linear_interpolation) i dati, se non ci sono dati "recenti" viene considerato 0 il valore attuale.

Successivamente, i dati di input ed output, gia' allineati, vengono sommati con quelli delle altre coppie host-servizio.

Inoltre viene calcolato il massimo puntuale dei valori e su questo viene calcolato il quantile.

## Descrizione delle metrics
- `bandwith_stats_95th` il percentile della banda
- `bandwith_stats_max` il massimo valore della banda
- `bandwith_stats_in`  media della banda in input
- `bandwith_stats_out` media della banda in output 
- `bandwith_stats_burst` penale calcolata sul traffico in eccesso
- `bandwith_stats_precision` rapporto tra il numero di punti aspettati e il numero di punti reali

## Descrizione Ambiente Python
Lo script per andare deve essere eseguito su un ambiente python 3 con le seguenti librerie:
```
Package         Version  
--------------- ---------
certifi         2019.6.16
chardet         3.0.4    
idna            2.8      
influxdb        5.2.2    
joblib          0.13.2   
numpy           1.16.4   
pandas          0.24.2   
pip             19.1.1   
python-dateutil 2.8.0    
pytz            2019.1   
requests        2.22.0   
scikit-learn    0.21.2   
scipy           1.3.0    
setuptools      40.8.0   
six             1.12.0   
sklearn         0.0      
urllib3         1.25.3   
```
nella cartella `quantile_env` c'e' un ambiente miniconda gia' configurato.