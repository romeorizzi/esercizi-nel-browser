import os
import ruamel.yaml
from pathlib import Path
import markdown
from graph_designer import init_graph_html, write_yaml
import convert
import site_utils as su

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
# - pagina_html: pagina a cui verrà reindirizzato lo studente una volta effettuata la request (click su un bottone, caricamento di un file, ecc.)
# - context: descrittore dei parametri della view (sarà più chiaro in seguito)
#
# In generale, lo scopo di questo file è generare altri file python e HTML, nello specifico questi
#
# RO_browser
#    |_esame
#        |_forms.py
#        |_urls.py
#        |_views.py
#        |_templates
#            |_esame
#                |_problema1.html
#                |_problema2.html
#                |_ ...

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
    txt += '\n'
    return txt

# converto gli .instance in .yaml
print('Inizio con la generazione degli .yaml a partire dagli .instance')
convert.start()

# dichiaro il path di tutti i file utili
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
global_args_dict: dict = {}
all_exercises: dict = {}
for key in PROBLEM_KEYS:
    all_exercises[key] = {}
    all_exercises[key]["instance"] = PROBLEM[key]['instance']
    all_exercises[key]["tasks"] = PROBLEM[key]['tasks']
    all_exercises[key]["ntasks"] = len(all_exercises[key]["tasks"])
    all_exercises[key]["name"] = PROBLEM[key]['name']
    all_exercises[key]["graphic_instance_descriptor"] = PROBLEM[key]["graphic_instance_descriptor"]
    all_exercises[key]["conclusion"] = PROBLEM[key]["general_description_to_conclude"]

txt = open("esame/generated/views_template.py","r").read()
txt += f"FEEDBACKS = os.path.join(home,f'{FEEDBACKS}') # yaml contenente i feedback suddivisi per esercizio e per task\nFEEDBACK_SAVED_LOG = os.path.join(home,f'{FEEDBACK_SAVED_LOG}')  # yaml contenente i feedback salvati suddivisi per esercizio e per task\nPOINTS_YAML = f'{POINTS_YAML}'  # yaml contenente i punti suddivisi per esercizio e per task\nSAVED_SCORES = f'{SAVED_SCORES}'  # yaml contenente i punti relativi agli esercizi salvati suddivisi per esercizio e per task\n"
f = open(os.path.join(home,VIEWS_DIRECTORY),"w")
f.write(txt)

# Qui stampiamo effettivamente i context per ogni esercizio
txt = "contexts = {" # dichiariamo contexts
for key in PROBLEM.keys(): # per ogni esercizio
    txt += f"'context_{all_exercises[key]['name']}': {{'data':{{" # inseriamo l'entry context_*nome esercizio*
    for k in all_exercises[key]['tasks'].keys(): # poi per ogni task trasformiamo la richiesta in html
        tasks_k = all_exercises[key]['tasks'][k]
        request = markdown.markdown(tasks_k['request'].replace('\n','<br>').replace('\\n','<br>'), extensions=['markdown.extensions.extra'])
        descr_before_task = ""
        if 'general_description_before_task' in tasks_k:
            descr_before_task = markdown.markdown(tasks_k['general_description_before_task'], extensions=['markdown.extensions.extra'])
        goals = []
        for goal in tasks_k['goals']:
            goals.append({'goal':goal,'value':'','form':''})
        if 'answ_form' in tasks_k:
            for i in range(len(tasks_k['answ_form'])):
                goals[i]['form'] = tasks_k['answ_form'][i]['title']
                goals[i]['value'] = tasks_k['answ_form'][i]['init_var']
            d = {"question":f"<label>{request}</label>", "feedback":"", "goals":goals, "descr_before_task":f"<label>{descr_before_task}</label>"}
        else:
            init_answ = markdown.markdown(tasks_k['init_answ_cell_msg_automatic'].replace('\n','<br>').replace('\\n','<br>'), extensions=['markdown.extensions.extra'])
            d = {"question":f"<label>{request}{init_answ}</label>", "feedback":"", "goals":goals, "descr_before_task":f"<label>{descr_before_task}</label>"}
        if 'componenti_stato' in tasks_k:
            d['componenti_stato'] = tasks_k['componenti_stato']
        if 'task_state_modifier' in tasks_k:
            d['task_state_modifier'] = tasks_k['task_state_modifier']
        if 'select' in tasks_k:
            d['select'] = tasks_k['select']

        if int(k) < 10:
            txt += f"'task0{k}':{d},"
        else:
            txt += f"'task{k}':{d},"
    txt += "}},"
txt += "}\n\n"
f.write(txt)

####################################################################################################################
#                                                                                                                  #
#                                                    SCORES                                                        #
#                                                                                                                  #
####################################################################################################################

# Commento per "scores" da stampare su views.py
txt = "# Anche qui vogliamo tenere traccia dei punti dell'utente per ogni esercizio a seconda della\n# sottomissione corrente. In particolare, ci interessano gli score per l'intero esercizio, ovvero\n# la somma dei punti per ciascuna voce (sicuri, possibili, fuori portata).\n\nscores = {" # dichiariamo scores

# Qui stampiamo gli score
for key in PROBLEM.keys(): # per ogni problema
    txt += f"'score_{all_exercises[key]['name']}': {{'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0}}," # inizializzo gli score
txt += "}\n\n"
f.write(txt)

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
etp += "}\n\n"
f.write(etp)

####################################################################################################################
#                                                                                                                  #
#                                                  EXAM CONTEXT                                                    #
#                                                                                                                  #
####################################################################################################################

# Context per la view esame

es = 1
txt = "exam_context = {'data':{"
for key in PROBLEM_KEYS: # per ogni esercizio scrivo i punti assegnando anche i colori
    txt += f"'{all_exercises[key]['name']}': {{'title': '{all_exercises[key]['name']}', 'score': {{'punti_sicuri':'<font color=\"green\">0/{ex_tot[key]}</font>', 'punti_aggiuntivi_possibili': '<font color=\"blue\">0/{ex_tot[key]}</font>', 'punti_fuori_portata':'<font color=\"red\">0/{ex_tot[key]}</font>'}}}},"
    es += 1
txt += "}}\n\n"
f.write(txt)

####################################################################################################################
#                                                                                                                  #
#                                                   VIEWS.PY (view)                                                #
#                                                                                                                  #
####################################################################################################################

# Generiamo tutte le view, una per ogni problema

for key in PROBLEM_KEYS:
    f.write(f"context_{all_exercises[key]['name']} = contexts['context_{all_exercises[key]['name']}'] # dichiaro context_{all_exercises[key]['name']}\n\n")
    f.write(f"score_{all_exercises[key]['name']} = scores['score_{all_exercises[key]['name']}'] # dichiaro score_{all_exercises[key]['name']}\n\n")
    f.write(f"def {all_exercises[key]['name']}(request): # definisco il nome della view \n")
    f.write(f"    rtalproblem = 'RO_{all_exercises[key]['name']}' # il corrispondente problema in TALight è RO_{all_exercises[key]['name']}\n")
    f.write("    rtalservice = 'check' # vogliamo che venga richiesto il servizio check per il problema\n")
    f.write("    rtaltoken = 'id625tbt_VR437029_OrLwSWKtpyrk1bS_RIVO_CARAPUCCI' # dummy token\n")
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
    f.write(f"            context_{all_exercises[key]['name']}['data'][task]['question'] = context_{all_exercises[key]['name']}['data'][task]['question'].replace('{forb_symbol}','').format(**vars())\n")
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
    f.write("                    try: # se il feedback è corretto aggiorno i punteggi\n")
    f.write(f"                        score_{all_exercises[key]['name']}[f'task0{{i}}'] = safe_points(answ)\n")
    f.write("                    except:\n")
    f.write("                        pass\n")
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
    f.write("                    try: # se il feedback è corretto aggiorno i punteggi\n")
    f.write(f"                        score_{all_exercises[key]['name']}[f'task{{i}}'] = safe_points(answ)\n")
    f.write("                    except:\n")
    f.write("                        pass\n")
    f.write("    get_scores_from_feedbacks(FEEDBACKS, POINTS_YAML)\n")
    f.write(f"    return render(request, 'esame/{all_exercises[key]['name']}.html', context_{all_exercises[key]['name']})\n\n")
    f.write("def grafo_template(request): # definisco il nome della view\n")
    f.write("    return render(request,os.path.join('esame','grafo_template.html'))\n")
    ##task += 1


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
    f.write("from django.views.generic import TemplateView\n\n")#aggiunto
    f.write("urlpatterns = [\n")
    f.write("    path('',views.esame, name='home'),\n")
    for key in PROBLEM_KEYS:
        f.write(f"    path('{all_exercises[key]['name']}',views.{all_exercises[key]['name']}, name='{all_exercises[key]['name']}'),\n") # indirizzo tutte le view
    #f.write("    path('graph',views.graph, name='graph'),\n")
    f.write("    url('grafo_template',views.grafo_template, name='grafo_template'),\n")
    f.write("    path('retrieve_saved_solutions/<str:ex>',views.retrieve_saved_solutions, name='retrieve_saved_solutions'),\n") # prende come parametro ex
    f.write("    path('save_solutions/<str:ex>',views.save_solutions,name='save_solutions'),\n") # prende come parametro ex
    f.write("    path('simple_upload/<str:ex>/<str:task>',views.simple_upload,name='simple_upload'),\n]") # prende come parametri ex e tfask
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
    f.write("from django import forms\n\n")
    f.write("class answer(forms.Form):\n")
    # inserisco tutti i goal richiesti da un problema (inserisco un nuovo goal solo se non è già presente)
    for key in PROBLEM_KEYS:
        for task in all_exercises[key]["tasks"].keys():
            for goal in all_exercises[key]["tasks"][task]["goals"]:
                if goal not in goals:
                    f.write(f"    ans_{goal} = forms.CharField(max_length = 200,required=False)\n")
                    goals.append(goal)
    # form per caricare i file
    f.write("\nclass uploaded_file(forms.Form):\n")
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
            init_esercizio_grafo_html(key)
        else:
            r = open(os.path.join(TEMPLATES_DIRECTORY,'esercizio_template.html'),'r')
            txt = "".join(r.readlines())
            txt = txt.replace("esercizio_tmp",all_exercises[key]['name']).replace("Titolo",all_exercises[key]['name']).replace("Istanza",su.instance_description(all_exercises[key]["instance"])).replace("esercizioxx",all_exercises[key]['name']).replace("Rappresentazione istanza",all_exercises[key]['graphic_instance_descriptor']).replace("Conclusione",all_exercises[key]["conclusion"]) # sostituisco le descrizioni generali in base all'esercizio
            r.close()
            f = open(os.path.join(GENERATED_DIRECTORY,f"{all_exercises[key]['name']}.html"),"w") # genero il file *nome esercizio*.html
            f.write(txt)
            f.close()

def init_esercizio_grafo_html(key):
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
        yaml_dict[f"context_{all_exercises[key]['name']}"] = {'data':{}}
        #yaml_dict[f"context_{all_exercises[key]['name']}"]['data'] = {}
        for task in PROBLEM[key]['tasks']:
            if task<10:
                yaml_dict[f"context_{all_exercises[key]['name']}"]['data'][f'task0{task}'] = {'feedback':""}
            else:
                yaml_dict[f"context_{all_exercises[key]['name']}"]['data'][f'task{task}'] = {'feedback':""}
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
                yaml_dict[all_exercises[key]['name']][f'task0{task}'] = {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0}
            else:
                yaml_dict[all_exercises[key]['name']][f'task{task}'] = {'punti_sicuri':0,'punti_aggiuntivi_possibili':0,'punti_fuori_portata':0}
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
    for subdir, _, files in os.walk(rootdir):
        for file in files:
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
