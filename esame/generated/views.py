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
FEEDBACKS = os.path.join(home,'/home/romeo/corsi/RO/esami/esercizi-nel-browser/simulazione_esame/browser_feedback_log/feedbacks.yaml') # yaml contenente i feedback suddivisi per esercizio e per task
FEEDBACK_SAVED_LOG = os.path.join(home,'/home/romeo/corsi/RO/esami/esercizi-nel-browser/simulazione_esame/browser_feedback_log/feedback_saved_log.yaml')  # yaml contenente i feedback salvati suddivisi per esercizio e per task
POINTS_YAML = '/home/romeo/corsi/RO/esami/esercizi-nel-browser/simulazione_esame/browser_feedback_log/points.yaml'  # yaml contenente i punti suddivisi per esercizio e per task
SAVED_SCORES = '/home/romeo/corsi/RO/esami/esercizi-nel-browser/simulazione_esame/browser_feedback_log/saved_scores.yaml'  # yaml contenente i punti relativi agli esercizi salvati suddivisi per esercizio e per task
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

contexts = {'context_mst': {'data'  :{'task01': {'question': '<label>Ritornare una soluzione che rispetti l\'opzione selezionata<br>Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")</label>', 'feedback': '', 'goals': ['certificato1'], 'descr_before_task': '<label>Si consideri il grafo non diretto G, con pesi sugli archi.</label>', 'componenti_stato': [{'ciclo': 'edgeset'}, {'taglio': 'edgeset'}, {'shore': 'nodeset'}], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).']},'task02': {'question': '<label>Restituire un grafo in cui si certifica se l\'arco è in tutte, nessuna o alcune ma non tutte le soluzioni ottime.<br>Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")</label>', 'feedback': '', 'goals': ['certificato2'], 'descr_before_task': "<label>Si consideri il grafo non-diretto G, con pesi sugli archi e l'arco (A,B).</label>", 'componenti_stato': [{'col3': 'edgecol'}], 'task_state_modifier': ['edgecol', 'refresh'], 'select': ['3-COLORAZIONE DEGLI ARCHI [col3]- il mio certificato è una 3-colorazione degli archi']},'task03': {'question': '<label>Restituire un grafo in cui si certifica se l\'arco è in tutte, nessuna o alcune ma non tutte le soluzioni ottime.<br>Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")</label>', 'feedback': '', 'goals': ['certificato3'], 'descr_before_task': "<label>Si consideri il grafo non-diretto G, con pesi sugli archi e l'arco (A,B).</label>", 'componenti_stato': [{'mia_orientazione': 'orientation'}, {'U': 'nodeset'}, {'F': 'edgeset'}], 'task_state_modifier': ['edgecol', 'orientation', 'refresh'], 'select': ['Yes, ORIENTAZIONE ACICLICA [mia_orientazione] - il mio certificato è una orientazione aciclica', 'No, FORBIDDEN SUBGRAPH NODE SET U [U] - il mio certificato è un sottografo sui nodi U', 'No, FORBIDDEN SUBGRAPH EDGE SET F [F] - il mio certificato è un sottografo di archi F']},}},'context_lcs': {'data'  :{'task01': {'question': '<label>Fornire una massima sottosequenza comune tra le due stringhe:<br/>s = GCTCTACGCTGGATTC<br/>t = ATGCCGCTTACCGTGATC.<br>Inserisci in `opt_sol1` una sottosequnza ottima\\nopt_sol1=SONOUNASTRINGA\\n<br>Immetti in `opt_val1` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val1=14</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label>Si considerino le seguenti sequenze di caratteri:<br/><br/></label>'},'task02': {'question': '<label>Fornire una stringa di lunghezza massima che inizi col prefisso CC e sia sottosequenza comune tra: <br/>s = GCTCTACGCTGGATTC<br/>t = ATGCCGCTTACCGTGATC.<br>Inserisci in `opt_sol2` una sottosequnza ottima\\nopt_sol2=SONOUNASTRINGA\\n<br>Immetti in `opt_val2` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val2=14</label>', 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task03': {'question': "<label>Fornire una massima sottosequenza comune tra:<br/><b>il suffisso </b> $s'$ = CTCTACGCTGGATTC di s e <br/>t = ATGCCGCTTACCGTGATC.<br>Inserisci in `opt_sol3` una sottosequnza ottima\\nopt_sol3=SONOUNASTRINGA\\n<br>Immetti in `opt_val3` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val3=14</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task04': {'question': "<label>Fornire una massima sottosequenza comune tra:<br/><b>il suffisso </b> $s'$ = ACGCTGGATTC di s e <br/>t = ATGCCGCTTACCGTGATC.<br>Inserisci in `opt_sol4` una sottosequnza ottima\\nopt_sol4=SONOUNASTRINGA\\n<br>Immetti in `opt_val4` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val4=14</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task05': {'question': "<label>Fornire una massima sottosequenza comune tra:<br/><b>il suffisso </b> $s'$ = GCTGGATTC di s e <br/>t = ATGCCGCTTACCGTGATC.<br>Inserisci in `opt_sol5` una sottosequnza ottima\\nopt_sol5=SONOUNASTRINGA\\n<br>Immetti in `opt_val5` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val5=14</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task06': {'question': "<label>Fornire una massima sottosequenza comune tra: <br/><b>il suffisso</b>  $t'$ = GCTTACCGTGATC di t e <br/>s = GCTCTACGCTGGATTC.<br>Inserisci in `opt_sol6` una sottosequnza ottima\\nopt_sol6=SONOUNASTRINGA\\n<br>Immetti in `opt_val6` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val6=14</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task07': {'question': "<label>Fornire una massima sottosequenza comune tra: <br/><b>il suffisso</b>  $t'$ = TTACCGTGATC di t e <br/>s = GCTCTACGCTGGATTC.<br>Inserisci in `opt_sol7` una sottosequnza ottima\\nopt_sol7=SONOUNASTRINGA\\n<br>Immetti in `opt_val7` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val7=14</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task08': {'question': "<label>Fornire una massima sottosequenza comune tra: <br/><b>il suffisso</b>  $t'$ = ACCGTGATC di t e <br/>s = GCTCTACGCTGGATTC.<br>Inserisci in `opt_sol8` una sottosequnza ottima\\nopt_sol8=SONOUNASTRINGA\\n<br>Immetti in `opt_val8` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val8=14</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},}},'context_knapsack': {'data'  :{'task01': {'question': "<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente CapacityMax= 36 fornirne uno in cui sia massima la somma dei valori.<br>Inserisci in `opt_sol1` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'H', 'G', 'E', 'A'])\\nopt_sol1=[]\\n<br>Immetti in `opt_val1` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val1=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label>In ogni richiesta del presente esercizio lo zaino disponibile avrà capienza al più CapacityMax = 36  e dovrai scegliere quali prendere da un sottoinsieme degli oggetti con nome, peso e valore come nella tabella sopra riportata</label>'},'task02': {'question': "<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 32</b>, fornirne uno in cui sia massima la somma dei valori.<br>Inserisci in `opt_sol2` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'H', 'G', 'D', 'F'])\\nopt_sol2=[]\\n<br>Immetti in `opt_val2` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val2=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task03': {'question': "<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 30</b>, fornirne uno in cui sia massima la somma dei valori.<br>Inserisci in `opt_sol3` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'H', 'E', 'A'])\\nopt_sol3=[]\\n<br>Immetti in `opt_val3` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val3=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task04': {'question': "<label>Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 28</b>, fornirne uno in cui sia massima la somma dei valori.<br>Inserisci in `opt_sol4` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'D', 'H'])\\nopt_sol4=[]\\n<br>Immetti in `opt_val4` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val4=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label>Nelle successive richieste alcuni degli oggetti saranno proibiti, oppure obbligati</label>'},'task05': {'question': "<label>Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['E'].<br>Inserisci in `opt_sol5` la lista degli oggetti da prendere (esempio: ['E', 'N', 'M', 'L', 'F', 'G'])\\nopt_sol5=[]\\n<br>Immetti in `opt_val5` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val5=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task06': {'question': "<label>Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E'].<br>Inserisci in `opt_sol6` la lista degli oggetti da prendere (esempio: ['B', 'N', 'M', 'L', 'A', 'F'])\\nopt_sol6=[]\\n<br>Immetti in `opt_val6` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val6=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task07': {'question': "<label>Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E', 'F'].<br>Inserisci in `opt_sol7` la lista degli oggetti da prendere (esempio: ['E', 'N', 'M', 'L', 'G', 'A'])\\nopt_sol7=[]\\n<br>Immetti in `opt_val7` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val7=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task08': {'question': "<label>Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere</b> tutti gli elementi in ['B', 'E'].<br>Inserisci in `opt_val8` il massimo valore possibile per una soluzione ammissibile (un intero, la somma dei valori degli oggetti presi)\\nopt_val8=-1</label>", 'feedback': '', 'goals': ['opt_val'], 'descr_before_task': '<label></label>'},'task09': {'question': "<label>Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'F'] e <b>nessuno</b> di quelli in ['E'].<br>Inserisci in `opt_sol9` la lista degli oggetti da prendere (esempio: ['B', 'E', 'N', 'D', 'H'])\\nopt_sol9=[]\\n<br>Immetti in `opt_val9` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val9=-1</label>", 'feedback': '', 'goals': ['opt_sol', 'opt_val'], 'descr_before_task': '<label></label>'},'task10': {'question': "<label>Fornire una soluzione ottima se <b>31 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'I'] e <b>nessuno</b> di quelli in ['F', 'E'].<br>Inserisci la tua risposta in forma di lista di oggetti da prendere (esempio: ['I', 'E', 'N', 'M', 'L', 'F', 'D'])\\nopt_sol10=[]</label>", 'feedback': '', 'goals': ['opt_sol'], 'descr_before_task': '<label></label>'},}},}

scores = {'score_mst': {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0},'score_lcs': {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0},'score_knapsack': {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0},}

labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N']
costs = [15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]
vals = [50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]
s = 'GCTCTACGCTGGATTC'
t = 'ATGCCGCTTACCGTGATC'
n = 24
m = 40
edges = '[(S,G)(S,A)(S,E)(G,B)(G,F)(E,F)(E,C)(F,D)(D,C)(D,B)(A,C)(A,B)(G,O)(B,Q)(O,Q)(O,M)(Q,I)(M,I)(M,H)(I,L)(L,H)(N,L)(P,H)(N,P)(N,W)(P,X)(W,T)(W,V)(W,X)(X,R)(X,Y)(V,Z)(V,R)(Z,T)(Z,U)(R,U)(U,Y)(Y,T)(O,P)(Q,N)]'

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

ex_tot_points = {'knapsack': 400,'lcs': 360,'mst': 210,}

exam_context = {'data'  :{'knapsack': {'title': 'knapsack', 'score': {'punti_sicuri':'<font color="green">0/400</font>', 'punti_aggiuntivi_possibili':'<font color="blue">0/400</font>','punti_fuori_portata':'<font color="red">0/400</font>'}},'lcs': {'title': 'lcs', 'score': {'punti_sicuri':'<font color="green">0/360</font>', 'punti_aggiuntivi_possibili':'<font color="blue">0/360</font>','punti_fuori_portata':'<font color="red">0/360</font>'}},'mst': {'title': 'mst', 'score': {'punti_sicuri':'<font color="green">0/210</font>', 'punti_aggiuntivi_possibili':'<font color="blue">0/210</font>','punti_fuori_portata':'<font color="red">0/210</font>'}},} }


def esame(request):
    return render(request, os.path.join('esame','esame.html'), exam_context)

context_knapsack = contexts['context_knapsack'] # dichiaro context_knapsack

score_knapsack = scores['score_knapsack'] # dichiaro score_knapsack

def knapsack(request): # definisco il nome della view 
    rtalproblem = 'RO_knapsack' # il corrispondente problema in TALight è RO_knapsack
    rtalservice = 'check' # vogliamo che venga richiesto il servizio check per il problema
    rtaltoken = 'id625tbt_VR437029_OrLwSWKtpyrk1bS_RIVO_CARAPUCCI' # dummy token
    instance_dict = {'labels': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'], 'costs': [15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7], 'vals': [50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]} # prendo i parametri dell'istanza
    ntasks = 10 # prendo il numero di task
    conv = Ansi2HTMLConverter(dark_bg = False) # inizializzo il convertitore HTML
    CapacityMax = 36
    labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N']
    costs = [15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7]
    vals = [50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22]
    task01= {'general_description_before_task': 'In ogni richiesta del presente esercizio lo zaino disponibile avrà capienza al più $CapacityMax$ = __36__  e dovrai scegliere quali prendere da un sottoinsieme degli oggetti con nome, peso e valore come nella tabella sopra riportata', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'goals': ['opt_sol', 'opt_val'], 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente CapacityMax= __36__ fornirne uno in cui sia massima la somma dei valori.', 'init_answ_cell_msg': "#Inserisci la tua risposta in forma di lista di oggetti da prendere (esempio: ['C', 'F', 'A'])\nopt_sol1=[]\n#Specificare il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi):\nopt_val1=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 1, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':36,'forced_out':[],'forced_in':[],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol1,'opt_sol1'),'opt_val':(opt_val1,'opt_val1'),})", 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol1` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'H', 'G', 'E', 'A'])\\nopt_sol1=[]\\n#Immetti in `opt_val1` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val1=-1"}
    task02= {'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol', 'opt_val'], 'CapacityGen': 32, 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 32</b>, fornirne uno in cui sia massima la somma dei valori.', 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol2` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'H', 'G', 'D', 'F'])\\nopt_sol2=[]\\n#Immetti in `opt_val2` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val2=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 2, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':32,'forced_out':[],'forced_in':[],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol2,'opt_sol2'),'opt_val':(opt_val2,'opt_val2'),})"}
    task03= {'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol', 'opt_val'], 'CapacityGen': 30, 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 30</b>, fornirne uno in cui sia massima la somma dei valori.', 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol3` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'H', 'E', 'A'])\\nopt_sol3=[]\\n#Immetti in `opt_val3` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val3=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 3, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':30,'forced_out':[],'forced_in':[],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol3,'opt_sol3'),'opt_val':(opt_val3,'opt_val3'),})"}
    task04= {'general_description_before_task': 'Nelle successive richieste alcuni degli oggetti saranno proibiti, oppure obbligati', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol', 'opt_val'], 'CapacityGen': 28, 'request': 'Tra i sottoinsiemi di oggetti di peso complessivo non eccedente <b>la capacità 28</b>, fornirne uno in cui sia massima la somma dei valori.', 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol4` la lista degli oggetti da prendere (esempio: ['N', 'M', 'L', 'I', 'D', 'H'])\\nopt_sol4=[]\\n#Immetti in `opt_val4` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val4=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 4, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':28,'forced_out':[],'forced_in':[],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol4,'opt_sol4'),'opt_val':(opt_val4,'opt_val4'),})"}
    task05= {'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol', 'opt_val'], 'CapacityGen': 36, 'forced_out': ['E'], 'request': "Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['E'].", 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol5` la lista degli oggetti da prendere (esempio: ['E', 'N', 'M', 'L', 'F', 'G'])\\nopt_sol5=[]\\n#Immetti in `opt_val5` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val5=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 5, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':36,'forced_out':['E'],'forced_in':[],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol5,'opt_sol5'),'opt_val':(opt_val5,'opt_val5'),})"}
    task06= {'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol', 'opt_val'], 'CapacityGen': 36, 'forced_out': ['B', 'E'], 'request': "Fornire una soluzione ottima se <b>36 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E'].", 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol6` la lista degli oggetti da prendere (esempio: ['B', 'N', 'M', 'L', 'A', 'F'])\\nopt_sol6=[]\\n#Immetti in `opt_val6` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val6=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 6, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':36,'forced_out':['B', 'E'],'forced_in':[],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol6,'opt_sol6'),'opt_val':(opt_val6,'opt_val6'),})"}
    task07= {'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol', 'opt_val'], 'CapacityGen': 34, 'forced_out': ['B', 'E', 'F'], 'request': "Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>non poter prendere</b> nessuno degli elementi in ['B', 'E', 'F'].", 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol7` la lista degli oggetti da prendere (esempio: ['E', 'N', 'M', 'L', 'G', 'A'])\\nopt_sol7=[]\\n#Immetti in `opt_val7` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val7=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 7, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':34,'forced_out':['B', 'E', 'F'],'forced_in':[],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol7,'opt_sol7'),'opt_val':(opt_val7,'opt_val7'),})"}
    task08= {'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_val'], 'CapacityGen': 34, 'forced_in': ['B', 'E'], 'request': "Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere</b> tutti gli elementi in ['B', 'E'].", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_val8` il massimo valore possibile per una soluzione ammissibile (un intero, la somma dei valori degli oggetti presi)\\nopt_val8=-1', 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 8, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':34,'forced_out':[],'forced_in':['B', 'E'],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_val':(opt_val8,'opt_val8'),})"}
    task09= {'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol', 'opt_val'], 'CapacityGen': 34, 'forced_in': ['B', 'F'], 'forced_out': ['E'], 'request': "Fornire una soluzione ottima se <b>34 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'F'] e <b>nessuno</b> di quelli in ['E'].", 'init_answ_cell_msg_automatic': "#Inserisci in `opt_sol9` la lista degli oggetti da prendere (esempio: ['B', 'E', 'N', 'D', 'H'])\\nopt_sol9=[]\\n#Immetti in `opt_val9` il valore della soluzione introdotta (un intero, la somma dei valori degli oggetti presi)\\nopt_val9=-1", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 9, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':34,'forced_out':['E'],'forced_in':['B', 'F'],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol9,'opt_sol9'),'opt_val':(opt_val9,'opt_val9'),})"}
    task10={'general_description_before_task': '', 'tot_points': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'goals': ['opt_sol'], 'CapacityGen': 31, 'forced_in': ['B', 'I'], 'forced_out': ['F', 'E'], 'request': "Fornire una soluzione ottima se <b>31 è la capienza dello zaino</b> da non superarsi ma assumendo di <b>dover prendere tutti</b> gli elementi in ['B', 'I'] e <b>nessuno</b> di quelli in ['F', 'E'].", 'init_answ_cell_msg_automatic': "#Inserisci la tua risposta in forma di lista di oggetti da prendere (esempio: ['I', 'E', 'N', 'M', 'L', 'F', 'D'])\\nopt_sol10=[]", 'verif': "verify_submission(TALight_problem_name='RO_knapsack',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 10, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'labels':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N'],'costs':[15, 16, 17, 11, 13, 5, 7, 3, 1, 12, 9, 7],'vals':[50, 52, 54, 40, 45, 17, 18, 7, 8, 42, 30, 22],'Knapsack_Capacity':31,'forced_out':['F', 'E'],'forced_in':['B', 'I'],'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol10,'opt_sol10'),})"}
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
    instance_dict = {'s': 'GCTCTACGCTGGATTC', 't': 'ATGCCGCTTACCGTGATC'} # prendo i parametri dell'istanza
    ntasks = 8 # prendo il numero di task
    conv = Ansi2HTMLConverter(dark_bg = False) # inizializzo il convertitore HTML
    s = 'GCTCTACGCTGGATTC'
    t = 'ATGCCGCTTACCGTGATC'
    task01= {'general_description_before_task': 'Si considerino le seguenti sequenze di caratteri:<br/><br/>', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'goals': ['opt_sol', 'opt_val'], 'request': 'Fornire una massima sottosequenza comune tra le due stringhe:<br/>s = GCTCTACGCTGGATTC<br/>t = ATGCCGCTTACCGTGATC.', 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol1=""\\n#e la sua lunghezza:\\nopt_val1=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 1, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol1,'opt_sol1'),'opt_val':(opt_val1,'opt_val1'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol1` una sottosequnza ottima\\nopt_sol1=SONOUNASTRINGA\\n#Immetti in `opt_val1` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val1=14'}
    task02= {'general_description_before_task': '', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'beginning': 'CC', 'goals': ['opt_sol', 'opt_val'], 'request': 'Fornire una stringa di lunghezza massima che inizi col prefisso CC e sia sottosequenza comune tra: <br/>s = GCTCTACGCTGGATTC<br/>t = ATGCCGCTTACCGTGATC.', 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol2=""\\n#e la sua lunghezza:\\nopt_val2=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 2, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'CC','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol2,'opt_sol2'),'opt_val':(opt_val2,'opt_val2'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol2` una sottosequnza ottima\\nopt_sol2=SONOUNASTRINGA\\n#Immetti in `opt_val2` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val2=14'}
    task03= {'general_description_before_task': '', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'reduce_s_to_its_suffix_of_length': 15, 'goals': ['opt_sol', 'opt_val'], 'request': "Fornire una massima sottosequenza comune tra:<br/><b>il suffisso </b> $s'$ = CTCTACGCTGGATTC di s e <br/>t = ATGCCGCTTACCGTGATC.", 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol3=""\\n#e la sua lunghezza:\\nopt_val3=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 3, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':15,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol3,'opt_sol3'),'opt_val':(opt_val3,'opt_val3'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol3` una sottosequnza ottima\\nopt_sol3=SONOUNASTRINGA\\n#Immetti in `opt_val3` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val3=14'}
    task04= {'general_description_before_task': '', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'reduce_s_to_its_suffix_of_length': 11, 'goals': ['opt_sol', 'opt_val'], 'request': "Fornire una massima sottosequenza comune tra:<br/><b>il suffisso </b> $s'$ = ACGCTGGATTC di s e <br/>t = ATGCCGCTTACCGTGATC.", 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol4=""\\n#e la sua lunghezza:\\nopt_val4=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 4, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':11,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol4,'opt_sol4'),'opt_val':(opt_val4,'opt_val4'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol4` una sottosequnza ottima\\nopt_sol4=SONOUNASTRINGA\\n#Immetti in `opt_val4` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val4=14'}
    task05= {'general_description_before_task': '', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'reduce_s_to_its_suffix_of_length': 9, 'goals': ['opt_sol', 'opt_val'], 'request': "Fornire una massima sottosequenza comune tra:<br/><b>il suffisso </b> $s'$ = GCTGGATTC di s e <br/>t = ATGCCGCTTACCGTGATC.", 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol5=""\\n#e la sua lunghezza:\\nopt_val5=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 5, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':9,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol5,'opt_sol5'),'opt_val':(opt_val5,'opt_val5'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol5` una sottosequnza ottima\\nopt_sol5=SONOUNASTRINGA\\n#Immetti in `opt_val5` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val5=14'}
    task06= {'general_description_before_task': '', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'reduce_t_to_its_suffix_of_length': 13, 'goals': ['opt_sol', 'opt_val'], 'request': "Fornire una massima sottosequenza comune tra: <br/><b>il suffisso</b>  $t'$ = GCTTACCGTGATC di t e <br/>s = GCTCTACGCTGGATTC.", 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol6=""\\n#e la sua lunghezza:\\nopt_val6=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 6, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':13,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol6,'opt_sol6'),'opt_val':(opt_val6,'opt_val6'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol6` una sottosequnza ottima\\nopt_sol6=SONOUNASTRINGA\\n#Immetti in `opt_val6` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val6=14'}
    task07= {'general_description_before_task': '', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'reduce_t_to_its_suffix_of_length': 11, 'goals': ['opt_sol', 'opt_val'], 'request': "Fornire una massima sottosequenza comune tra: <br/><b>il suffisso</b>  $t'$ = TTACCGTGATC di t e <br/>s = GCTCTACGCTGGATTC.", 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol7=""\\n#e la sua lunghezza:\\nopt_val7=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 7, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':11,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol7,'opt_sol7'),'opt_val':(opt_val7,'opt_val7'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol7` una sottosequnza ottima\\nopt_sol7=SONOUNASTRINGA\\n#Immetti in `opt_val7` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val7=14'}
    task08= {'general_description_before_task': '', 'tot_points': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'reduce_t_to_its_suffix_of_length': 9, 'goals': ['opt_sol', 'opt_val'], 'request': "Fornire una massima sottosequenza comune tra: <br/><b>il suffisso</b>  $t'$ = ACCGTGATC di t e <br/>s = GCTCTACGCTGGATTC.", 'init_answ_cell_msg': '#Inserisci la tua risposta (una stringa, per esempio "TATATAX")\\nopt_sol8=""\\n#e la sua lunghezza:\\nopt_val8=7', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 8, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':9,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol8,'opt_sol8'),'opt_val':(opt_val8,'opt_val8'),})", 'init_answ_cell_msg_automatic': '#Inserisci in `opt_sol8` una sottosequnza ottima\\nopt_sol8=SONOUNASTRINGA\\n#Immetti in `opt_val8` il valore della soluzione introdotta (un intero, la lunghezza della stringa introdotta)\\nopt_val8=14'}
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
    instance_dict = {'n': 24, 'm': 40, 'edges': '[(S,G)(S,A)(S,E)(G,B)(G,F)(E,F)(E,C)(F,D)(D,C)(D,B)(A,C)(A,B)(G,O)(B,Q)(O,Q)(O,M)(Q,I)(M,I)(M,H)(I,L)(L,H)(N,L)(P,H)(N,P)(N,W)(P,X)(W,T)(W,V)(W,X)(X,R)(X,Y)(V,Z)(V,R)(Z,T)(Z,U)(R,U)(U,Y)(Y,T)(O,P)(Q,N)]'} # prendo i parametri dell'istanza
    ntasks = 3 # prendo il numero di task
    conv = Ansi2HTMLConverter(dark_bg = False) # inizializzo il convertitore HTML
    n = 24
    m = 40
    edges = '[(S,G)(S,A)(S,E)(G,B)(G,F)(E,F)(E,C)(F,D)(D,C)(D,B)(A,C)(A,B)(G,O)(B,Q)(O,Q)(O,M)(Q,I)(M,I)(M,H)(I,L)(L,H)(N,L)(P,H)(N,P)(N,W)(P,X)(W,T)(W,V)(W,X)(X,R)(X,Y)(V,Z)(V,R)(Z,T)(Z,U)(R,U)(U,Y)(Y,T)(O,P)(Q,N)]'
    task01= {'general_description_before_task': 'Si consideri il grafo non diretto $G$, con pesi sugli archi.', 'tot_points': 70, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'componenti_stato': [{'ciclo': 'edgeset'}, {'taglio': 'edgeset'}, {'shore': 'nodeset'}], 'task_state_modifier': ['edgecol', 'nodetag', 'edgetag', 'orientation', 'refresh'], 'select': ['NESSUNA [ciclo]- il mio certificato è un ciclo specificato come un sottoinsieme di archi', 'TUTTE [taglio] - il mio certificato è un taglio espresso come il sottoinsieme degli archi ricompresi nel taglio.', 'TUTTE [shore] - il mio certificato è un taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S )', 'ALCUNE MA NON TUTTE, perchè non tutte [ciclo] - un ciclo per certificare che non è in tutte.', 'ALCUNE MA NON TUTTE, perchè alcune [taglio] - un taglio per certificare che è in qualcuna. Il taglio espresso come il sottoinsieme degli archi compresi nel taglio.', 'ALCUNE MA NON TUTTE,  perchè alcune [shore] - un taglio per certificare che è in qualcuna. Il taglio espresso con un sottoinsieme S dei nodi (gli archi del taglio saranno quelli con un estremo in S ).'], 'goals': ['certificato1'], 'request': "Ritornare una soluzione che rispetti l'opzione selezionata", 'init_answ_cell_msg': '#Seleziona nodi e/o archi (colora i nodi cliccando e gli archi con il bottone) \\n Scegliere poi un opzione di risposta tra le successive.', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 1, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol1,'opt_sol1'),'opt_val':(opt_val1,'opt_val1'),})", 'init_answ_cell_msg_automatic': '#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")'}
    task02= {'general_description_before_task': "Si consideri il grafo non-diretto $G$, con pesi sugli archi e l'arco (A,B).", 'tot_points': 70, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'componenti_stato': [{'col3': 'edgecol'}], 'task_state_modifier': ['edgecol', 'refresh'], 'select': ['3-COLORAZIONE DEGLI ARCHI [col3]- il mio certificato è una 3-colorazione degli archi'], 'goals': ['certificato2'], 'request': "Restituire un grafo in cui si certifica se l'arco è in tutte, nessuna o alcune ma non tutte le soluzioni ottime.", 'init_answ_cell_msg': '#Seleziona nodi e/o archi (colora i nodi cliccando e gli archi con il bottone) \\n Scegliere poi un opzione di risposta tra le successive.', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 1, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol1,'opt_sol1'),'opt_val':(opt_val1,'opt_val1'),})", 'init_answ_cell_msg_automatic': '#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")'}
    task03= {'general_description_before_task': "Si consideri il grafo non-diretto $G$, con pesi sugli archi e l'arco (A,B).", 'tot_points': 70, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'componenti_stato': [{'mia_orientazione': 'orientation'}, {'U': 'nodeset'}, {'F': 'edgeset'}], 'task_state_modifier': ['edgecol', 'orientation', 'refresh'], 'select': ['Yes, ORIENTAZIONE ACICLICA [mia_orientazione] - il mio certificato è una orientazione aciclica', 'No, FORBIDDEN SUBGRAPH NODE SET U [U] - il mio certificato è un sottografo sui nodi U', 'No, FORBIDDEN SUBGRAPH EDGE SET F [F] - il mio certificato è un sottografo di archi F'], 'goals': ['certificato3'], 'request': "Restituire un grafo in cui si certifica se l'arco è in tutte, nessuna o alcune ma non tutte le soluzioni ottime.", 'init_answ_cell_msg': '#Seleziona nodi e/o archi (colora i nodi cliccando e gli archi con il bottone) \\n Scegliere poi un opzione di risposta tra le successive.', 'verif': "verify_submission(TALight_problem_name='RO_lcs',checkers=['TALight', 'embedded_in_notebook'],task_dict={'task': 1, 'pt_tot': 45, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0}, input_data_assigned={'s':'GCTCTACGCTGGATTC','t':'ATGCCGCTTACCGTGATC','beginning':'','ending':'','forbidden_s_interval_first_pos':1000000,'forbidden_s_interval_last_pos':0,'reduce_s_to_its_suffix_of_length':16,'reduce_s_to_its_prefix_of_length':16,'reduce_t_to_its_suffix_of_length':18,'reduce_t_to_its_prefix_of_length':18,'partialDPtable':[],'CAP_FOR_NUM_OPT_SOLS':10,'CAP_FOR_NUM_SOLS':10,}, long_answer_dict={'opt_sol':(opt_sol1,'opt_sol1'),'opt_val':(opt_val1,'opt_val1'),})", 'init_answ_cell_msg_automatic': '#Seleziona nodi e/o archi (colora i nodi cliccando su essi e gli archi con il bottone "Colora Archi")'}
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
