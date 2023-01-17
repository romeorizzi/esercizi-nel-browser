# RTal python library for Jupyter Notebook usage
# Requirements: websocket, json

# to install websocket inside a Jupyter notebook use:
# import sys
# !{sys.executable} -m pip install websocket-client

import os
import sys
from IPython.display import display, HTML
import json
import ruamel.yaml
import pyrtal
""" How to use pyrtal:
TAL_Client = pyrtal.RTAL() # with the URL of the server as argument (default: local, i.e. ws://127.0.0.1:8008/)
# list command:
TAL_Client.list() # yields a json/yaml description of the whole tree in the meta.yaml file of the problem (where the branches not of pertinence for the rtal/rtald protocol are dropped)
# get command:
public_archive_name,public_archive_content = TAL_Client.get('sum')
with open(public_archive_name,'wb') as fout:
     fout.write(public_archive_content)
# connect command:
oneConnection = TAL_Client.connect('sum','free_sum')
## type(oneConnection) is <class 'builtins.RTALConn'> and offers 3 methods:
##    oneConnection.close()   oneConnection.read()   oneConnection.write()
## Esempio d'uso di read/write:
oneConnection.read()
b"# Servir\xc3\xb2: problem=sum, service=free_sum\n#  con argomenti: num_questions=10, numbers=twodigits, obj=any, META_TTY=0 (i.e., False), META_TTY=0 (i.e., False), lang=it.\n# Le frasi in italiano utilizzate in questa chiamata del servizio free_sum provengono dal file 'free_sum_feedbackBook.None.yaml' collocato nella cartella 'lang' del problema sum.\n29\n"
(to transform this bytes objet into a string use its method .decode("utf-8"))
oneConnection.write('0 29\n'.encode())
oneConnection.read()
b'# OK! infatti, 0+29=29.\n47\n'
## Argomenti di connect:
oneConnection = TAL_Client.connect('sum','free_sum', args:Dict, tty:bool, token:str = None, files:Dict)
### scambio di files con servizio TALight:
#### gestione files in ingresso al servizio:
files={'filehandler1':open(filename,'rb').read()}
#### gestione files in uscita dal servizio:
close() --> Dict con chiavi i nomi dei file e contenuto i valori
esempio ottenere e salvare tutti i files prodotti da una chiamata al servizio (non i files di log che vengono tenuti sul server):
for filename,filecontent in oneConnection.close().items():
    with open(filename,'wb') as fout:
         fout.write(filecontent)
"""

RTAL_PRIVATE_ACCESS_TOKEN="%(RTAL_PRIVATE_ACCESS_TOKEN)s"
PATH_EDITABLE_SETTINGS = os.getcwd()
while os.path.isdir(PATH_EDITABLE_SETTINGS):
    if os.path.isfile(os.path.join(PATH_EDITABLE_SETTINGS,'settings','settings.yaml')):
        break
    PATH_EDITABLE_SETTINGS = os.path.join(PATH_EDITABLE_SETTINGS,'..')
SETTINGS_FILE_FULLNAME=os.path.join(PATH_EDITABLE_SETTINGS,'settings','settings.yaml') 
with open(SETTINGS_FILE_FULLNAME,"r") as stream:
     settings = ruamel.yaml.safe_load(stream)


def info():
    print("These are your current dynamic settings, as set in the file",end="\n   ")
    print(SETTINGS_FILE_FULLNAME)
    for k,v in settings.items():
        print(f"{k}: {v}")
    hint = """
To see all the info you can get enter and run this piece of code:
   vars = [k for k in locals().keys() if k[0] != '_']
   vars.sort()
   print('\\n'.join(iter(vars)))"""
    print(hint)

def printif(category_of_interest,msg, **kwargs):
    if category_of_interest in settings['RTAL_INTERFACE_VERBOSITY']:
        print(msg, **kwargs)


def rtal_list(rtal_URL=None):
    """returns the whole json/yaml tree of all problems served by the TAL server at rtal_URL
    Parameters:
    - rtal_URL: rtal server address
    Call examples:
       1. rtal_list("wss://ta.di.univr.it/tal")
       2. rtal_list("ws://127.0.0.1:8008") # explicit call to local server
       3. rtal_list() # implicit call to local server
    """
    try:
        if rtal_URL==None:
            TAL_Client = pyrtal.RTAL() # implicitly goes for the local server
        else:
            TAL_Client = pyrtal.RTAL(rtal_URL)
    except Exception as e:
        printif('TALight_protocol_signals_problem',e)
        printif('TALight_protocol_signals_problem',f'Could not connect to the (active?) TAL server {rtal_URL}{" (local server supposed to be exposed at ws://127.0.0.1:8008/)" if rtal_URL is None else ""}')
        return {}
    try:
        json_dict = TAL_Client.list()
    except Exception as e:
        printif('TALight_protocol_signals_problem',e)
        printif('TALight_protocol_signals_problem',f'Troubles when running the list command on the active TAL server {rtal_URL}')
        return {}
    return json_dict

def check_rtal_deploys_problem_service(rtal_URL,problem,service=None):
    """checks that the TAL server at given rtal_URL serves a given problem/server
    Parameters:
    - rtal_URL: rtal server address
    Call examples:
       1. rtal_list("wss://ta.di.univr.it/tal","sum")
       2. rtal_list("ws://127.0.0.1:8008","sum")
    """
    json_dict = rtal_list(rtal_URL=None)
    if not problem in json_dict:
        printif('TALight_protocol_signals_problem',f'Problem `{problem}` not currently deployed by the active TAL server {rtal_URL}')
        return False
    if not service is None and not service in json_dict['services'][service]:
        printif('TALight_protocol_signals_problem',f'Service `{service}` not currently deployed for problem `{problem}` by the active TAL server {rtal_URL}')
        return False
    return True

def rtal_connect(rtal_URL, problem, service, rtalargs_dict, rtaltoken=None,load_files={},output_files_local_folder=None):
    """sends a TALight connect request
    Parameters:
    - rtal_URL: rtal server address
    - problem: name of the TALight problem offering the solution checking and oracle services
    - service: name of the checking TALight service of interest
    - rtalargs_dict: dictionary with the arguments to be sent to the TALight service
    - output_files_local_folder (optional): the name of the local folder where TALight could store files like e.g. a certificate for a good submission received 
    - rtaltoken (optional): the student access token so that logs are stored on the server or even just to access the service"""
        
    def my_repr(obj):
        r = repr(obj)
        if r[0] == "'":
            r=r[1:]
        if r[-1] == "'":
            r=r[:-1]
        return r

    rtalargs={}
    for key in rtalargs_dict:
        rtalargs[key] = my_repr(rtalargs_dict[key])
    try:
        if rtal_URL==None:
            TAL_Client = pyrtal.RTAL() # implicitly goes for the local server
        else:
            TAL_Client = pyrtal.RTAL(rtal_URL)
    except Exception as e:
        printif('TALight_protocol_signals_problem',e)
        printif('TALight_protocol_signals_problem',f'Could not connect to the (active?) TAL server {rtal_URL}{" (local server supposed to be exposed at ws://127.0.0.1:8008/)" if rtal_URL is None else ""}')
        return    
    try: 
        oneConnection = TAL_Client.connect(problem,service,rtalargs,tty=False,token=rtaltoken,files=load_files)
    except Exception as e: 
        printif('TALight_protocol_signals_problem', e, end='') 
        printif('TALight_protocol_signals_problem', f' on TAL server {rtal_URL}{" (local server, as assumed to be exposed at ws://127.0.0.1:8008/)" if rtal_URL is None or rtal_URL=="ws://127.0.0.1:8008/" else ""}')
        return
    try:
        TAL_service_printout = oneConnection.read().decode("utf-8") 
    except Exception as e:
        printif('TALight_protocol_signals_problem',e)
        printif('TALight_protocol_signals_problem',f'Got problems when reading the output from service `{service}` of problem `{problem}` at TAL server {rtal_URL}')
        return
    # OUTPUT FILES DOWNLOAD IF ANY AND NO IMPEDEMENTS:
    output_files = None
    try:
        output_files = oneConnection.close()
    except Exception as e:
        printif('TALight_protocol_signals_problem',e)
        printif('TALight_protocol_signals_problem',f'Got problems when closing the connection to service `{service}` of problem `{problem}` at TAL server {rtal_URL}. No certificate could be stored in local for extra safety (double checkability).')
    if output_files != None and len(output_files) > 0:
        if output_files_local_folder is None:
            printif('TALight_protocol_signals_problem',f'The service has returned some certificate files but no local folder for storing them has been specified.')
        absolute_path_download_folder = os.path.join(os.getcwd(),output_files_local_folder)
        if not os.path.exists(absolute_path_download_folder):
            try:
                os.makedirs(absolute_path_download_folder)
            except Exception as e:
                printif('TALight_protocol_signals_problem',e)
                printif('TALight_protocol_signals_problem',f'Permissions issues when trying to create the folder {absolute_path_download_folder}')
        if os.path.exists(absolute_path_download_folder):
            for filename,filecontent in output_files:
                try:
                    with open(os.path.join(os.getcwd(),output_files_local_folder,filename),'wb') as fout:
                        fout.write(filecontent)
                except Exception as e:
                    printif('TALight_protocol_signals_problem',e)
                    printif('TALight_protocol_signals_problem',f'File {filename} could not be written in local as a certificate for extra safety (double checkability). Permissions issues with folder {absolute_path_download_folder}')
    # RETURNING THE DIRECT OUTPUT FROM THE SERVER:
    #TAL_service_printout = TAL_service_printout.decode('UTF-8')
    printif('TALight_protocol','TALight service printout:' + TAL_service_printout)
    feedback_dict={'feedback_string':TAL_service_printout}
    if 'as_yaml_with_points' in rtalargs and rtalargs['as_yaml_with_points'] == '1':
        try:
            feedback_dict=eval(TAL_service_printout)
        except:
            pass
    if 'color_implementation' in rtalargs and rtalargs['color_implementation'] == 'html':
        feedback_dict['feedback_string']=HTML(feedback_dict['feedback_string'])
    return feedback_dict
        


# Test TALight list command (check which problems are currently served. The purpouse is just to check if you reach the server):

if settings['DEBUG_RTAL_AT_SET_UP']:
    for rtal_URL_name in settings['RTAL_URLS']:
        URL = settings[rtal_URL_name]
        print("\n"f"List of TAL problems served on server {rtal_URL_name} [{URL}]:")
        json_dict = rtal_list(URL)
        for key in json_dict: 
            print(key) 

# Example on how to lay down the data to prepare for an rtal_connect call for a specific problem when testing its correct interface as for the TALight server:

task_dict={'task': 1, 'pt_tot': 40, 'pt_formato_OK': 0, 'pt_feasibility_OK': 1, 'pt_consistency_OK': 0, 'with_positive_enforcement':'1', 'with_notes':'1', 'as_yaml_with_points':'1','color_implementation':'html','with_output_files':'0'}
input_data_assigned={'labels': ['A', 'B', 'C', 'D', 'E'], 'costs': [2, 3, 4, 5, 6], 'vals': [13, 17, 19, 30, 101], 'Knapsack_Capacity': 5, 'forced_out': [], 'forced_in': [], 'partialDPtable': []}
alias_dict={'opt_sol69':'opt_sol','opt_val69':'opt_val'}
answer_dict={'opt_sol69':['A','B'],'opt_val69':30}
rtalargs_dict = task_dict
rtalargs_dict['input_data_assigned'] = input_data_assigned
rtalargs_dict['alias_dict'] = alias_dict
rtalargs_dict['answer_dict'] = answer_dict

def monitor_what_submitted_to_rtald(problem_name, rtalargs_dict):
    if settings['MONITOR_CALLS_TO_RTAL_CHECKERS']:
        command_line = f"rtal connect {problem_name} check  "
        for key in rtalargs_dict:
            command_line += f'-a {key}="{rtalargs_dict[key]}"  '
        print("\n\n\n" + "*-------"*5)
        print("SICCOME PARLIAMO DIRETTAMENTE AD RTALD DOBBIAMO PASSARGLI LA LISTA COMPLETA DEGLI ARGOMENTI (IL DEFAULTING NON RISOLVE). QUESTO MESSAGGIO SERVE PER TENERTI CONSAPEVOLE DI COSA ESCE E CONSENTIRTI DI REPLICARLO AGEVOLMENTE A RIGA DI COMANDO PER TESTARLO IN CASO DI PROBLEMI\n\n" f"Gestire rtalargs_dict={rtalargs_dict}" "\n\ncorrisponde alla riga seguente di comando:\n   " f"$ {command_line}")
        print("*-------"*5 + "*\n\n\n")


monitor_what_submitted_to_rtald("RO_knapsack", rtalargs_dict)

# Example call with TOKEN to an rtal problem service meant to play as a checker:
if settings['DEBUG_RTAL_AT_SET_UP']:
    for rtal_URL_name in settings['RTAL_URLS']:
        rtal_URL = settings[rtal_URL_name]
        print("\n"f"Now calling server {rtal_URL_name} [{rtal_URL}]:")
        feedback_dict = rtal_connect(rtal_URL, 'RO_knapsack', 'check', rtalargs_dict=rtalargs_dict, output_files_local_folder='output_files_TALight', rtaltoken=RTAL_PRIVATE_ACCESS_TOKEN)
        print("\n"f"Feedback from server {rtal_URL_name} [{rtal_URL}]:")
        if feedback_dict != None:
            display(feedback_dict['feedback_string'])
        else:
            print("\n"f"The Feedback received from the server {rtal_URL_name} is EMPTY")
            

# Example call without TOKEN to an rtal problem service meant to play as a checker:
if settings['DEBUG_RTAL_AT_SET_UP']:
    for rtal_URL_name in settings['RTAL_URLS']:
        rtal_URL = settings[rtal_URL_name]
        feedback_dict = rtal_connect(rtal_URL, 'RO_knapsack', 'check', rtalargs_dict=rtalargs_dict, output_files_local_folder='output_files_TALight', rtaltoken=None)
        print(f"Feedback from server {rtal_URL_name} [{rtal_URL}]:")
        if feedback_dict != None:
            display(feedback_dict['feedback_string'])
        else:
            print("The Feedback received from the server is EMPTY")


# Example call with to an rtal problem checker service with files saved in local:
if settings['DEBUG_RTAL_AT_SET_UP']:
    print("files saved in local: -NOT YET IMPLEMENTED-")

# Example call to an rtal problem service meant to play as an oracle:
if settings['DEBUG_RTAL_AT_SET_UP']:
    print("files saved in local: -NOT YET COME INTO THE GAME-")

