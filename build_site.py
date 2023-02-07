####################################################################################################################
#                                                                                                                  #
#                                                   INTRODUZIONE                                                   #
#                                                                                                                  #
####################################################################################################################

# Per questo progetto è stato utilizzato Django, un framework di Python. L'idea è tenere traccia delle operazioni
# dello studente durante l'esame e permettergli di sottoporre richieste al server TALight per ottenere dei feedback
# sulle sue soluzioni, consentendogli inoltre di caricare file di qualsiasi formato.
# In Django, una pagina visualizzabile sul sito corrisponde ad una view, ovvero ad una funzione definita così (nel 
# modo più semplice):
#
# def nome_view(request):
#    [corpo della funzione]
#    return render(request, pagina_html, context)
#
# - request: corrisponde alla richiesta di avvio della view
# - pagina_html: pagina a cui verrà reindirizzato lo studente una volta effettuata la request (click su un bottone,
#                caricamento di un file, ecc.)
# - context: descrittore dei parametri della view (sarà più chiaro in seguito)
#
# In generale, lo scopo di questo file è generare altri file python e HTML, nello specifico questi
#
# RO_browser
#    |
#    |_esame
#        |
#        |_forms.py
#        |
#        |_urls.py
#        |
#        |_views.py
#        |
#        |_templates
#            |
#            |_esame
#                |
#                |_problema1.html
#                |
#                |_problema2.html
#                |
#                |_ ...


####################################################################################################################
#                                                                                                                  #
#                                                     START                                                        #
#                                                                                                                  #
####################################################################################################################

import os
import ruamel.yaml
import ast
from pathlib import Path
from graph_designer import init_graph_html, write_yaml

import site_utils as su

# da rimuovere in seguito
while True:
    yes_no = input("Sei sicuro di voler inizializzare il sito? Così facendo eventuali risultati salvati andranno persi!\n[y/N]\n")
    if yes_no =="N" or yes_no == "n" or yes_no == "no":
        print("\nOK, interrompo l'inizializzazione. Se vuoi riavviare il server senza perdere i risultati acquisiti esegui 'manage.py runserver' .")
        exit(0)
    elif yes_no == "y" or yes_no == "yes":
        print("\nOK, procedo con l'inizializzazione.")
        break

# dichiaro il path di tutti i file utili

# da sostituire a integrazione completata
'''
#FEEDBACKS = os.path.join(Path.home(),'corsi','RO','esami','RO_browser','simulazione_esame','browser_feedback_log','feedbacks.yaml') # yaml contenente i feedback suddivisi per esercizio e per task
#FEEDBACK_SAVED_LOG = os.path.join(Path.home(),'corsi','RO','esami','RO_browser','simulazione_esame','browser_feedback_log','feedback_saved_log.yaml')  # yaml contenente i feedback salvati suddivisi per esercizio e per task
#POINTS_YAML = os.path.join(Path.home(),'corsi','RO','esami','RO_browser','simulazione_esame','browser_feedback_log','points.yaml')  # yaml contenente i punti suddivisi per esercizio e per task
#SAVED_SCORES = os.path.join(Path.home(),'corsi','RO','esami','RO_browser','simulazione_esame','browser_feedback_log','saved_scores.yaml')  # yaml contenente i punti relativi agli esercizi salvati suddivisi per esercizio e per task
#RTAL_URL='ws://127.0.0.1:8008 # connessione a localhost porta 8008'
'''
home = str(Path.home())
META_YAML_TEMPL = os.path.join(home,"TALight","example_problems","tutorial","RO_EX","meta.yaml")
EXAM_DIRECTORY = os.path.join(os.getcwd(),"simulazione_esame")
VIEWS_DIRECTORY = os.path.join(os.getcwd(),"esame","generated","views.py")
URLS_DIRECTORY = os.path.join(os.getcwd(),"esame","generated","urls.py")
FORMS_DIRECTORY = os.path.join(os.getcwd(),"esame","generated","forms.py")
GENERATED_DIRECTORY = os.path.join(os.getcwd(),"esame","generated")
ESAME_DIRECTORY = os.path.join(os.getcwd(),"esame")
TEMPLATES_DIRECTORY = os.path.join(os.getcwd(),"esame","templates","esame")
FEEDBACKS = os.path.join(os.getcwd(),"simulazione_esame","browser_feedback_log","feedbacks.yaml")
FEEDBACK_SAVED_LOG = os.path.join(os.getcwd(),"simulazione_esame","browser_feedback_log","feedback_saved_log.yaml")
PROBLEM = su.surf_problem(EXAM_DIRECTORY)
PROBLEM_KEYS = sorted(PROBLEM.keys()) # !
POINTS_YAML = os.path.join(os.getcwd(),"simulazione_esame","browser_feedback_log","points.yaml")
SAVED_SCORES = os.path.join(os.getcwd(),"simulazione_esame","browser_feedback_log","saved_scores.yaml")
global_args = {}

# raccolgo i servizi per tutti i problemi RO_* coinvolti

for key in PROBLEM_KEYS:
    meta = META_YAML_TEMPL.replace("EX",PROBLEM[key]['name'])
    with open(meta,'r') as stream:
        try:
            META_YAML = ruamel.yaml.safe_load(stream)
        except ruamel.yaml.YAMLError as exc:
            print(exc)
            exit(1)
    global_args[key] = META_YAML['services']['check']['args']

# raccolgo tutti gli argomenti degli yaml per ogni problema 
   
global_args_dict = {}
all_exercises = {}
for key in PROBLEM_KEYS:
    all_exercises[key] = {}
    all_exercises[key]["instance"] = PROBLEM[key]['instance']
    all_exercises[key]["tasks"] = PROBLEM[key]['tasks']
    all_exercises[key]["ntasks"] = len(all_exercises[key]["tasks"])
    all_exercises[key]["name"] = PROBLEM[key]['name']
    all_exercises[key]["instance"] = PROBLEM[key]['instance']
    all_exercises[key]["graphic_instance_descriptor"] = PROBLEM[key]["graphic_instance_descriptor"]
    all_exercises[key]["conclusion"] = PROBLEM[key]["general_description_to_conclude"]   

def match_yaml_args():
    txt = ""
    for key in PROBLEM_KEYS: # per ogni problema
        global_args_dict[key] = {} 
        for instance_key in all_exercises[key]["instance"].keys(): # per ogni chiave dell'istanza del problema
            if instance_key in global_args[key]: # se la chiave è richiesta anche nello yaml la stampo
                # a seconda che si tratti di una stringa o no stampo in modo diverso
                arg = all_exercises[key]["instance"][instance_key]            
                if type(arg) == str:
                    txt += f"{instance_key} = '{arg}'\n"
                else:
                    txt += f"{instance_key} = {arg}\n"               
                global_args_dict[key][instance_key] = arg # aggiungo l'argomento alla lista
    return txt

               
f = open(os.path.join(home,VIEWS_DIRECTORY),"w")
f.write("import os\n")
f.write("import shutil\n")
f.write("import ast\n")
f.write("import ruamel\n\n")
f.write("from datetime import datetime\n")
f.write("from django.shortcuts import render,redirect\n")
f.write("from django.contrib import messages\n")
f.write("from .forms import answer,uploaded_file\n")
f.write("from ansi2html import Ansi2HTMLConverter\n")
f.write("from django.core.files.storage import FileSystemStorage\n")
f.write("from pathlib import Path\n")
f.write("\n")
f.write("import rtal_lib as rl\n")
f.write("\n")
f.write(f"home = str(Path.home())\n")
f.write(f"FEEDBACKS = os.path.join(home,'{FEEDBACKS}') # yaml contenente i feedback suddivisi per esercizio e per task\n")
f.write(f"FEEDBACK_SAVED_LOG = os.path.join(home,'{FEEDBACK_SAVED_LOG}')  # yaml contenente i feedback salvati suddivisi per esercizio e per task\n")
f.write(f"POINTS_YAML = '{POINTS_YAML}'  # yaml contenente i punti suddivisi per esercizio e per task\n")
f.write(f"SAVED_SCORES = '{SAVED_SCORES}'  # yaml contenente i punti relativi agli esercizi salvati suddivisi per esercizio e per task\n")
f.write("RTAL_URL='ws://127.0.0.1:8008' # connessione a localhost porta 8008\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                   CONTEXTS                                                       #
#                                                                                                                  #
####################################################################################################################

# Commento per "contexts" da stampare su views.py

txt = f"# Il dizionario 'contexts' contiene tutte le informazioni utili ad ogni esercizio. Abbiamo deciso\n"
txt += f"# di gestire il salvataggio dei dati tramite file yaml, percio' dobbiamo tenere traccia per ogni\n"
txt += f"# esercizio e per ogni task del punteggio e dei feedback. In generale, assegnamo a ogni esercizio\n"
txt += f"# il suo context, il quale avra' nome context_ESERCIZIO (e.g. context_knapsack, context_lcs, ...).\n"
txt += f"# La struttura di contexts è la seguente (ogni nodo rappresenta una entry del dizionario):\n"
txt += f"\n"
txt += f"# contexts\n"
txt += f"#  |\n"
txt += f"#  |_ context_knapsack: identifica a quale problema si riferisce il context\n"
txt += f"#  |    |\n"
txt += f"#  |    |_data: raccoglitore dei dati dell'esercizio\n"
txt += f"#  |        |\n"
txt += f"#  |        |_task01\n"
txt += f"#  |        |   |\n"
txt += f"#  |        |   |_question: domanda relativa alla task01\n"
txt += f"#  |        |   |\n"
txt += f"#  |        |   |_feedback: feedback di TALight alla soluzione dell'utente (quando prodotto)\n"
txt += f"#  |        |   |\n"
txt += f"#  |        |   |_goals: nome dei goal per la task01\n"
txt += f"#  |        |\n"
txt += f"#  |        |_task02\n"
txt += f"#  |        |   |\n"
txt += f"#  |        |   |_question: domanda relativa alla task02\n"
txt += f"#  |        |   |\n"
txt += f"#  |        |   |_feedback: feedback di TALight alla soluzione dell'utente (quando prodotto)\n"
txt += f"#  |        |   |\n"
txt += f"#  |        |   |_goals: nome dei goal per la task02\n"
txt += f"#  |        |\n"
txt += f"#  |        .\n"
txt += f"#  |        .\n"
txt += f"#  |        .\n"
txt += f"#  |\n"        
txt += f"#  |_ context_lcs\n"
txt += f"#  |\n"
txt += f"#  .\n"
txt += f"#  .\n"
txt += f"#  .\n"
txt += f"\n"
txt += f"# Fondamentalmente, il dizionario contexts contiene tutte le informazioni correntemente presenti\n"
txt += f"# sul sito e che possono anche essere trasferite su uno yaml (ad esempio, ogni feedback viene \n"
txt += f"# riportato sul file yaml che raccoglie tutti i feedback di TALight riguardanti le ultime\n"
txt += f"# sottomissioni dell'utente). In pratica tutto ciò che viene visualizzato sul sito è contenuto\n"
txt += f"# in contexts.\n"
txt += f"\n"

# Qui stampiamo effettivamente i context per ogni esercizio
txt += f"contexts = {{" # dichiariamo contexts
for key in PROBLEM.keys(): # per ogni esercizio
    txt += f"'context_{all_exercises[key]['name']}': {{'data'  :{{" # inseriamo l'entry context_*nome esercizio*
    for k in all_exercises[key]['tasks'].keys(): # poi per ogni task trasformiamo la richiesta in html
        descr_before_task = ""
        if 'general_description_before_task' in all_exercises[key]['tasks'][k].keys():
            descr_before_task = all_exercises[key]['tasks'][k]['general_description_before_task'].replace('__','').replace('$','')
        d = {"question":f"<label>{all_exercises[key]['tasks'][k]['request'].replace('__','')}{all_exercises[key]['tasks'][k]['init_answ_cell_msg_automatic'].replace('#','<br>')}</label>","feedback":"", "goals":all_exercises[key]['tasks'][k]['goals'],"descr_before_task":f"<label>{descr_before_task}</label>"}
        if 'componenti_stato' in all_exercises[key]['tasks'][k].keys():
            d['componenti_stato'] = all_exercises[key]['tasks'][k]['componenti_stato']
        if 'task_state_modifier' in all_exercises[key]['tasks'][k].keys():
            d['task_state_modifier'] = all_exercises[key]['tasks'][k]['task_state_modifier']
        if 'select' in all_exercises[key]['tasks'][k].keys():
            d['select'] = all_exercises[key]['tasks'][k]['select']
        if int(k)< 10:              
            txt += f"'task0{k}': {d},"
        else:
            txt += f"'task{k}': {d},"
    txt += "}},"
txt += "}\n"
f.write(txt)
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                    SCORES                                                        #
#                                                                                                                  #
####################################################################################################################

# Commento per "scores" da stampare su views.py

txt += f"# Anche qui vogliamo tenere traccia dei punti dell'utente per ogni esercizio a seconda della\n"
txt += f"# sottomissione corrente. In particolare, ci interessano gli score per l'intero esercizio, ovvero\n"
txt += f"# la somma dei punti per ciascuna voce (sicuri, possibili, fuori portata).\n"
txt += f"\n"

# Qui stampiamo gli score

txt = f"scores = {{" # dichiariamo scores
for key in PROBLEM.keys(): # per ogni problema
    txt += f"'score_{all_exercises[key]['name']}': {{'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0}}," # inizializzo gli score
txt += "}\n"
f.write(txt)
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                MATCH YAML ARGS                                                   #
#                                                                                                                  #
####################################################################################################################

# Qui chiamiamo la funzione 'match_yaml_args()' definita prima. In pratica vado a cercare nello yaml "originale" del problema
# gli stessi elementi che si ripresentano anche nell'istanza fornita dal problem generator (ad esempio, per il problema
# knapsack ho un'istanza contenente vari argomenti che descrivono universalmente l'istanza, per cui prendo quelli richiesti 
# dallo yaml di RO_knapsack e scelgo di tenere quelli che corrispondono stampandoli direttamente come variabili all'interno 
# della view.

f.write(match_yaml_args())
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                           WRITE TO YAML FEEDBACK                                                 #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione write_to_yaml_feedback

f.write("def write_to_yaml_feedback(yaml_path,exercise,task,feedback):\n")
f.write("    # apro e leggo lo yaml contenente i feedback\n")
f.write("    with open(yaml_path,'r') as stream:\n")
f.write("        try:\n")
f.write("            full_yaml_dict = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    # scrivo il feedback in base alla task a cui è riferito\n")
f.write("    if task<10:\n")
f.write("       full_yaml_dict[f'context_{exercise}']['data'][f'task0{task}']['feedback'] = feedback\n")
f.write("    else:\n")
f.write("        full_yaml_dict[f'context_{exercise}']['data'][f'task{task}']['feedback'] = feedback\n")
f.write("    # apro lo yaml contenente i feedback e scrivo il nuovo feedback\n")
f.write("    f = open(yaml_path,'w')\n")
f.write("    ruamel.yaml.dump(full_yaml_dict, f, default_flow_style=False)\n")
f.write("    f.close()\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                   GET SCORES                                                     #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione get_scores

f.write("def get_scores(feedback):\n")
f.write("    points = {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0}\n")
f.write("    try: # se è un feedback contenente punti faccio il parsing\n")
f.write("        pos1 = feedback.index('punti sicuri')\n")
f.write("        pos2 = feedback[pos1:].index(':') + pos1\n")
f.write("        pos3 = feedback[pos2:].index(']') + pos2\n")
f.write("        if feedback[pos2+1:pos3] == ' None':\n")
f.write("            points['punti_sicuri'] = 0\n")
f.write("        else:\n")
f.write("            points['punti_sicuri'] = int(feedback[pos2+1:pos3])\n")
f.write("        pos1 = feedback.index('punti aggiuntivi possibili')\n")
f.write("        pos2 = feedback[pos1:].index(':') + pos1\n")
f.write("        pos3 = feedback[pos2:].index(']') + pos2\n")
f.write("        if feedback[pos2+1:pos3] == ' None':\n")
f.write("            points['punti_aggiuntivi_possibili'] = 0\n")
f.write("        else:\n")
f.write("            points['punti_aggiuntivi_possibili'] = int(feedback[pos2+1:pos3])\n")
f.write("        pos1 = feedback.index('punti fuori portata')\n")
f.write("        pos2 = feedback[pos1:].index(':') + pos1\n")
f.write("        pos3 = feedback[pos2:].index(']') + pos2\n")
f.write("        if feedback[pos2+1:pos3] == ' None':\n")
f.write("            points['punti_fuori_portata'] = 0\n")
f.write("        else:\n")
f.write("            points['punti_fuori_portata'] = int(feedback[pos2+1:pos3])\n")
f.write("    except: # se non è un feedback contenente punti vuol dire che non ho fatto punti\n")
f.write("        pass\n")
f.write("    return points\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                   HTML SCORE                                                     #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione html_score

f.write("def html_score(ex):\n")
f.write("    # traduco i colori in html\n")
f.write("    green = '<font color=\"green\">'\n")
f.write("    red = '<font color=\"red\">'\n")
f.write("    blue = '<font color=\"blue\">'\n")
f.write("    close = '</font>'\n")
f.write("    # Vado a leggermi i punteggi\n")
f.write("    with open(POINTS_YAML,'r') as stream:\n")
f.write("        try:\n")
f.write("            points_dict = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    # punti totali per l'esercizio\n")
f.write("    punti_sicuri = 0\n")
f.write("    punti_aggiuntivi_possibili = 0\n")
f.write("    punti_fuori_portata = 0\n")
f.write("    # sommo i punti di tutte le task\n")
f.write("    for task in points_dict[ex].keys():\n")
f.write("        punti_sicuri += points_dict[ex][task]['punti_sicuri']\n")
f.write("        punti_aggiuntivi_possibili += points_dict[ex][task]['punti_aggiuntivi_possibili']\n") 
f.write("        punti_fuori_portata += points_dict[ex][task]['punti_fuori_portata']\n") 
f.write("    # li riporto qui associando i colori ai punti (verde = sicuri, blu = possibili, rosso = fuori portata)\n")
f.write("    html_ps = f'{green}{punti_sicuri}/{ex_tot_points[ex]}{close}'\n")
f.write("    html_pa = f'{blue}{punti_aggiuntivi_possibili}/{ex_tot_points[ex]}{close}'\n")
f.write("    html_pf = f'{red}{punti_fuori_portata}/{ex_tot_points[ex]}{close}'\n")
f.write("    return {'punti_sicuri': html_ps, 'punti_aggiuntivi_possibili': html_pa, 'punti_fuori_portata':html_pf}\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                            GET SCORES FROM FEEDBACKS                                             #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione get_scores_from_feedbacks

f.write("def get_scores_from_feedbacks(FEEDBACK_YAML, POINTS_YAML):\n")
f.write("    # apro lo yaml con i feedback\n")
f.write("    with open(FEEDBACK_YAML,'r') as stream:\n")
f.write("        try:\n")
f.write("            feedback_dict = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    points_dict = {}\n")
f.write("    for context in contexts.keys(): # per ogni esercizio\n")
f.write("        esercizio = f'{context[8:]}'\n")
f.write("        points_dict[esercizio] = {} # inizializzo il dizionario dei punti per l'esercizio\n")
f.write("        for task in contexts[context]['data'].keys(): # per ogni task\n")
f.write("            points_dict[esercizio][task] = {} # inizializzo il dizionario dei punti per la task\n")
f.write("            feedback = contexts[context]['data'][task]['feedback'] # prendo il feedback\n")
f.write("            scores = get_scores(feedback) # e ricavo i punti\n")
f.write("            points_dict[esercizio][task]['punti_sicuri'] = scores['punti_sicuri']\n")
f.write("            points_dict[esercizio][task]['punti_aggiuntivi_possibili'] = scores['punti_aggiuntivi_possibili']\n")
f.write("            points_dict[esercizio][task]['punti_fuori_portata'] = scores['punti_fuori_portata']\n")
f.write("    # riporto i punteggi nello yaml dei punti\n")
f.write("    f = open(POINTS_YAML,'w')\n")
f.write("    ruamel.yaml.dump(points_dict, f, default_flow_style=False)\n")
f.write("    f.close()\n")
f.write("    # modifico i punti totali degli esercizi\n")
f.write("    for context in contexts.keys():\n")
f.write("        esercizio = f'{context[8:]}'\n")
f.write("        exam_context['data'][esercizio]['score'] = html_score(esercizio)\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                     GET GOALS                                                    #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione get_goals

f.write("def get_goals(answer,task):\n")
f.write("    answer_dict = {}\n")
f.write("    for goal in task['goals']: # per ogni goal richiesto dalla task\n")
f.write("    # prendo la soluzione dell'utente e provo a convertirla nei tre formati possibili (int, list, str)\n")
f.write("    # quando riesco a farlo la associo al goal e genero answer_dict\n")
f.write("        already_cast = 0\n")
f.write("        try:\n")
f.write("            answer_dict[goal] = int(answer.cleaned_data[f'ans_{goal}'])\n")
f.write("            already_cast = 1\n")
f.write("        except:\n")
f.write("            pass\n")
f.write("        try:\n")
f.write("            answer_dict[goal] = ast.literal_eval(answer.cleaned_data[f'ans_{goal}'])\n")
f.write("            already_cast = 1\n")
f.write("        except:\n")
f.write("            pass\n")
f.write("        if not already_cast:\n")
f.write("            answer_dict[goal] = answer.cleaned_data[f'ans_{goal}']\n")
f.write("    return answer_dict\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                     GET SELECT                                                    #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione get_select

f.write("def get_select(answer,task):\n")
f.write("    answer_dict = {}\n")
f.write("    for select in task['select']: # per ogni select nel task\n")
f.write("    # prendo la soluzione dell'utente e provo a convertirla nei tre formati possibili (int, list, str)\n")
f.write("    # quando riesco a farlo la associo al goal e genero answer_dict\n")
f.write("        already_cast = 0\n")
f.write("        try:\n")
f.write("            answer_dict[select] = int(answer.cleaned_data[f'ans_{select}'])\n")
f.write("            already_cast = 1\n")
f.write("        except:\n")
f.write("            pass\n")
f.write("        try:\n")
f.write("            answer_dict[select] = ast.literal_eval(answer.cleaned_data[f'ans_{select}'])\n")
f.write("            already_cast = 1\n")
f.write("        except:\n")
f.write("            pass\n")
f.write("        if not already_cast:\n")
f.write("            answer_dict[select] = answer.cleaned_data[f'ans_{select}']\n")
f.write("    return answer_dict\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                            RETRIEVE SAVED SOLUTIONS                                              #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione retrieve_saved_solutions

f.write("def retrieve_saved_solutions(request,ex):\n")
f.write("    context = f'context_{ex}' # prendo l'esercizio\n")
f.write("    # apro e leggo lo yaml dei feedback salvati\n")
f.write("    with open(FEEDBACK_SAVED_LOG,'r') as stream:\n")
f.write("        try:\n")
f.write("            saved_log_dict = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    # lo aggiorno con i feedback correnti\n")
f.write("    for task in saved_log_dict[context]['data'].keys():\n")
f.write("        feedback = saved_log_dict[context]['data'][task]['feedback']\n")
f.write("        contexts[context]['data'][task]['feedback'] = feedback\n")
f.write("        write_to_yaml_feedback(FEEDBACKS,ex,int(task[-2:]),feedback)\n")
f.write("    print('\\n***********************************\\n')\n")
f.write("    print('\\nHo caricato gli ultimi risultati salvati come richiesto.\\n')\n")
f.write("    print('\\n***********************************\\n')\n")
f.write("    return redirect(ex)\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                     SAVE SCORES                                                  #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione save_scores

f.write("def save_scores(ex):\n")
f.write("    # apro e leggo il file dei punteggi correnti\n")
f.write("    with open(POINTS_YAML,'r') as stream:\n")
f.write("        try:\n")
f.write("            points = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    # apro e leggo il file dei punteggi salvati\n")
f.write("    with open(SAVED_SCORES,'r') as stream:\n")
f.write("        try:\n")
f.write("            saved_scores = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    # sostituisco i punti salvati con i punti correnti\n")
f.write("    saved_scores[ex] = points[ex]\n")
f.write("    f = open(SAVED_SCORES,'w')\n")
f.write("    ruamel.yaml.dump(saved_scores, f, default_flow_style=False)\n")
f.write("    f.close()\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                  SAVE SOLUTIONS                                                  #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione save_solutions

f.write("def save_solutions(request,ex):\n")
f.write("    context = f'context_{ex}' # prendo l'esercizio\n")
f.write("    # apro e leggo il file dei feedback correnti\n")
f.write("    with open(FEEDBACKS,'r') as stream:\n")
f.write("        try:\n")
f.write("            last_log_dict = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    # apro e leggo il file dei feedback salvati\n")
f.write("    with open(FEEDBACK_SAVED_LOG,'r') as stream:\n")
f.write("        try:\n")
f.write("            saved_log_dict = ruamel.yaml.safe_load(stream)\n")
f.write("        except ruamel.yaml.YAMLError as exc:\n")
f.write("            print(exc)\n")
f.write("            exit(1)\n")
f.write("    # sostituisco i feedback salvati con i feedback correnti\n")
f.write("    saved_log_dict[context] = last_log_dict[context]\n")
f.write("    f = open(FEEDBACK_SAVED_LOG,'w')\n")
f.write("    ruamel.yaml.dump(saved_log_dict, f, default_flow_style=False)\n")
f.write("    f.close()\n")
f.write("    print('\\n***********************************\\n')\n")
f.write("    print('\\nHo salvato i risultati come richiesto.\\n')\n")
f.write("    print('\\n***********************************\\n')\n")
f.write("    save_scores(ex)\n")
f.write("    return redirect(ex)\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                  SIMPLE UPLOAD                                                   #
#                                                                                                                  #
####################################################################################################################

# Qui stampiamo la funzione simple_upload

f.write("def simple_upload(request,ex,task):\n")
f.write("    if request.method == 'POST' and request.FILES['myfile']:\n")
f.write("        update_dir = os.path.join(os.getcwd(),'simulazione_esame',f'{ex}','allegati') # cartella di caricamento del file\n")
f.write("        myfile = request.FILES['myfile']\n")
f.write("        fs = FileSystemStorage(location=update_dir)\n")
f.write("        time = datetime.now().strftime('%H:%M:%S')\n")
f.write("        filename = fs.save(f'{task}_{myfile.name}_{time}', myfile) # aggiungo task e timestamp al nome del file\n")
f.write("        return redirect(ex)\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                  EX TOT POINTS                                                   #
#                                                                                                                  #
####################################################################################################################

# Calcolo quanti sono in totale i punti raggiungibili per ogni esercizio

ex_tot = {}
etp = "ex_tot_points = {"
for key in PROBLEM_KEYS:
    tot = 0
    for task in all_exercises[key]["tasks"].keys():
        tot += all_exercises[key]["tasks"][task]["tot_points"]
    ex_tot[key] = tot
    etp += f"'{all_exercises[key]['name']}': {tot},"
etp += "}\n"

f.write(etp)
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                  EXAM CONTEXT                                                    #
#                                                                                                                  #
####################################################################################################################

# Context per la view esame

es = 1
txt = "exam_context = {'data'  :{"
for key in PROBLEM_KEYS: # per ogni esercizio scrivo i punti assegnando anche i colori
    green = '<font color="green">'
    red = '<font color="red">'
    blue = '<font color="blue">'
    close = '</font>'    
    txt += f"'{all_exercises[key]['name']}': {{'title': '{all_exercises[key]['name']}', 'score': {{'punti_sicuri':'{green}0/{ex_tot[key]}{close}', 'punti_aggiuntivi_possibili':'{blue}0/{ex_tot[key]}{close}','punti_fuori_portata':'{red}0/{ex_tot[key]}{close}'}}}},"
    es += 1
txt += "} }\n"
#txt += "'graph':{'title':'graph','score': {'punti_sicuri':0, 'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0}}}}\n" # da togliere in futuro
f.write(txt)
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                   ESAME.PY (view)                                                #
#                                                                                                                  #
####################################################################################################################

# Generiamo la view esame (pagina principale)

f.write("\n")
f.write("def esame(request):\n")  
f.write("    return render(request, os.path.join('esame','esame.html'), exam_context)\n")
f.write("\n")

####################################################################################################################
#                                                                                                                  #
#                                                   VIEWS.PY (view)                                                #
#                                                                                                                  #
####################################################################################################################

# Generiamo tutte le view, una per ogni problema        

for key in PROBLEM_KEYS:    
    f.write(f"context_{all_exercises[key]['name']} = contexts['context_{all_exercises[key]['name']}'] # dichiaro context_{all_exercises[key]['name']}\n") 
    f.write("\n")
    f.write(f"score_{all_exercises[key]['name']} = scores['score_{all_exercises[key]['name']}'] # dichiaro score_{all_exercises[key]['name']}\n") 
    f.write("\n")
    f.write(f"def {all_exercises[key]['name']}(request): # definisco il nome della view \n") 
    f.write(f"    rtalproblem = 'RO_{all_exercises[key]['name']}' # il corrispondente problema in TALight è RO_{all_exercises[key]['name']}\n") 
    f.write(f"    rtalservice = 'check' # vogliamo che venga richiesto il servizio check per il problema\n") 
    f.write(f"    rtaltoken = 'id625tbt_VR437029_OrLwSWKtpyrk1bS_RIVO_CARAPUCCI' # dummy token\n") 
    f.write(f"    instance_dict = {global_args_dict[key]} # prendo i parametri dell'istanza\n") 
    f.write(f"    ntasks = {all_exercises[key]['ntasks']} # prendo il numero di task\n") 
    f.write("    conv = Ansi2HTMLConverter(dark_bg = False) # inizializzo il convertitore HTML\n") 
    for el in all_exercises[key]["instance"].keys(): # dichiaro tutti gli argomenti dell'istanza come variabili per semplificare il codice
        try: # distinguo fra int, list e str
            if any(c.isalpha() for c in all_exercises[key]['instance'][el]) and type(all_exercises[key]['instance'][el]) == str:
                f.write(f"    {el} = '{all_exercises[key]['instance'][el]}'\n")    
            else:
               f.write(f"    {el} = {all_exercises[key]['instance'][el]}\n")  
        except:
            f.write(f"    {el} = {all_exercises[key]['instance'][el]}\n")  
    for k in all_exercises[key]['tasks'].keys(): # dichiaro tutte le task come variabili per semplificare il codice
        if int(k)<10:
            f.write(f"    task0{k}= {all_exercises[key]['tasks'][k]}\n")
        else:
            f.write(f"    task{k}={all_exercises[key]['tasks'][k]}\n")
    f.write(f"    for task in context_{all_exercises[key]['name']}['data'].keys():\n")
    f.write("        try:\n")
    forb_symbol = "\" # fix temporaneo errore sintassi yaml (attesa uniformazione)" 
    f.write(f"            context_{all_exercises[key]['name']}['data'][task]['question'] = context_{all_exercises[key]['name']}['data'][task]['question'].replace('\{forb_symbol}','').format(**vars())\n")
    f.write("        except:\n")
    f.write("            pass\n")
    f.write("    for i in range(1,ntasks+1):\n")
    f.write("        if i<10:\n")
    f.write("            if 'CapacityGen' in locals()[f'task0{i}'].keys(): # fix temporaneo errore sintassi yaml (attesa uniformazione)\n") 
    f.write("                instance_dict['Knapsack_Capacity'] = locals()[f'task0{i}']['CapacityGen']\n")
    f.write("            else:\n")
    f.write("                try:\n")
    f.write("                    instance_dict['Knapsack_Capacity'] = CapacityMax\n")
    f.write("                except:\n")
    f.write("                    pass\n")
    f.write("            if request.method == 'POST' and f'run_script_task0{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form\n") 
    f.write("                a = answer(request.POST)\n")
    f.write("                print(a)\n")
    f.write("                if a.is_valid():\n")
    f.write(f"                    answer_dict = get_goals(a,context_{all_exercises[key]['name']}['data'][f'task0{{i}}']) # prendo le risposte \n") 
    f.write("                    if answer_dict != {}:\n")
    f.write("                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte\n") 
    f.write("                        try: # se il feedback è corretto\n") 
    f.write("                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')\n")
    f.write("                        except Exception as e: # se non ho avviato TALight mando messaggio di errore\n") 
    f.write("                            answ = f'<b><font color=\"red\">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'\n")
    f.write("                    else: # dati non inseriti correttamente\n") 
    f.write("                            answ = '<b><font color=\"red\">Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.</font></b>'\n")
    f.write(f"                    write_to_yaml_feedback(FEEDBACKS,'{all_exercises[key]['name']}',i,answ) # se tutto ok scrivo il feedback nel file\n") 
    f.write(f"                    context_{all_exercises[key]['name']}['data'][f'task0{{i}}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina\n")
    f.write(f"                    try: # se il feedback è corretto aggiorno i punteggi\n") 
    f.write(f"                        score_{all_exercises[key]['name']}[f'task0{{i}}'] = safe_points(answ)\n")
    f.write(f"                    except:\n")
    f.write(f"                        pass\n")
    f.write("        else:\n")
    f.write("            try:\n")
    f.write("                instance_dict['Knapsack_Capacity'] = locals()[f'task{i}']['CapacityGen'] # fix temporaneo errore sintassi yaml (attesa uniformazione)\n")
    f.write("            except:\n")
    f.write("                instance_dict['Knapsack_Capacity'] = CapacityMax\n")
    f.write("            if request.method == 'POST' and f'run_script_task{i}' in request.POST: # richiesta che si attiva quando inserisco un valore nella form\n")
    f.write("                a = answer(request.POST)\n")
    f.write("                if a.is_valid():\n")
    f.write(f"                    answer_dict = get_goals(a,context_{all_exercises[key]['name']}['data'][f'task{{i}}'])\n")
    f.write("                    if answer_dict != {}:\n")
    f.write("                        rtalargs_dict = {'input_data_assigned':instance_dict,'answer_dict': answer_dict} # dizionario da passare a rtal_connect con istanza e risposte\n") 
    f.write("                        try: # se il feedback è corretto\n") 
    f.write("                            answ = conv.convert(rl.rtal_connect(RTAL_URL,rtalproblem,rtalservice,rtalargs_dict,rtaltoken)['feedback_string']).replace('#AAAAAA','#FFFFFF')\n")
    f.write("                        except Exception as e: # se non ho avviato TALight mando messaggio di errore\n") 
    f.write("                            answ = f'<b><font color=\"red\">Non ho potuto produrre alcun feedback. Hai avviato il server di TALight?</font></b><br><br>ERRORE: {str(e)}'\n")
    f.write("                    else: # dati non inseriti correttamente\n")
    f.write("                            answ = 'Non ho potuto richiedere alcun servizio, controlla che il tipo dei dati che hai immesso sia corretto.'\n")
    f.write(f"                    write_to_yaml_feedback(FEEDBACKS,'{all_exercises[key]['name']}',i,answ) # se tutto ok scrivo il feedback nel file\n")
    f.write(f"                    context_{all_exercises[key]['name']}['data'][f'task{{i}}']['feedback'] = answ # aggiungo il feedback al context per poterlo visualizzare nella pagina\n")
    f.write(f"                    try: # se il feedback è corretto aggiorno i punteggi\n")
    f.write(f"                        score_{all_exercises[key]['name']}[f'task{{i}}'] = safe_points(answ)\n")
    f.write(f"                    except:\n")
    f.write(f"                        pass\n")
    f.write("    get_scores_from_feedbacks(FEEDBACKS, POINTS_YAML)\n")
    f.write(f"    return render(request, 'esame/{all_exercises[key]['name']}.html', context_{all_exercises[key]['name']})\n\n")     
    f.write("def grafo_template(request): # definisco il nome della view\n")
    f.write("    return render(request,os.path.join('esame','grafo_template.html'))\n")
    task += 1

    
####################################################################################################################
#                                                                                                                  #
#                                                      URLS.PY                                                     #
#                                                                                                                  #
####################################################################################################################

# Generiamo il file urls.py contenente i riferimenti alle varie pagine (views)
# La struttura di urlpatterns è
#
# urlpatterns = [
#     path('nome_url/<tipo1:variabile1>/<tipo2:variabile2>/...', views.nome_view, name='nome_pagina')
#     path('nome_url/<tipo1:variabile1>/<tipo2:variabile2>/...', views.nome_view, name='nome_pagina')
#     ...
# ]
#
# - 'nome_url/<tipo1:variabile1>/<tipo2:variabile2>/...' : nome_url è il nome della pagina che verrà visualizzato nella barra degli indirizzi. Ogni parametro
#                                                          che si vuole passare al file html va dichiarato qui dentro col formato <tipo:nome>
# - views.nome_view: nome della funzione scritta in views.py da richiamare
# - name='nome_pagina': nome che identifica questa url (e' buona norma porlo uguale a nome_url)

def init_urls():
    f = open(URLS_DIRECTORY,"w")
    f.write("from django.urls import path\n")
    f.write("from . import views\n")
    f.write("from django.conf.urls import url\n")#aggiunto
    f.write("from django.views.generic import TemplateView\n")#aggiunto
    f.write("\n")
    f.write("urlpatterns = [\n")
    f.write("    path('',views.esame, name='home'),\n")
    for key in PROBLEM_KEYS:
        f.write(f"    path('{all_exercises[key]['name']}',views.{all_exercises[key]['name']}, name='{all_exercises[key]['name']}'),\n") # indirizzo tutte le view
    #f.write("    path('graph',views.graph, name='graph'),\n")
    f.write("    url('grafo_template',views.grafo_template, name='grafo_template'),\n")
    f.write("    path('retrieve_saved_solutions/<str:ex>',views.retrieve_saved_solutions, name='retrieve_saved_solutions'),\n") # prende come parametro ex 
    f.write("    path('save_solutions/<str:ex>',views.save_solutions,name='save_solutions'),\n") # prende come parametro ex 
    f.write("    path('simple_upload/<str:ex>/<str:task>',views.simple_upload,name='simple_upload'),\n") # prende come parametri ex e task
    f.write("]")
    f.close()

####################################################################################################################
#                                                                                                                  #
#                                                      FORMS.PY                                                    #
#                                                                                                                  #
####################################################################################################################

# Generiamo il file forms.py contenente il tipo di form utilizzabili per caricare file o risultati

def init_forms():
    # form per caricare i risultati
    goals = []
    f = open(FORMS_DIRECTORY,"w")
    f.write("#-*- coding: utf-8 -*-\n")
    f.write("from django import forms\n")
    f.write("\n")
    f.write("class answer(forms.Form):\n")
    # inserisco tutti i goal richiesti da un problema (inserisco un nuovo goal solo se non è già presente)
    for key in PROBLEM_KEYS:
        for task in all_exercises[key]["tasks"].keys():
            for goal in all_exercises[key]["tasks"][task]["goals"]:
                if goal not in goals:
                    f.write(f"    ans_{goal} = forms.CharField(max_length = 200,required=False)\n")
                    goals.append(goal)
    # form per caricare i file
    f.write("\n")
    f.write("class uploaded_file(forms.Form):\n")
    f.write("    file = forms.FileField()\n")
    f.close()    

####################################################################################################################
#                                                                                                                  #
#                                                  ESERCIZIO.HTML                                                  #
#                                                                                                                  #
####################################################################################################################

# I file presenti all'interno della directory templates sono due file html utili a generare i file html per ogni pagina.
# Qui generiamo un file html per ogni esercizio.

def init_esercizio_html():
    for key in PROBLEM_KEYS:
        if all_exercises[key]['name'] == "mst":
            init_esercizio_grafo_html()
        else:
            r = open(os.path.join(TEMPLATES_DIRECTORY,'esercizio_template.html'),'r')
            txt = "".join(r.readlines())
            txt = txt.replace("esercizio_tmp",all_exercises[key]['name']).replace("Titolo",all_exercises[key]['name']).replace("Istanza",su.instance_description(all_exercises[key]["instance"])).replace("esercizioxx",all_exercises[key]['name']).replace("Rappresentazione istanza",all_exercises[key]['graphic_instance_descriptor']).replace("Conclusione",all_exercises[key]["conclusion"]) # sostituisco le descrizioni generali in base all'esercizio
            r.close()
            f = open(os.path.join(GENERATED_DIRECTORY,f"{all_exercises[key]['name']}.html"),"w") # genero il file *nome esercizio*.html
            f.write(txt)
            f.close()
    
def init_esercizio_grafo_html():
        r = open(os.path.join(TEMPLATES_DIRECTORY,'esercizio_grafo_template.html'),'r')
        txt = "".join(r.readlines())
        txt = txt.replace("esercizio_tmp",all_exercises[key]['name']).replace("Titolo",all_exercises[key]['name']).replace("Istanza",su.instance_description(all_exercises[key]["instance"])).replace("esercizioxx",all_exercises[key]['name']).replace("Rappresentazione istanza",all_exercises[key]['graphic_instance_descriptor']).replace("Conclusione",all_exercises[key]["conclusion"]) # sostituisco le descrizioni generali in base all'esercizio
        r.close()
        f = open(os.path.join(GENERATED_DIRECTORY,f"{all_exercises[key]['name']}.html"),"w") # genero il file *nome esercizio*.html
        f.write(txt)
        f.close()


####################################################################################################################
#                                                                                                                  #
#                                                     ESAME.HTML                                                   #
#                                                                                                                  #
####################################################################################################################

# Genero il file esame.html (a differenza di esercizio.html non viene cambiato nulla, ma in futuro può essere utile)

def init_esame_html():
    keys = sorted(PROBLEM.keys())
    r = open(os.path.join(TEMPLATES_DIRECTORY,'esame_template.html'),'r')
    txt = "".join(r.readlines())
    r.close()
    f = open(os.path.join(GENERATED_DIRECTORY,"esame.html"),"w")
    f.write(txt)
    f.close()

####################################################################################################################
#                                                                                                                  #
#                                                EMPTY FEEDBACK LOG                                                #
#                                                                                                                  #
####################################################################################################################

# Inizializzo il file contenente i feedback (se non presente lo creo, se presente lo svuoto)

def empty_feedback_log(log_path):
    yaml_dict = {}
    for key in PROBLEM_KEYS:
        yaml_dict[f"context_{all_exercises[key]['name']}"] = {}
        yaml_dict[f"context_{all_exercises[key]['name']}"]['data'] = {}
        for task in PROBLEM[key]['tasks']:
            if task<10:
                yaml_dict[f"context_{all_exercises[key]['name']}"]['data'][f'task0{task}'] = {}
                yaml_dict[f"context_{all_exercises[key]['name']}"]['data'][f'task0{task}']['feedback'] = "" # svuoto
            else:
                yaml_dict[f"context_{all_exercises[key]['name']}"]['data'][f'task{task}'] = {}
                yaml_dict[f"context_{all_exercises[key]['name']}"]['data'][f'task{task}']['feedback'] = "" # svuoto
    # sovrascrivo il file 
    f = open(log_path,"w")
    ruamel.yaml.dump(yaml_dict, f, default_flow_style=False)
    f.close()

####################################################################################################################
#                                                                                                                  #
#                                                EMPTY SCORES LOG                                                  #
#                                                                                                                  #
####################################################################################################################

# Inizializzo il file contenente i punti (se non presente lo creo, se presente lo svuoto)

def empty_score_log(points_path):
    yaml_dict = {}
    for key in PROBLEM_KEYS:
        yaml_dict[all_exercises[key]['name']] = {}
        for task in PROBLEM[key]['tasks']:
            if task<10:
                yaml_dict[all_exercises[key]['name']][f'task0{task}'] = {}
                yaml_dict[all_exercises[key]['name']][f'task0{task}']['punti_sicuri'] = 0
                yaml_dict[all_exercises[key]['name']][f'task0{task}']['punti_aggiuntivi_possibili'] = 0
                yaml_dict[all_exercises[key]['name']][f'task0{task}']['punti_fuori_portata'] = 0
            else:
                yaml_dict[all_exercises[key]['name']][f'task{task}'] = {}
                yaml_dict[all_exercises[key]['name']][f'task{task}']['punti_sicuri'] = 0
                yaml_dict[all_exercises[key]['name']][f'task{task}']['punti_aggiuntivi_possibili'] = 0
                yaml_dict[all_exercises[key]['name']][f'task{task}']['punti_fuori_portata'] = 0
    # sovrascrivo il file 
    f = open(points_path,"w")
    ruamel.yaml.dump(yaml_dict, f, default_flow_style=False)
    f.close()

####################################################################################################################
#                                                                                                                  #
#                                                CLEAR SYMLINKS                                                    #
#                                                                                                                  #
####################################################################################################################

# Elimino i vecchi symlink relativi all'inizializzazione precedente
def clear_symlinks():
    rootdir = ESAME_DIRECTORY
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            #print os.path.join(subdir, file)
            filepath = subdir + os.sep + file
            if os.path.islink(filepath):
                os.remove(filepath)
    
####################################################################################################################
#                                                                                                                  #
#                                                GENERATE SYMLINKS                                                 #
#                                                                                                                  #
####################################################################################################################

# Genero i nuovi symlink

def generate_symlinks():
    os.symlink(os.path.join(GENERATED_DIRECTORY,"views.py"),os.path.join(ESAME_DIRECTORY,"views.py"))
    os.symlink(os.path.join(GENERATED_DIRECTORY,"urls.py"),os.path.join(ESAME_DIRECTORY,"urls.py"))
    os.symlink(os.path.join(GENERATED_DIRECTORY,"forms.py"),os.path.join(ESAME_DIRECTORY,"forms.py"))
    for key in PROBLEM_KEYS:        
        os.symlink(os.path.join(GENERATED_DIRECTORY,f"{all_exercises[key]['name']}.html"),os.path.join(TEMPLATES_DIRECTORY,f"{all_exercises[key]['name']}.html"))    
    os.symlink(os.path.join(GENERATED_DIRECTORY,"esame.html"),os.path.join(TEMPLATES_DIRECTORY,"esame.html"))
    os.symlink(os.path.join(GENERATED_DIRECTORY,"grafo.html"),os.path.join(TEMPLATES_DIRECTORY,"grafo.html"))
    
####################################################################################################################
#                                                                                                                  #
#                                                 INIZIALIZZAZIONE                                                 #
#                                                                                                                  #
####################################################################################################################

empty_feedback_log(os.path.join(home,FEEDBACKS)) # svuoto il file dei feedback correnti
empty_feedback_log(os.path.join(home,FEEDBACK_SAVED_LOG)) # svuoto il file dei feedback salvati
empty_score_log(POINTS_YAML) # svuoto il file dei punteggi correnti
empty_score_log(SAVED_SCORES) # svuoto il file dei punteggi salvati
init_forms() # genero forms.py
init_urls() # genero urls.py
write_yaml()
init_esame_html()
init_graph_html()
init_esercizio_html()
clear_symlinks()
generate_symlinks()
