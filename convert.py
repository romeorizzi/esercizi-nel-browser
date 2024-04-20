import os
import re
import yaml as ya
from utils import graph
from utils.RO_utils import *

class Default(dict):
    def __missing__(self, key):
        return key.join('{}')

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def analyze_string(string, instance, task, str_instance):
    _task = Default({'task' : task})
    #_err = Default(task)
    _instance = Default(instance)
    new_str = str(string)

    try:
        new_str = new_str.format_map(_task)
    except:
        pass
    try:
        new_str = new_str.format_map(_instance)
    except:
        pass
    #try:
    #    new_str = new_str.format_map(_err)
    #except:
    #    pass

    missing = set()
    found = set(re.findall(r'{(.+?)}', new_str, flags=re.M))
    if len(found) > 0:
        task_found = re.findall(r'task\["(.+?)"\]', str(found), flags=re.M)
        for key in task_found:
            task_key = f'task["{key}"]'
            value = str(task[key])
            old_str = new_str
            new_str = new_str.replace('{'+task_key+'}', value)
            if old_str == new_str:
                for found_key in [x for x in found if 'task["' in x]:
                    new_str = new_str.replace(task_key, value)
                    found.remove(found_key)
                    found.add(found_key.replace(task_key, value))
            else:
                found.remove(task_key)

        for code in found:
            try:
                result = {}
                exec(f"{str_instance}output_of_code=str({code})", globals(), result)
                new_str = new_str.replace('{'+code+'}', result['output_of_code'])
            except:
                missing.add(code)
        if len(missing):
            print(f"{bcolors.WARNING}\tMissing: {missing}{bcolors.ENDC}")
    return(new_str.replace('*^*','{').replace('*&*','}'), missing)

def analyze_generic(request, instance, str_instance, task):
    if isinstance(request, str):
        return analyze_string(request, instance, task, str_instance)[0]
    elif isinstance(request, dict):
        for field in request:
            request[field] = analyze_string(request[field], instance, task, str_instance)[0]
    return request

def analyze_general_description_before_task(gdbf, instance, str_instance, task):
    if "rendition" in gdbf and gdbf["rendition"] == "from_code":
        result = analyze_string(gdbf["content"], instance, task, str_instance)
        try:
            result_ = {}
            exec(f"output={result[0]}", globals(), result_)
            gdbf["content"] = result_['output']
        except:
            print(f"{bcolors.WARNING}\t{result[0]}{bcolors.ENDC}")
            gdbf["content"] = result[0]
    else:
        for field in gdbf:
            result = analyze_string(gdbf[field], instance, task, str_instance)
            gdbf[field] = result[0]
    return gdbf

def analyze_task(task, instance, str_instance, task_number, pure_instance):
    instance['task_number'] = task_number
    str_instance += f'task_number={task_number};'
    #task_dict = f"'task_number':{task_number},"
    task_dict = '{'
    for key in task:
        if key == 'answ_form':
            if isinstance(task['answ_form'], list):
                for i in range(len(task['answ_form'])):
                    task[key][i] = analyze_generic(task[key][i], instance, str_instance, task)
            else:
                task[key] = analyze_generic(task[key], instance, str_instance, task)
        elif key == 'general_description_before_task':
            gdbf = task['general_description_before_task']
            if isinstance(gdbf, list):
                gdbf_str = ''
                for content in gdbf:
                    gdbf_str += analyze_general_description_before_task(content, instance, str_instance, task)['content']
                task['general_description_before_task'] = gdbf_str
            else:
                task['general_description_before_task'] = analyze_general_description_before_task(gdbf, instance, str_instance, task)['content']
        elif key == 'verif':
            if not isinstance(task['verif'], dict):
                task['verif'] = analyze_generic(task['verif'], instance, str_instance, task)
        elif key == 'request':
            if isinstance(task[key], dict):
                task[key] = analyze_generic(task[key], instance, str_instance, task)['content']
            else:
                task[key] = analyze_generic(task[key], instance, str_instance, task)
        else:
            task[key] = analyze_generic(task[key], instance, str_instance, task)

        if key not in ('verif', 'goals', 'general_description_before_task','init_answ_cell_msg','request','answ_form'):
            task_dict += f"""'{key}':{repr(task[key])},"""

    if 'verif' in task and isinstance(task['verif'], dict):
        #input_data_assigned = '{'
        for obj in pure_instance:
            task_dict += f"""'{obj}':{repr(pure_instance[obj])},"""
            #input_data_assigned = f"""'{obj}':{repr(pure_instance[obj])},"""
        task_dict += '}'

        answer_dict = '{'
        goals = task['goals']
        if isinstance(goals, list):
            for goal in goals:
                answer_dict += f"'{goal}':({goal}{task_number},'{goal}{task_number}'),"
        else:
            answer_dict = f"'{goals}':({goals}{task_number},'{goals}{task_number}')"
        answer_dict += '}'

        task['verif'] = (f"'verify_submission(TALight_problem_name='{task['verif']['TALight_problem_name']}',checkers={task['verif']['checkers']},task_dict={task_dict},input_data_assigned={task_dict},long_answer_dict={answer_dict})'")
    return task

def analyze_instance(yaml_dict):
    instance = yaml_dict['instance'].copy()
    pure_instance = {}
    str_instance = ''
    for key in instance:
        value = str(instance[key])
        code = f"{key}={value};"
        try:
            exec(code)
            str_instance += code
        except:
            str_instance += f"{key}='{value}';"
        instance[key] = value.replace('{','*^*').replace('}','*&*')
        pure_instance[key] = value

    yaml_new = yaml_dict.copy()
    n = 1
    for i in range(len(yaml_dict['tasks'])):
        yaml_new['tasks'][i][n] = analyze_task(yaml_dict['tasks'][i][n], instance, str_instance, n, pure_instance)
        yaml_new['tasks'][i][n]['init_answ_cell_msg_automatic'] = ''
        if 'init_answ_cell_msg' in yaml_new['tasks'][i][n]:
            yaml_new['tasks'][i][n]['init_answ_cell_msg_automatic'] = yaml_new['tasks'][i][n]['init_answ_cell_msg']
        n += 1

    if 'general_description_to_conclude' in yaml_new and 'content' in yaml_new['general_description_to_conclude']:
        yaml_new['general_description_to_conclude'] = yaml_new['general_description_to_conclude']['content']
    yaml_new['graphic_instance_descriptor'] = ''
    if 'edges' in yaml_new['instance']:
        graph.create_graphml(yaml_new['instance']['edges'], yaml_new['graphml'])
    return yaml_new

def start():
    dirs = []
    for folder in next(os.walk('simulazione_esame'))[1]:
        if 'esercizio_' in folder:
            dirs.append(f'simulazione_esame/{folder}')

    for path in dirs:
        #aliases = {}
        #try:
        #    with open(path+name+'/alias.conf', 'r') as alias_file:
        #        for line in alias_file:
        #            sline = line.split(':')
        #            aliases[sline[0]]=':'.join(sline[1:]).replace('\n','')
        #        alias_file.close()
        #except Exception as e :
        #    print("Alias file error")
        #    pass
        #path_1 = f'{path}{name}'
        for folder in next(os.walk(path))[1]:
            try:
                path_ = f'{path}/{folder}/'
                for file in next(os.walk(path_))[2]:
                    if file[-9:] in '.instance':
                        path_instance = f"{path_}{file}"
                        with open(path_instance, 'r') as file:
                            instance = ya.safe_load(file)
                            print(f"{bcolors.BOLD}{bcolors.HEADER}{path_instance}{bcolors.ENDC}")
                            new_instance = analyze_instance(instance)
                            with open(path_instance[:-9]+'.yaml', 'w') as file:
                                ya.dump(new_instance, file)
            except FileNotFoundError:
                #print(".instance file error")
                pass

if __name__ == '__main__':
    start()
