# QuantileChecker
Script che legge i dati **dal primo del mese a questo istante** di input ed output e calcola il 95-esimo percentile dei dati e altre statistiche. Si possono anche fare calcoli aggregati nel caso uno o piu' servizi su uno o piu' host siano associati.

# Introduzione

### Spiegazione del quantile e come viene calcolato
Supponiamo di avere dei dati di bandwidth in ingresso da uno switch:
![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/singolo_valore_iniziale.png)

Per calcolare il quantile, la prima cosa da fare e' ordinare tutti i valori dal piu' piccolo al piu' grande:

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/singolo_valore_ordinato.png)

Ora, il 95-esimo percentile e' quel valore tale per cui ci c'e' il 5% di valori **maggiori** ed il 95% di valori **minori**.

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/singolo_valore_quantile.png)

Quindi una volta individuato il punto, avremo il 5% di valori a destra e il 95% dei valori a sinistra.

Il che si traduce nel fatto che sul grafico orignale avremo il 5% dei punti **sopra** il quantile e il 95% dei punti **sotto**.

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/singolo_valore_esempio.png)

## Come aggreghiamo Input ed Output?
Nel esempio dello switch avremo sia bandwidth di input che di output:
![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/in_out_iniziale.png)

Quello che andremo a fare e' prendere il **massimo puntuale**, quindi per ogni istante di tempo prendiamo il massimo valore tra input ed output:

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/in_out_max.png)

Il risultato e':

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/in_out_solo_max.png)

## Cosa succede se un servizio e' distribuito su piu' switch?

Ci troveremo in una situazione come la seguente:

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/multipli_iniziale.png)

Andremo ad sommare i massimi di bandwidth utilizzate dagli switches.
Cosi da ottenere efettivamente il massimo consumo di bandwidth del servizio.
Per ottenere il massimo consumo di bandwidth del servizio dovremo sommare i massimi di bandwidth utilizzate dagli switches.

Pero' insorge un problema, per poter sommare i **punti** devono avere **lo stesso timestamp**.

Ma, poiche' e' imporbabile che le statistiche degli switches siano salvate sempre nello stesso istante, non e' detto che ad un punto di uno switch ne corrisponda uno del altro ma probabilmente vi sara' un piccolo disallineamento:

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/multipli_allineamento.png)


Una strategia per risolvere questo problema e' quello di andare a **creare** i punti dove non ci sono, nello specifico, il metodo adottato si chiama Interpolazione Lineare.

## Intrpolazione Lineare

L'idea e' quella di selezionare i **due punti piu' vicini al tempo cercato**:

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/interpolazione_iniziale.png)

E poi andare a "scegliere" il punto sul segmento che unisce i due punti:

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/interpolazione_finale.png)

Quindi per "allineare" i dati provenienti da piu' switches noi andremo a **creare** i punti per ogni multiplo di 5 minuti. 

Cioe' ad esempio per [12:00, 12:05, 12:10, 12:15, 12:20, 12:25, ...]

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/interpolazione_esempio.png)

Nel grafico possiamo vedere i punti "scelti" dalla Interpolazione lineare (in rosso), scegliendo punti ogni 5 minuti, sui dati iniziali (in blu).

## Considerazioni:

![](https://github.com/zommiommy/quantile_checking/raw/master/doc/imgs/interpolazione_finale.png)

Il punto creato C sara' sempre maggiore o uguale di A e minore o uguale di B.
E viceversa se il segmento e' descrescente invece che crescente.

**Questo implica che se andremo a calcolare la media sui dati interpolati, questa sara' leggermnete minore di quella sui dati originali.**

**Inoltre, se vi e' un crash e quindi per lunghi periodi andremo a non avere punti, il consumo effettivo sara' leggermnete sovra-stimato poiche' non avremo il "buco" ma un segmento che unisce l'ultimo dato prima del buco e il primo dopo.**

Quindi se il primo dato dopo il "buco" coincide con l'ultimo prima, andremo ad analizzare come se il consumo fosse stato costante! Questo pero' non e' un problema nel caso si compri il servizio in base alla banda massima utilizzabile invece che sul utilizzo.


# Implementazione

### Schema aspettato:
```
time  hostname  service  metric  value  unit
----  --------  -------  ------  -----  ----
```
Inoltre **attualmente** ci aspettiamo che unit sia sempre `bits` e percio' non e' controllata.

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
                        passed as HOSTNAME|SERVICE. One can use this argument
                        multiple times to select multiple hosts and services

query settings:
  -I INPUT, --input INPUT
                        The name of the input bandwidth metric, default-
                        value='inBandwidth'
  -O OUTPUT, --output OUTPUT
                        The name of the output bandwidth metric, default-
                        value='outBandwidth'
  -rc, --report-csv     Flag, if enabled the data read from the DB are dumped
                        as a CSV
  -rcp REPORT_CSV_PATH, --report-csv-path REPORT_CSV_PATH
                        Path where to save the data used, default-value='./'

Fee settings:
  -m MAX, --max MAX     The maxiumum ammount of Bandwidth usable in Mbit/s
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
$ python src/main.py -M disk -HS test.local.it|Diskspace -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwidth_stats_95th=261745Mib, bandwidth_stats_max=261749Mib, bandwidth_stats_in=128200Mib, bandwidth_stats_out=128200Mib, bandwidth_stats_precision=1%, bandwidth_stats_burst=1
```
Oppure usando il wrapper che va ad usare l'environment `quantile_env`:
```bash
$ ./bin/quantile_checker -M disk -HS test.local.it|Diskspace  -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwidth_stats_95th=261745Mib, bandwidth_stats_max=261749Mib, bandwidth_stats_in=128200Mib, bandwidth_stats_out=128200Mib, bandwidth_stats_precision=1%, bandwidth_stats_burst=1
```

Inoltre e' possibile specificare piu' host e servizi:
```bash
$ ./bin/quantile_checker -M disk -HS test1.local.it|Diskspace -HS test1.local.it|CpuUsage -HS test2.local.it|Diskspace -I Win -O Win --max 1000 -p 3
Il 95th percentile calcolato e' 261745Mib | bandwidth_stats_95th=261745Mib, bandwidth_stats_max=261749Mib, bandwidth_stats_in=128200Mib, bandwidth_stats_out=128200Mib, bandwidth_stats_precision=1%, bandwidth_stats_burst=1
```

## Riasunto dei dettagli di calcolo
Lo script scarica i dati singolarmente per ogni coppia host-servizio.

Lo script si aspetta un punto ogni 5 minuti.

Calcola la precisione come il rapporto tra il numero di punti aspettati e quelli attuali.
Per ogni coppia host-servizio viene tenuta la precisione minima tra input ed output.

I dati successivamente vengono "normalizzati" allineandoli sui 5-minuti. (Quindi dopo questo passaggio avremo punti sempre e solo su orari come 8:00, 8:05, 8:10).
Questo allineamento e' fatto [interpolando linearmente](https://en.wikipedia.org/wiki/Linear_interpolation) i dati, se non ci sono dati "recenti" viene considerato 0 il valore attuale.

Successivamente, i dati di input ed output, gia' allineati, vengono sommati con quelli delle altre coppie host-servizio.

Inoltre viene calcolato il massimo puntuale dei valori e su questo viene calcolato il quantile.

## Descrizione delle metrics
- `bandwidth_stats_95th` il percentile della banda
- `bandwidth_stats_max` il massimo valore della banda
- `bandwidth_stats_in`  media della banda in input
- `bandwidth_stats_out` media della banda in output 
- `bandwidth_stats_burst` penale calcolata sul traffico in eccesso
- `bandwidth_stats_precision` rapporto tra il numero di punti aspettati e il numero di punti reali

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
