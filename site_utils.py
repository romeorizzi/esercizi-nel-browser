import ruamel.yaml
import os

############## INSTANCE FORMAT ##############
#                                           #
# An instance for this problem consists of  # 
# a dictionary with the following keys      #
#                                           #
# [problem]                                 #
# [name]                                    #
# [title]                                   #
# [description]                             #
# [tags]                                    #
# [modes]                                   #
# [instance]                                #
# [tasks]                                   #
#   |___[1]                                 #
#   |    |___[tot_points]                   #
#   |    |                                  #
#   |    |___[pt_formato_OK]                #
#   |    |                                  #
#   |    |___[pt_feasibility_OK]            #
#   |    |                                  #
#   |    |___[task_codename]                #
#   |    |                                  #
#   |    |___[request]                      #
#   |    |                                  #
#   |    |___[init_answ_cell_msg]           #
#   |    |                                  #
#   |    |___[verif]                        #
#   |                                       #
#   |___[2]                                 #
#        |                                  #
#        .                                  #
#        .                                  #
#        .                                  #
#                                           #
#############################################

def find(string,char): # find all char occurencies in string
    return [i for i, l in enumerate(string) if l == char]

def load_yaml(request,values_dict):
    occurencies = find(request,"$")
    idx = 0
    words = []
    while idx < len(occurencies):
        idx_start = occurencies[idx]
        idx_end = occurencies[idx+1]
        word = request[idx_start+1:idx_end]
        words.append(word)
        idx +=2
    final = request
    for word in words:
        try:
            final = final.replace(f"${word}$",word).replace(f"={word}",f"={values_dict['instance'][word]}")
        except:
            pass        
    return final

def get_instance_from_yaml(PATH):
    INSTANCE = {}    
    YAML_FILE = ""
    for file in os.listdir(PATH):
        if file == "settings.yaml":
            return INSTANCE
        if file.endswith(".yaml"):
            YAML_FILE = f"{PATH}/{file}"
    yaml = ruamel.yaml.YAML(typ='safe', pure=True)
    with open(YAML_FILE,'r') as stream:
        try:
            INSTANCE = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)
    tasks = {}
    for i in range(len(INSTANCE["tasks"])):
        tasks[i+1] = INSTANCE["tasks"][i][i+1]
    INSTANCE["tasks"] = tasks
    
    # rectify statements
    problem_values = INSTANCE
    for task in INSTANCE["tasks"]:
        INSTANCE["tasks"][task]["request"] = load_yaml(INSTANCE["tasks"][task]["request"], problem_values)
    
    return INSTANCE
        
def surf_problem(EXAM_PATH):
    PROBLEM = {}
    for folder in os.listdir(EXAM_PATH):
        if os.path.isdir(f"{EXAM_PATH}/{folder}/modo_browser"):
            for file in os.listdir(f"{EXAM_PATH}/{folder}/modo_browser"):
                if file.endswith(".yaml"):
                    PROBLEM[folder] = get_instance_from_yaml(f"{EXAM_PATH}/{folder}/modo_browser")
    return PROBLEM
    
def instance_description(instance):
    instance_descriptor = f""
    for key in instance.keys():
        instance_descriptor += "<b>" + key + ": </b>" + str(instance.get(key)) + "<br>"
    return instance_descriptor
