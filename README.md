# QuantileChecker
Script che legge i dati **delle ultime 24 ore** di input ed output e calcola il 95-esimo percentile dei dati e altre statistiche.

### Schema aspettato:
```
time  hostname  service  metric  value  unit
----  --------  -------  ------  -----  ----
```

## Esempio di utilizzo
Chiamamando lo script direttamente:
```bash
$ python src/main.py -M disk -S Diskspace -H rt-sccm01-p1.idolrt.regione.toscana.it -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwith_stats_95th=261745Mib, bandwith_stats_max=261749Mib, bandwith_stats_in=128200Mib, bandwith_stats_out=128200Mib, bandwith_stats_precision=1%, bandwith_stats_burst=1
```
Oppure usando il wrapper che va ad usare l'environment `quantile_env`:
```bash
$ ./bin/quantile_checker -M disk -S Diskspace -H rt-sccm01-p1.idolrt.regione.toscana.it -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwith_stats_95th=261745Mib, bandwith_stats_max=261749Mib, bandwith_stats_in=128200Mib, bandwith_stats_out=128200Mib, bandwith_stats_precision=1%, bandwith_stats_burst=1
```
