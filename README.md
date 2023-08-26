# INIZIALIZZARE IL SITO

Con l'inizializzazione del sito vengono eliminati tutti i dati presenti all'interno della directory, compresi i risultati salvati e gli allegati inseriti fino a questo momento. Se vuoi davvero fare questo, allora lancia questo comando nella directory del progetto

```
python build_site.py
```

Fatto questo, il sito sarà inizializzato e pronto all'uso.


### INSTALLARE django

```
pip install django=3.2
```

### AVVIARE IL SITO

Per avviare il sito lancia questo comando nella directory del progetto

```
python manage.py runserver
```

Poi apri questo link http://127.0.0.1:8000/esame

### RICORDATI DI AVVIARE TALIGHT

Se non avvii il server TALight non potrai utilizzarne i servizi! 
Lancia il comando

```
./rtald -d ~/TALight/example_problems/tutorial
```
