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

def esame(request):
    return render(request, os.path.join('esame','esame.html'), exam_context)

