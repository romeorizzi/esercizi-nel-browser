import os
import shutil
import ast
import ruamel

from datetime import datetime
from django.shortcuts import render,redirect
from django.contrib import messages
from .forms import answer,uploaded_file
from ansi2html import Ansi2HTMLConverter
from django.core.files.storage import FileSystemStorage
from pathlib import Path

import rtal_lib as rl

home = str(Path.home())
FEEDBACKS = os.path.join(home,'/home/orion/Git/esercizi-nel-browser/simulazione_esame/browser_feedback_log/feedbacks.yaml') # yaml contenente i feedback suddivisi per esercizio e per task
FEEDBACK_SAVED_LOG = os.path.join(home,'/home/orion/Git/esercizi-nel-browser/simulazione_esame/browser_feedback_log/feedback_saved_log.yaml')  # yaml contenente i feedback salvati suddivisi per esercizio e per task
POINTS_YAML = '/home/orion/Git/esercizi-nel-browser/simulazione_esame/browser_feedback_log/points.yaml'  # yaml contenente i punti suddivisi per esercizio e per task
SAVED_SCORES = '/home/orion/Git/esercizi-nel-browser/simulazione_esame/browser_feedback_log/saved_scores.yaml'  # yaml contenente i punti relativi agli esercizi salvati suddivisi per esercizio e per task
RTAL_URL='ws://127.0.0.1:8008' # connessione a localhost porta 8008

# Il dizionario 'contexts' contiene tutte le informazioni utili ad ogni esercizio. Abbiamo deciso
# di gestire il salvataggio dei dati tramite file yaml, percio' dobbiamo tenere traccia per ogni
# esercizio e per ogni task del punteggio e dei feedback. In generale, assegnamo a ogni esercizio
# il suo context, il quale avra' nome context_ESERCIZIO (e.g. context_knapsack, context_lcs, ...).
# La struttura di contexts è la seguente (ogni nodo rappresenta una entry del dizionario):

# contexts
#  |
#  |_ context_knapsack: identifica a quale problema si riferisce il context
#  |    |
#  |    |_data: raccoglitore dei dati dell'esercizio
#  |        |
#  |        |_task01
#  |        |   |
#  |        |   |_question: domanda relativa alla task01
#  |        |   |
#  |        |   |_feedback: feedback di TALight alla soluzione dell'utente (quando prodotto)
#  |        |   |
#  |        |   |_goals: nome dei goal per la task01
#  |        |
#  |        |_task02
#  |        |   |
#  |        |   |_question: domanda relativa alla task02
#  |        |   |
#  |        |   |_feedback: feedback di TALight alla soluzione dell'utente (quando prodotto)
#  |        |   |
#  |        |   |_goals: nome dei goal per la task02
#  |        |
#  |        .
#  |        .
#  |        .
#  |
#  |_ context_lcs
#  |
#  .
#  .
#  .

# Fondamentalmente, il dizionario contexts contiene tutte le informazioni correntemente presenti
# sul sito e che possono anche essere trasferite su uno yaml (ad esempio, ogni feedback viene 
# riportato sul file yaml che raccoglie tutti i feedback di TALight riguardanti le ultime
# sottomissioni dell'utente). In pratica tutto ciò che viene visualizzato sul sito è contenuto
# in contexts.

contexts = {'context_knapsack': {'data'  :{'task01': {'question': "<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente CapacityMax= 36 fornirne uno in cui sia massima la somma dei valori.<br>Inserisci la tua risposta in forma di lista di oggetti da prendere (esempio: ['C', 'F', 'A'])\nopt_sol1=[]\n<br>Specificare il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi):\nopt_val1=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label>In ogni richiesta del presente esercizio lo zaino disponibile avrà capienza al più CapacityMax = 36  e dovrai scegliere quali prendere da un sottoinsieme degli oggetti con nome, peso e valore come da seguente tabella:\n\n|      |   A |   B |   C |   D |   E |   F |   G |   H |   I |   L |   M |   N |\n|:-----|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|\n| peso |  15 |  16 |  17 |  11 |  13 |   5 |   7 |   3 |   1 |  12 |   9 |   7 |\n| val  |  50 |  52 |  54 |  40 |  45 |  17 |  18 |   7 |   8 |  42 |  30 |  22 |</label>'},'task02': {'question': '<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 32</b>, fornirne uno in cui sia massima la somma dei valori.</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task03': {'question': '<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 30</b>, fornirne uno in cui sia massima la somma dei valori.</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task04': {'question': '<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 28</b>, fornirne uno in cui sia massima la somma dei valori.</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label>Nelle successive richieste alcuni degli oggetti saranno proibiti, oppure obbligati</label>'},'task05': {'question': "<label>Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['E'].</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task06': {'question': "<label>Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E'].</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task07': {'question': "<label>Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E', 'F'].</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task08': {'question': "<label>Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere</b> tutti gli elementi in ['B', 'E'].</label>", 'feedback': '', 'goals': ['opt_val'], 'descr_before_task': '<label></label>'},'task09': {'question': "<label>Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'F'] e <b>nessuno</b> di quelli in ['E'].</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task10': {'question': "<label>Fornire una soluzione ottima se <b>31 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'I'] e <b>nessuno</b> di quelli in ['F', 'E'].</label>", 'feedback': '', 'goals': ['opt_sol'], 'descr_before_task': '<label></label>'},}},'context_lcs': {'data'  :{'task01': {'question': '<label>Fornire una massima sottosequenza comune tra le due stringhe<br/>s = AAGCGAGATAGCCGGT<br/>t = ATAACCGATACAAGTC.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol1=""\\n<br>e la sua lunghezza:\\nopt_val1=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label>Si considerino le seguenti sequenze di caratteri:<br/><br/> s = AAGCGAGATAGCCGGT <br/>  t = ATAACCGATACAAGTC</label>'},'task02': {'question': '<label>Fornire una stringa di lunghezza massima che inizi col prefisso CC e sia sottosequenza comune tra<br/>s = AAGCGAGATAGCCGGT<br/>t = ATAACCGATACAAGTC.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol2=""\\n<br>e la sua lunghezza:\\nopt_val2=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task03': {'question': '<label>Fornire una massima sottosequenza comune tra<br/><b>il suffisso </b> $s\\\'$ = AGCGAGATAGCCGGT di s e <br/>t = ATAACCGATACAAGTC.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol3=""\\n<br>e la sua lunghezza:\\nopt_val3=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task04': {'question': '<label>Fornire una massima sottosequenza comune tra<br/><b>il suffisso </b> $s\\\'$ = AGATAGCCGGT di s e <br/>t = ATAACCGATACAAGTC.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol4=""\\n<br>e la sua lunghezza:\\nopt_val4=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task05': {'question': '<label>Fornire una massima sottosequenza comune tra<br/><b>il suffisso </b> $s\\\'$ = ATAGCCGGT di s e <br/>t = ATAACCGATACAAGTC.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol5=""\\n<br>e la sua lunghezza:\\nopt_val5=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task06': {'question': '<label>Fornire una massima sottosequenza comune tra<br/><b>il suffisso</b>  $t\\\'$ = ACCGATACAAGTC di t e <br/>s = AAGCGAGATAGCCGGT.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol6=""\\n<br>e la sua lunghezza:\\nopt_val6=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task07': {'question': '<label>Fornire una massima sottosequenza comune tra<br/><b>il suffisso</b>  $t\\\'$ = CGATACAAGTC di t e <br/>s = AAGCGAGATAGCCGGT.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol7=""\\n<br>e la sua lunghezza:\\nopt_val7=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task08': {'question': '<label>Fornire una massima sottosequenza comune tra<br/><b>il suffisso</b>  $t\\\'$ = ATACAAGTC di t e <br/>s = AAGCGAGATAGCCGGT.<br>Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol8=""\\n<br>e la sua lunghezza:\\nopt_val8=7</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},}},'context_mst': {'data'  :{'task01': {'question': '<label>Fornire un albero ricoprente di peso minimo e specificarne il peso complessivo.<br>Inserisci la tua risposta in forma di lista di archi da prendere (esempio: [0, 3, 4, 6])\nopt_sol1=[]\n<br>Specificare il peso della soluzione introdotta (un intero, la somma dei pesi degli archi presi):\nopt_val1=-1</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label>Ogni richiesta del presente esercizio farà riferimento al grafo G offerto nel seguente riquadro. Il grafo G ha 5 nodi, labellati coi primi 5 numeri naturali e 8 archi pesati, labellati coi primi 8 numeri naturali. La lista ordinata degli archi è [({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]. Ecco una rappresentazione di G (da quì puoi scaricarti G in vari formati):\n\nedge_weighted_graph_2picture(n=5,m=8,edges=[[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]])</label>', 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},'task02': {'question': '<label>Specificare quanti siano gli alberi ricoprenti di peso minimo.<br>Inserisci la tua risposta (un intero, il numero di soluzioni ottime diverse):\nopt_val2=-1</label>', 'feedback': '', 'goals': ['num_opt_sols'], 'descr_before_task': '<label></label>', 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},'task03': {'question': '<label>Specificare quanti siano gli alberi ricoprenti di peso minimo.<br>Inserisci la tua risposta in questa cella di testo libero.</label>', 'feedback': '', 'goals': 'not a TALight verify service goal', 'descr_before_task': '<label></label>', 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},'task04': {'question': "<label>Dire, certificandolo, se l'arco ${query_edge}$ appartenga a tutti, oppure a nessuno, oppure a qualcuno ma non tutti gli alberi ricoprenti di peso minimo.<br>Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate4=''\n<br>Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate4=''\n<br>Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert4=[0,3,7,2]\nedgecut_cert4=[0,3,7,2]\ncutshore_cert4=[0,3,7,2]</label>", 'feedback': '', 'goals': ['edge_classification'], 'descr_before_task': '<label></label>', 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},'task05': {'question': "<label>Dire, certificandolo, se l'arco ${query_edge}$ appartenga a tutti, oppure a nessuno, oppure a qualcuno ma non tutti gli alberi ricoprenti di peso minimo.<br>Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate5=''\n<br>Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate5=''\n<br>Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert5=[0,3,7,2]\nedgecut_cert5=[0,3,7,2]\ncutshore_cert5=[0,3,7,2]</label>", 'feedback': '', 'goals': ['edge_classification'], 'descr_before_task': '<label></label>', 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},'task06': {'question': "<label>Dire, certificandolo, se l'arco ${query_edge}$ appartenga a tutti, oppure a nessuno, oppure a qualcuno ma non tutti gli alberi ricoprenti di peso minimo.<br>Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate6=''\n<br>Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate6=''\n<br>Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert6=[0,3,7,2]\nedgecut_cert6=[0,3,7,2]\ncutshore_cert6=[0,3,7,2]</label>", 'feedback': '', 'goals': ['edge_classification'], 'descr_before_task': '<label></label>', 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},'task07': {'question': "<label>Fornire un albero ricoprente di peso minimo tra quelli forzati a contenere l'arco ${forced_in}$. Specificare il peso complessivo della tua soluzione.<br>Inserisci la tua risposta in forma di lista di archi da prendere (esempio: [0, 3, 4, 6])\nopt_sol7=[]\n<br>Specificare il peso della soluzione introdotta (un intero, la somma dei pesi degli archi presi):\nopt_val7=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>', 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},}},}

scores = {'score_knapsack': {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0},'score_lcs': {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0},'score_mst': {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0},}

costs = [15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]
labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N']
vals = [50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]
s = 'AAGCGAGATAGCCGGT'
t = 'ATAACCGATACAAGTC'
edges = '[(A,B)(B,T)(T,A)(T,D)(A,F)(B,E)(E,F)]'
m = 7
n = 6

def write_to_yaml_feedback(yaml_path,exercise,task,feedback):
    # apro e leggo lo yaml contenente i feedback
    with open(yaml_path,'r') as stream:
        try:
            full_yaml_dict = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    # scrivo il feedback in base alla task a cui è riferito
    if task<10:
       full_yaml_dict[f'context_{exercise}']['data'][f'task0{task}']['feedback'] = feedback
    else:
        full_yaml_dict[f'context_{exercise}']['data'][f'task{task}']['feedback'] = feedback
    # apro lo yaml contenente i feedback e scrivo il nuovo feedback
    f = open(yaml_path,'w')
    ruamel.yaml.dump(full_yaml_dict, f, default_flow_style=False)
    f.close()

def get_scores(feedback):
    points = {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0}
    try: # se è un feedback contenente punti faccio il parsing
        pos1 = feedback.index('punti sicuri')
        pos2 = feedback[pos1:].index(':') + pos1
        pos3 = feedback[pos2:].index(']') + pos2
        if feedback[pos2+1:pos3] == ' None':
            points['punti_sicuri'] = 0
        else:
            points['punti_sicuri'] = int(feedback[pos2+1:pos3])
        pos1 = feedback.index('punti aggiuntivi possibili')
        pos2 = feedback[pos1:].index(':') + pos1
        pos3 = feedback[pos2:].index(']') + pos2
        if feedback[pos2+1:pos3] == ' None':
            points['punti_aggiuntivi_possibili'] = 0
        else:
            points['punti_aggiuntivi_possibili'] = int(feedback[pos2+1:pos3])
        pos1 = feedback.index('punti fuori portata')
        pos2 = feedback[pos1:].index(':') + pos1
        pos3 = feedback[pos2:].index(']') + pos2
        if feedback[pos2+1:pos3] == ' None':
            points['punti_fuori_portata'] = 0
        else:
            points['punti_fuori_portata'] = int(feedback[pos2+1:pos3])
    except: # se non è un feedback contenente punti vuol dire che non ho fatto punti
        pass
    return points

def html_score(ex):
    # traduco i colori in html
    green = '<font color="green">'
    red = '<font color="red">'
    blue = '<font color="blue">'
    close = '</font>'
    # Vado a leggermi i punteggi
    with open(POINTS_YAML,'r') as stream:
        try:
            points_dict = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    # punti totali per l'esercizio
    punti_sicuri = 0
    punti_aggiuntivi_possibili = 0
    punti_fuori_portata = 0
    # sommo i punti di tutte le task
    for task in points_dict[ex].keys():
        punti_sicuri += points_dict[ex][task]['punti_sicuri']
        punti_aggiuntivi_possibili += points_dict[ex][task]['punti_aggiuntivi_possibili']
        punti_fuori_portata += points_dict[ex][task]['punti_fuori_portata']
    # li riporto qui associando i colori ai punti (verde = sicuri, blu = possibili, rosso = fuori portata)
    html_ps = f'{green}{punti_sicuri}/{ex_tot_points[ex]}{close}'
    html_pa = f'{blue}{punti_aggiuntivi_possibili}/{ex_tot_points[ex]}{close}'
    html_pf = f'{red}{punti_fuori_portata}/{ex_tot_points[ex]}{close}'
    return {'punti_sicuri': html_ps, 'punti_aggiuntivi_possibili': html_pa, 'punti_fuori_portata':html_pf}

def get_scores_from_feedbacks(FEEDBACK_YAML, POINTS_YAML):
    # apro lo yaml con i feedback
    with open(FEEDBACK_YAML,'r') as stream:
        try:
            feedback_dict = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    points_dict = {}
    for context in contexts.keys(): # per ogni esercizio
        esercizio = f'{context[8:]}'
        points_dict[esercizio] = {} # inizializzo il dizionario dei punti per l'esercizio
        for task in contexts[context]['data'].keys(): # per ogni task
            points_dict[esercizio][task] = {} # inizializzo il dizionario dei punti per la task
            feedback = contexts[context]['data'][task]['feedback'] # prendo il feedback
            scores = get_scores(feedback) # e ricavo i punti
            points_dict[esercizio][task]['punti_sicuri'] = scores['punti_sicuri']
            points_dict[esercizio][task]['punti_aggiuntivi_possibili'] = scores['punti_aggiuntivi_possibili']
            points_dict[esercizio][task]['punti_fuori_portata'] = scores['punti_fuori_portata']
    # riporto i punteggi nello yaml dei punti
    f = open(POINTS_YAML,'w')
    ruamel.yaml.dump(points_dict, f, default_flow_style=False)
    f.close()
    # modifico i punti totali degli esercizi
    for context in contexts.keys():
        esercizio = f'{context[8:]}'
        exam_context['data'][esercizio]['score'] = html_score(esercizio)

def get_goals(answer,task):
    answer_dict = {}
    for goal in task['goals']: # per ogni goal richiesto dalla task
    # prendo la soluzione dell'utente e provo a convertirla nei tre formati possibili (int, list, str)
    # quando riesco a farlo la associo al goal e genero answer_dict
        already_cast = 0
        try:
            answer_dict[goal] = int(answer.cleaned_data[f'ans_{goal}'])
            already_cast = 1
        except:
            pass
        try:
            answer_dict[goal] = ast.literal_eval(answer.cleaned_data[f'ans_{goal}'])
            already_cast = 1
        except:
            pass
        if not already_cast:
            answer_dict[goal] = answer.cleaned_data[f'ans_{goal}']
    return answer_dict

def get_select(answer,task):
    answer_dict = {}
    for select in task['select']: # per ogni select nel task
    # prendo la soluzione dell'utente e provo a convertirla nei tre formati possibili (int, list, str)
    # quando riesco a farlo la associo al goal e genero answer_dict
        already_cast = 0
        try:
            answer_dict[select] = int(answer.cleaned_data[f'ans_{select}'])
            already_cast = 1
        except:
            pass
        try:
            answer_dict[select] = ast.literal_eval(answer.cleaned_data[f'ans_{select}'])
            already_cast = 1
        except:
            pass
        if not already_cast:
            answer_dict[select] = answer.cleaned_data[f'ans_{select}']
    return answer_dict

def retrieve_saved_solutions(request,ex):
    context = f'context_{ex}' # prendo l'esercizio
    # apro e leggo lo yaml dei feedback salvati
    with open(FEEDBACK_SAVED_LOG,'r') as stream:
        try:
            saved_log_dict = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    # lo aggiorno con i feedback correnti
    for task in saved_log_dict[context]['data'].keys():
        feedback = saved_log_dict[context]['data'][task]['feedback']
        contexts[context]['data'][task]['feedback'] = feedback
        write_to_yaml_feedback(FEEDBACKS,ex,int(task[-2:]),feedback)
    print('\n***********************************\n')
    print('\nHo caricato gli ultimi risultati salvati come richiesto.\n')
    print('\n***********************************\n')
    return redirect(ex)

def save_scores(ex):
    # apro e leggo il file dei punteggi correnti
    with open(POINTS_YAML,'r') as stream:
        try:
            points = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    # apro e leggo il file dei punteggi salvati
    with open(SAVED_SCORES,'r') as stream:
        try:
            saved_scores = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    # sostituisco i punti salvati con i punti correnti
    saved_scores[ex] = points[ex]
    f = open(SAVED_SCORES,'w')
    ruamel.yaml.dump(saved_scores, f, default_flow_style=False)
    f.close()

def save_solutions(request,ex):
    context = f'context_{ex}' # prendo l'esercizio
    # apro e leggo il file dei feedback correnti
    with open(FEEDBACKS,'r') as stream:
        try:
            last_log_dict = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    # apro e leggo il file dei feedback salvati
    with open(FEEDBACK_SAVED_LOG,'r') as stream:
        try:
            saved_log_dict = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    # sostituisco i feedback salvati con i feedback correnti
    saved_log_dict[context] = last_log_dict[context]
    f = open(FEEDBACK_SAVED_LOG,'w')
    ruamel.yaml.dump(saved_log_dict, f, default_flow_style=False)
    f.close()
    print('\n***********************************\n')
    print('\nHo salvato i risultati come richiesto.\n')
    print('\n***********************************\n')
    save_scores(ex)
    return redirect(ex)

def simple_upload(request,ex,task):
    if request.method == 'POST' and request.FILES['myfile']:
        update_dir = os.path.join(os.getcwd(),'simulazione_esame',f'{ex}','allegati') # cartella di caricamento del file
        myfile = request.FILES['myfile']
        fs = FileSystemStorage(location=update_dir)
        time = datetime.now().strftime('%H:%M:%S')
        filename = fs.save(f'{task}_{myfile.name}_{time}', myfile) # aggiungo task e timestamp al nome del file
        return redirect(ex)

ex_tot_points = {'knapsack': 400,'lcs': 360,'mst': 440,}

exam_context = {'data'  :{'knapsack': {'title': 'knapsack', 'score': {'punti_sicuri':'<font color="green">0/400</font>', 'punti_aggiuntivi_possibili':'<font color="blue">0/400</font>','punti_fuori_portata':'<font color="red">0/400</font>'}},'lcs': {'title': 'lcs', 'score': {'punti_sicuri':'<font color="green">0/360</font>', 'punti_aggiuntivi_possibili':'<font color="blue">0/360</font>','punti_fuori_portata':'<font color="red">0/360</font>'}},'mst': {'title': 'mst', 'score': {'punti_sicuri':'<font color="green">0/440</font>', 'punti_aggiuntivi_possibili':'<font color="blue">0/440</font>','punti_fuori_portata':'<font color="red">0/440</font>'}},} }


def esame(request):
    return render(request, os.path.join('esame','esame.html'), exam_context)

context_knapsack = contexts['context_knapsack'] # dichiaro context_knapsack

score_knapsack = scores['score_knapsack'] # dichiaro score_knapsack

def knapsack(request): # definisco il nome della view 
    rtalproblem = 'RO_knapsack' # il corrispondente problema in TALight è RO_knapsack
    rtalservice = 'check' # vogliamo che venga richiesto il servizio check per il problema
    rtaltoken = 'id625tbt_VR437029_OrLwSWKtpyrk1bS_RIVO_CARAPUCCI' # dummy token
    instance_dict = {'costs': [15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7], 'labels': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'], 'vals': [50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]} # prendo i parametri dell'istanza
    ntasks = 10 # prendo il numero di task
    conv = Ansi2HTMLConverter(dark_bg = False) # inizializzo il convertitore HTML
    CapacityMax = 36
    costs = [15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]
    labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N']
    vals = [50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]
    task01= {'general_description_before_task': 'In ogni richiesta del presente esercizio lo zaino disponibile avrà capienza al più $CapacityMax$ = __36__  e dovrai scegliere quali prendere da un sottoinsieme degli oggetti con nome, peso e valore come da seguente tabella:\n\n|      |   A |   B |   C |   D |   E |   F |   G |   H |   I |   L |   M |   N |\n|:-----|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|\n| peso |  15 |  16 |  17 |  11 |  13 |   5 |   7 |   3 |   1 |  12 |   9 |   7 |\n| val  |  50 |  52 |  54 |  40 |  45 |  17 |  18 |   7 |   8 |  42 |  30 |  22 |', 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': "#Inserisci la tua risposta in forma di lista di oggetti da prendere (esempio: ['C', 'F', 'A'])\nopt_sol1=[]\n#Specificare il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi):\nopt_val1=-1", 'init_answ_cell_msg_automatic': "#Inserisci la tua risposta in forma di lista di oggetti da prendere (esempio: ['C', 'F', 'A'])\nopt_sol1=[]\n#Specificare il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi):\nopt_val1=-1", 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente CapacityMax= __36__ fornirne uno in cui sia massima la somma dei valori.', 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'pt_consistency_OK\':0,\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'pt_consistency_OK\':0,\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol1,\'opt_sol1\'),\'opt_val\':(opt_val1,\'opt_val1\'),})\''}
    task02= {'CapacityGen': 32, 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 32</b>, fornirne uno in cui sia massima la somma dei valori.', 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':32,\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':32,\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol2,\'opt_sol2\'),\'opt_val\':(opt_val2,\'opt_val2\'),})\''}
    task03= {'CapacityGen': 30, 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 30</b>, fornirne uno in cui sia massima la somma dei valori.', 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':30,\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':30,\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol3,\'opt_sol3\'),\'opt_val\':(opt_val3,\'opt_val3\'),})\''}
    task04= {'CapacityGen': 28, 'general_description_before_task': 'Nelle successive richieste alcuni degli oggetti saranno proibiti, oppure obbligati', 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 28</b>, fornirne uno in cui sia massima la somma dei valori.', 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':28,\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':28,\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol4,\'opt_sol4\'),\'opt_val\':(opt_val4,\'opt_val4\'),})\''}
    task05= {'CapacityGen': 36, 'forced_out': ['E'], 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': "Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['E'].", 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':36,\'forced_out\':[\'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':36,\'forced_out\':[\'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol5,\'opt_sol5\'),\'opt_val\':(opt_val5,\'opt_val5\'),})\''}
    task06= {'CapacityGen': 36, 'forced_out': ['B', 'E'], 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': "Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E'].", 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':36,\'forced_out\':[\'B\', \'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':36,\'forced_out\':[\'B\', \'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol6,\'opt_sol6\'),\'opt_val\':(opt_val6,\'opt_val6\'),})\''}
    task07= {'CapacityGen': 34, 'forced_out': ['B', 'E', 'F'], 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': "Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E', 'F'].", 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':34,\'forced_out\':[\'B\', \'E\', \'F\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':34,\'forced_out\':[\'B\', \'E\', \'F\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol7,\'opt_sol7\'),\'opt_val\':(opt_val7,\'opt_val7\'),})\''}
    task08= {'CapacityGen': 34, 'forced_in': ['B', 'E'], 'goals': ['opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': "Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere</b> tutti gli elementi in ['B', 'E'].", 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':34,\'forced_in\':[\'B\', \'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':34,\'forced_in\':[\'B\', \'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_val\':(opt_val8,\'opt_val8\'),})\''}
    task09= {'CapacityGen': 34, 'forced_in': ['B', 'F'], 'forced_out': ['E'], 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': "Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'F'] e <b>nessuno</b> di quelli in ['E'].", 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':34,\'forced_in\':[\'B\', \'F\'],\'forced_out\':[\'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':34,\'forced_in\':[\'B\', \'F\'],\'forced_out\':[\'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol9,\'opt_sol9\'),\'opt_val\':(opt_val9,\'opt_val9\'),})\''}
    task10={'CapacityGen': 31, 'forced_in': ['B', 'I'], 'forced_out': ['F', 'E'], 'goals': ['opt_sol'], 'init_answ_cell_msg_automatic': '', 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': "Fornire una soluzione ottima se <b>31 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'I'] e <b>nessuno</b> di quelli in ['F', 'E'].", 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_knapsack\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':31,\'forced_in\':[\'B\', \'I\'],\'forced_out\':[\'F\', \'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'CapacityGen\':31,\'forced_in\':[\'B\', \'I\'],\'forced_out\':[\'F\', \'E\'],\'init_answ_cell_msg_automatic\':\'PLACEHOLDER_prompt\',\'CapacityMax\':\'36\',\'labels\':"[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'L\', \'M\', \'N\']",\'costs\':\'[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]\',\'vals\':\'[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]\',},long_answer_dict={\'opt_sol\':(opt_sol10,\'opt_sol10\'),})\''}
    for task in context_knapsack['data'].keys():
        try:
            context_knapsack['data'][task]['question'] = context_knapsack['data'][task]['question'].replace('\" # fix temporaneo errore sintassi yaml (attesa uniformazione)','').format(**vars())
        except:
            pass
    for i in range(1,ntasks+1):
        if i<10:
            if 'CapacityGen' in locals()[f'task0{i}'].keys(): # fix temporaneo errore sintassi yaml (attesa uniformazione)
                instance_dict['Knapsack_Capacity'] = locals()[f'task0{i}']['CapacityGen']
            else:
                try:
                    instance_dict['Knapsack_Capacity'] = CapacityMax
                except:
                    pass
            if request.method == 'POST' and f'run_script_task0{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form
                a = answer(request.POST)
                print(a)
                if a.is_valid():
                    answer_dict = get_goals(a,context_knapsack['data'][f'task0{i}']) # prendo le risposte 
                    if answer_dict != {}:
                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte
                        try: # se il feedback è corretto
                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')
                        except Exception as e: # se non ho avviato TALight mando messaggio di errore
                            answ = f'<b><font color="red">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'
                    else: # dati non inseriti correttamente
                            answ = '<b><font color="red">Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.</font></b>'
                    write_to_yaml_feedback(FEEDBACKS,'knapsack',i,answ) # se tutto ok scrivo il feedback nel file
                    context_knapsack['data'][f'task0{i}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina
                    try: # se il feedback è corretto aggiorno i punteggi
                        score_knapsack[f'task0{i}'] = safe_points(answ)
                    except:
                        pass
        else:
            try:
                instance_dict['Knapsack_Capacity'] = locals()[f'task{i}']['CapacityGen'] # fix temporaneo errore sintassi yaml (attesa uniformazione)
            except:
                instance_dict['Knapsack_Capacity'] = CapacityMax
            if request.method == 'POST' and f'run_script_task{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form
                a = answer(request.POST)
                if a.is_valid():
                    answer_dict = get_goals(a,context_knapsack['data'][f'task{i}'])
                    if answer_dict != {}:
                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte
                        try: # se il feedback è corretto
                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')
                        except Exception as e: # se non ho avviato TALight mando messaggio di errore
                            answ = f'<b><font color="red">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'
                    else: # dati non inseriti correttamente
                            answ = 'Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.'
                    write_to_yaml_feedback(FEEDBACKS,'knapsack',i,answ) # se tutto ok scrivo il feedback nel file
                    context_knapsack['data'][f'task{i}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina
                    try: # se il feedback è corretto aggiorno i punteggi
                        score_knapsack[f'task{i}'] = safe_points(answ)
                    except:
                        pass
    get_scores_from_feedbacks(FEEDBACKS, POINTS_YAML)
    return render(request, 'esame/knapsack.html', context_knapsack)

def grafo_template(request): # definisco il nome della view
    return render(request,os.path.join('esame','grafo_template.html'))
context_lcs = contexts['context_lcs'] # dichiaro context_lcs

score_lcs = scores['score_lcs'] # dichiaro score_lcs

def lcs(request): # definisco il nome della view 
    rtalproblem = 'RO_lcs' # il corrispondente problema in TALight è RO_lcs
    rtalservice = 'check' # vogliamo che venga richiesto il servizio check per il problema
    rtaltoken = 'id625tbt_VR437029_OrLwSWKtpyrk1bS_RIVO_CARAPUCCI' # dummy token
    instance_dict = {'s': 'AAGCGAGATAGCCGGT', 't': 'ATAACCGATACAAGTC'} # prendo i parametri dell'istanza
    ntasks = 8 # prendo il numero di task
    conv = Ansi2HTMLConverter(dark_bg = False) # inizializzo il convertitore HTML
    s = 'AAGCGAGATAGCCGGT'
    t = 'ATAACCGATACAAGTC'
    task01= {'general_description_before_task': 'Si considerino le seguenti sequenze di caratteri:<br/><br/> $s$ = __AAGCGAGATAGCCGGT__ <br/>  $t$ = __ATAACCGATACAAGTC__', 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol1=""\\n#e la sua lunghezza:\\nopt_val1=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol1=""\\n#e la sua lunghezza:\\nopt_val1=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': 'Fornire una massima sottosequenza comune tra le due stringhe<br/>s = AAGCGAGATAGCCGGT<br/>t = ATAACCGATACAAGTC.', 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol1,'opt_sol1'),'opt_val':(opt_val1,'opt_val1'),})'"}
    task02= {'beginning': 'CC', 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol2=""\\n#e la sua lunghezza:\\nopt_val2=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol2=""\\n#e la sua lunghezza:\\nopt_val2=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': 'Fornire una stringa di lunghezza massima che inizi col prefisso __CC__ e sia sottosequenza comune tra<br/>s = AAGCGAGATAGCCGGT<br/>t = ATAACCGATACAAGTC.', 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'beginning':'CC','s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'beginning':'CC','s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol2,'opt_sol2'),'opt_val':(opt_val2,'opt_val2'),})'"}
    task03= {'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol3=""\\n#e la sua lunghezza:\\nopt_val3=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol3=""\\n#e la sua lunghezza:\\nopt_val3=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'reduce_s_to_its_suffix_of_length': 15, 'request': "Fornire una massima sottosequenza comune tra<br/><b>il suffisso </b> $s\\'$ = AGCGAGATAGCCGGT di s e <br/>t = ATAACCGATACAAGTC.", 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_s_to_its_suffix_of_length':15,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_s_to_its_suffix_of_length':15,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol3,'opt_sol3'),'opt_val':(opt_val3,'opt_val3'),})'"}
    task04= {'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol4=""\\n#e la sua lunghezza:\\nopt_val4=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol4=""\\n#e la sua lunghezza:\\nopt_val4=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'reduce_s_to_its_suffix_of_length': 11, 'request': "Fornire una massima sottosequenza comune tra<br/><b>il suffisso </b> $s\\'$ = AGATAGCCGGT di s e <br/>t = ATAACCGATACAAGTC.", 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_s_to_its_suffix_of_length':11,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_s_to_its_suffix_of_length':11,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol4,'opt_sol4'),'opt_val':(opt_val4,'opt_val4'),})'"}
    task05= {'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol5=""\\n#e la sua lunghezza:\\nopt_val5=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol5=""\\n#e la sua lunghezza:\\nopt_val5=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'reduce_s_to_its_suffix_of_length': 9, 'request': "Fornire una massima sottosequenza comune tra<br/><b>il suffisso </b> $s\\'$ = ATAGCCGGT di s e <br/>t = ATAACCGATACAAGTC.", 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_s_to_its_suffix_of_length':9,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_s_to_its_suffix_of_length':9,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol5,'opt_sol5'),'opt_val':(opt_val5,'opt_val5'),})'"}
    task06= {'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol6=""\\n#e la sua lunghezza:\\nopt_val6=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol6=""\\n#e la sua lunghezza:\\nopt_val6=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'reduce_t_to_its_suffix_of_length': 13, 'request': "Fornire una massima sottosequenza comune tra<br/><b>il suffisso</b>  $t\\'$ = ACCGATACAAGTC di t e <br/>s = AAGCGAGATAGCCGGT.", 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_t_to_its_suffix_of_length':13,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_t_to_its_suffix_of_length':13,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol6,'opt_sol6'),'opt_val':(opt_val6,'opt_val6'),})'"}
    task07= {'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol7=""\\n#e la sua lunghezza:\\nopt_val7=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol7=""\\n#e la sua lunghezza:\\nopt_val7=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'reduce_t_to_its_suffix_of_length': 11, 'request': "Fornire una massima sottosequenza comune tra<br/><b>il suffisso</b>  $t\\'$ = CGATACAAGTC di t e <br/>s = AAGCGAGATAGCCGGT.", 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_t_to_its_suffix_of_length':11,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_t_to_its_suffix_of_length':11,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol7,'opt_sol7'),'opt_val':(opt_val7,'opt_val7'),})'"}
    task08= {'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol8=""\\n#e la sua lunghezza:\\nopt_val8=7', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol8=""\\n#e la sua lunghezza:\\nopt_val8=7', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'reduce_t_to_its_suffix_of_length': 9, 'request': "Fornire una massima sottosequenza comune tra<br/><b>il suffisso</b>  $t\\'$ = ATACAAGTC di t e <br/>s = AAGCGAGATAGCCGGT.", 'tot_points': 45, 'verif': "'verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_t_to_its_suffix_of_length':9,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},input_data_assigned={'tot_points':45,'pt_formato_OK':0,'pt_feasibility_OK':1,'pt_consistency_OK':0,'reduce_t_to_its_suffix_of_length':9,'s':'AAGCGAGATAGCCGGT','t':'ATAACCGATACAAGTC',},long_answer_dict={'opt_sol':(opt_sol8,'opt_sol8'),'opt_val':(opt_val8,'opt_val8'),})'"}
    for task in context_lcs['data'].keys():
        try:
            context_lcs['data'][task]['question'] = context_lcs['data'][task]['question'].replace('\" # fix temporaneo errore sintassi yaml (attesa uniformazione)','').format(**vars())
        except:
            pass
    for i in range(1,ntasks+1):
        if i<10:
            if 'CapacityGen' in locals()[f'task0{i}'].keys(): # fix temporaneo errore sintassi yaml (attesa uniformazione)
                instance_dict['Knapsack_Capacity'] = locals()[f'task0{i}']['CapacityGen']
            else:
                try:
                    instance_dict['Knapsack_Capacity'] = CapacityMax
                except:
                    pass
            if request.method == 'POST' and f'run_script_task0{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form
                a = answer(request.POST)
                print(a)
                if a.is_valid():
                    answer_dict = get_goals(a,context_lcs['data'][f'task0{i}']) # prendo le risposte 
                    if answer_dict != {}:
                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte
                        try: # se il feedback è corretto
                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')
                        except Exception as e: # se non ho avviato TALight mando messaggio di errore
                            answ = f'<b><font color="red">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'
                    else: # dati non inseriti correttamente
                            answ = '<b><font color="red">Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.</font></b>'
                    write_to_yaml_feedback(FEEDBACKS,'lcs',i,answ) # se tutto ok scrivo il feedback nel file
                    context_lcs['data'][f'task0{i}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina
                    try: # se il feedback è corretto aggiorno i punteggi
                        score_lcs[f'task0{i}'] = safe_points(answ)
                    except:
                        pass
        else:
            try:
                instance_dict['Knapsack_Capacity'] = locals()[f'task{i}']['CapacityGen'] # fix temporaneo errore sintassi yaml (attesa uniformazione)
            except:
                instance_dict['Knapsack_Capacity'] = CapacityMax
            if request.method == 'POST' and f'run_script_task{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form
                a = answer(request.POST)
                if a.is_valid():
                    answer_dict = get_goals(a,context_lcs['data'][f'task{i}'])
                    if answer_dict != {}:
                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte
                        try: # se il feedback è corretto
                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')
                        except Exception as e: # se non ho avviato TALight mando messaggio di errore
                            answ = f'<b><font color="red">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'
                    else: # dati non inseriti correttamente
                            answ = 'Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.'
                    write_to_yaml_feedback(FEEDBACKS,'lcs',i,answ) # se tutto ok scrivo il feedback nel file
                    context_lcs['data'][f'task{i}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina
                    try: # se il feedback è corretto aggiorno i punteggi
                        score_lcs[f'task{i}'] = safe_points(answ)
                    except:
                        pass
    get_scores_from_feedbacks(FEEDBACKS, POINTS_YAML)
    return render(request, 'esame/lcs.html', context_lcs)

def grafo_template(request): # definisco il nome della view
    return render(request,os.path.join('esame','grafo_template.html'))
context_mst = contexts['context_mst'] # dichiaro context_mst

score_mst = scores['score_mst'] # dichiaro score_mst

def mst(request): # definisco il nome della view 
    rtalproblem = 'RO_mst' # il corrispondente problema in TALight è RO_mst
    rtalservice = 'check' # vogliamo che venga richiesto il servizio check per il problema
    rtaltoken = 'id625tbt_VR437029_OrLwSWKtpyrk1bS_RIVO_CARAPUCCI' # dummy token
    instance_dict = {'edges': '[(A,B)(B,T)(T,A)(T,D)(A,F)(B,E)(E,F)]', 'm': 7, 'n': 6} # prendo i parametri dell'istanza
    ntasks = 7 # prendo il numero di task
    conv = Ansi2HTMLConverter(dark_bg = False) # inizializzo il convertitore HTML
    edges = '[(A,B)(B,T)(T,A)(T,D)(A,F)(B,E)(E,F)]'
    m = 7
    n = 6
    task01= {'general_description_before_task': 'Ogni richiesta del presente esercizio farà riferimento al grafo $G$ offerto nel seguente riquadro. Il grafo $G$ ha __5__ nodi, labellati coi primi __5__ numeri naturali e __8__ archi pesati, labellati coi primi __8__ numeri naturali. La lista ordinata degli archi è __[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]__. Ecco una rappresentazione di $G$ (da quì puoi scaricarti $G$ in vari formati):\n\nedge_weighted_graph_2picture(n=5,m=8,edges=[[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]])', 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta in forma di lista di archi da prendere (esempio: [0, 3, 4, 6])\nopt_sol1=[]\n#Specificare il peso della soluzione introdotta (un intero, la somma dei pesi degli archi presi):\nopt_val1=-1', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta in forma di lista di archi da prendere (esempio: [0, 3, 4, 6])\nopt_sol1=[]\n#Specificare il peso della soluzione introdotta (un intero, la somma dei pesi degli archi presi):\nopt_val1=-1', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': 'Fornire un albero ricoprente di peso minimo e specificarne il peso complessivo.', 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'tot_points': 70, 'verif': '\'verify_submission(TALight_problem_name=\'RO_mst\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':70,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'pt_consistency_OK\':0,\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},input_data_assigned={\'tot_points\':70,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'pt_consistency_OK\':0,\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},long_answer_dict={\'opt_sol\':(opt_sol1,\'opt_sol1\'),\'opt_val\':(opt_val1,\'opt_val1\'),})\''}
    task02= {'goals': ['num_opt_sols'], 'init_answ_cell_msg': '#Inserisci la tua risposta (un intero, il numero di soluzioni ottime diverse):\nopt_val2=-1', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta (un intero, il numero di soluzioni ottime diverse):\nopt_val2=-1', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 0, 'pt_formato_OK': 0, 'request': 'Specificare quanti siano gli alberi ricoprenti di peso minimo.', 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'tot_points': 60, 'verif': '\'verify_submission(TALight_problem_name=\'RO_mst\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':60,\'pt_formato_OK\':0,\'pt_feasibility_OK\':0,\'pt_consistency_OK\':0,\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},input_data_assigned={\'tot_points\':60,\'pt_formato_OK\':0,\'pt_feasibility_OK\':0,\'pt_consistency_OK\':0,\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},long_answer_dict={\'num_opt_sols\':(num_opt_sols2,\'num_opt_sols2\'),})\''}
    task03= {'goals': 'not a TALight verify service goal', 'init_answ_cell_msg': '#Inserisci la tua risposta in questa cella di testo libero.', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta in questa cella di testo libero.', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 0, 'pt_formato_OK': 0, 'request': 'Specificare quanti siano gli alberi ricoprenti di peso minimo.', 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'tot_points': 90}
    task04= {'cut_cert_type': 'free', 'goals': ['edge_classification'], 'init_answ_cell_msg': "#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate4=''\n#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate4=''\n#Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert4=[0,3,7,2]\nedgecut_cert4=[0,3,7,2]\ncutshore_cert4=[0,3,7,2]", 'init_answ_cell_msg_automatic': "#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate4=''\n#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate4=''\n#Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert4=[0,3,7,2]\nedgecut_cert4=[0,3,7,2]\ncutshore_cert4=[0,3,7,2]", 'pt_consistency_OK': 0, 'pt_feasibility_OK': 59, 'pt_formato_OK': 1, 'query_edge': 0, 'request': "Dire, certificandolo, se l'arco ${query_edge}$ appartenga a tutti, oppure a nessuno, oppure a qualcuno ma non tutti gli alberi ricoprenti di peso minimo.", 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'tot_points': 60, 'verif': '\'verify_submission(TALight_problem_name=\'RO_mst\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':60,\'pt_formato_OK\':1,\'pt_feasibility_OK\':59,\'pt_consistency_OK\':0,\'query_edge\':0,\'cut_cert_type\':\'free\',\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},input_data_assigned={\'tot_points\':60,\'pt_formato_OK\':1,\'pt_feasibility_OK\':59,\'pt_consistency_OK\':0,\'query_edge\':0,\'cut_cert_type\':\'free\',\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},long_answer_dict={\'edge_classification\':(edge_classification4,\'edge_classification4\'),})\''}
    task05= {'cut_cert_type': 'free', 'goals': ['edge_classification'], 'init_answ_cell_msg': "#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate5=''\n#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate5=''\n#Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert5=[0,3,7,2]\nedgecut_cert5=[0,3,7,2]\ncutshore_cert5=[0,3,7,2]", 'init_answ_cell_msg_automatic': "#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate5=''\n#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate5=''\n#Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert5=[0,3,7,2]\nedgecut_cert5=[0,3,7,2]\ncutshore_cert5=[0,3,7,2]", 'pt_consistency_OK': 0, 'pt_feasibility_OK': 59, 'pt_formato_OK': 1, 'query_edge': 4, 'request': "Dire, certificandolo, se l'arco ${query_edge}$ appartenga a tutti, oppure a nessuno, oppure a qualcuno ma non tutti gli alberi ricoprenti di peso minimo.", 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'tot_points': 60, 'verif': '\'verify_submission(TALight_problem_name=\'RO_mst\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':60,\'pt_formato_OK\':1,\'pt_feasibility_OK\':59,\'pt_consistency_OK\':0,\'query_edge\':4,\'cut_cert_type\':\'free\',\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},input_data_assigned={\'tot_points\':60,\'pt_formato_OK\':1,\'pt_feasibility_OK\':59,\'pt_consistency_OK\':0,\'query_edge\':4,\'cut_cert_type\':\'free\',\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},long_answer_dict={\'edge_classification\':(edge_classification5,\'edge_classification5\'),})\''}
    task06= {'cut_cert_type': 'free', 'goals': ['edge_classification'], 'init_answ_cell_msg': "#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate6=''\n#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate6=''\n#Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert6=[0,3,7,2]\nedgecut_cert6=[0,3,7,2]\ncutshore_cert6=[0,3,7,2]", 'init_answ_cell_msg_automatic': "#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate6=''\n#Inserisci la tua risposta (una stringa tra 'in_all', 'in_no', 'in_some_but_not_in_all'):\ncertificate6=''\n#Specificare i certificati necessari a convalidare la tua catalogazione. Se serve un certificato di taglio, puoi limitarti a fornirlo solo come lista degli archi costituenti il taglio (esempio: [0,3,7,2]), oppure solo come lista dei nodi di una delle due shore del taglio (se offri entrambe le descrizioni del taglio certificante verrà verificata la consistenza tra di esse). Se serve un certificato di ciclo, la lista degli archi costituenti il ciclo deve essere ordinata come da una percorrenza del ciclo:\ncyc_cert6=[0,3,7,2]\nedgecut_cert6=[0,3,7,2]\ncutshore_cert6=[0,3,7,2]", 'pt_consistency_OK': 0, 'pt_feasibility_OK': 59, 'pt_formato_OK': 1, 'query_edge': 5, 'request': "Dire, certificandolo, se l'arco ${query_edge}$ appartenga a tutti, oppure a nessuno, oppure a qualcuno ma non tutti gli alberi ricoprenti di peso minimo.", 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'tot_points': 60, 'verif': '\'verify_submission(TALight_problem_name=\'RO_mst\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':60,\'pt_formato_OK\':1,\'pt_feasibility_OK\':59,\'pt_consistency_OK\':0,\'query_edge\':5,\'cut_cert_type\':\'free\',\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},input_data_assigned={\'tot_points\':60,\'pt_formato_OK\':1,\'pt_feasibility_OK\':59,\'pt_consistency_OK\':0,\'query_edge\':5,\'cut_cert_type\':\'free\',\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},long_answer_dict={\'edge_classification\':(edge_classification6,\'edge_classification6\'),})\''}
    task07= {'forced_in': 4, 'goals': ['opt_sol', 'opt_val'], 'init_answ_cell_msg': '#Inserisci la tua risposta in forma di lista di archi da prendere (esempio: [0, 3, 4, 6])\nopt_sol7=[]\n#Specificare il peso della soluzione introdotta (un intero, la somma dei pesi degli archi presi):\nopt_val7=-1', 'init_answ_cell_msg_automatic': '#Inserisci la tua risposta in forma di lista di archi da prendere (esempio: [0, 3, 4, 6])\nopt_sol7=[]\n#Specificare il peso della soluzione introdotta (un intero, la somma dei pesi degli archi presi):\nopt_val7=-1', 'pt_consistency_OK': 0, 'pt_feasibility_OK': 1, 'pt_formato_OK': 0, 'request': "Fornire un albero ricoprente di peso minimo tra quelli forzati a contenere l'arco __${forced_in}$__. Specificare il peso complessivo della tua soluzione.", 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'tot_points': 40, 'verif': '\'verify_submission(TALight_problem_name=\'RO_mst\',checkers=[\'TALight\', \'embedded_in_notebook\'],task_dict={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'pt_consistency_OK\':0,\'forced_in\':4,\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},input_data_assigned={\'tot_points\':40,\'pt_formato_OK\':0,\'pt_feasibility_OK\':1,\'pt_consistency_OK\':0,\'forced_in\':4,\'task_state_modifier\':[\'edgecol\', \'nodetag\', \'edgetag\', \'orientation\', \'refresh\'],\'select\':[\'NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi\', \'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.\', \'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )\', \'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.\', \'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.\', \'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).\'],\'init_answ_cell_msg_automatic\':\'#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")\',\'n\':\'5\',\'m\':\'8\',\'edges\':\'[({0,1},2),({1,2},2),({2,3},2),({1,3},2),({3,4},5),({1,4},3),({0,4},3)]\',},long_answer_dict={\'opt_sol\':(opt_sol7,\'opt_sol7\'),\'opt_val\':(opt_val7,\'opt_val7\'),})\''}
    for task in context_mst['data'].keys():
        try:
            context_mst['data'][task]['question'] = context_mst['data'][task]['question'].replace('\" # fix temporaneo errore sintassi yaml (attesa uniformazione)','').format(**vars())
        except:
            pass
    for i in range(1,ntasks+1):
        if i<10:
            if 'CapacityGen' in locals()[f'task0{i}'].keys(): # fix temporaneo errore sintassi yaml (attesa uniformazione)
                instance_dict['Knapsack_Capacity'] = locals()[f'task0{i}']['CapacityGen']
            else:
                try:
                    instance_dict['Knapsack_Capacity'] = CapacityMax
                except:
                    pass
            if request.method == 'POST' and f'run_script_task0{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form
                a = answer(request.POST)
                print(a)
                if a.is_valid():
                    answer_dict = get_goals(a,context_mst['data'][f'task0{i}']) # prendo le risposte 
                    if answer_dict != {}:
                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte
                        try: # se il feedback è corretto
                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')
                        except Exception as e: # se non ho avviato TALight mando messaggio di errore
                            answ = f'<b><font color="red">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'
                    else: # dati non inseriti correttamente
                            answ = '<b><font color="red">Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.</font></b>'
                    write_to_yaml_feedback(FEEDBACKS,'mst',i,answ) # se tutto ok scrivo il feedback nel file
                    context_mst['data'][f'task0{i}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina
                    try: # se il feedback è corretto aggiorno i punteggi
                        score_mst[f'task0{i}'] = safe_points(answ)
                    except:
                        pass
        else:
            try:
                instance_dict['Knapsack_Capacity'] = locals()[f'task{i}']['CapacityGen'] # fix temporaneo errore sintassi yaml (attesa uniformazione)
            except:
                instance_dict['Knapsack_Capacity'] = CapacityMax
            if request.method == 'POST' and f'run_script_task{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form
                a = answer(request.POST)
                if a.is_valid():
                    answer_dict = get_goals(a,context_mst['data'][f'task{i}'])
                    if answer_dict != {}:
                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte
                        try: # se il feedback è corretto
                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')
                        except Exception as e: # se non ho avviato TALight mando messaggio di errore
                            answ = f'<b><font color="red">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'
                    else: # dati non inseriti correttamente
                            answ = 'Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.'
                    write_to_yaml_feedback(FEEDBACKS,'mst',i,answ) # se tutto ok scrivo il feedback nel file
                    context_mst['data'][f'task{i}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina
                    try: # se il feedback è corretto aggiorno i punteggi
                        score_mst[f'task{i}'] = safe_points(answ)
                    except:
                        pass
    get_scores_from_feedbacks(FEEDBACKS, POINTS_YAML)
    return render(request, 'esame/mst.html', context_mst)

def grafo_template(request): # definisco il nome della view
    return render(request,os.path.join('esame','grafo_template.html'))
