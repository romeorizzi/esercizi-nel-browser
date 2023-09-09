import sys 
from xml.dom import minidom
import ruamel.yaml

sys.setrecursionlimit(10**9)
yaml = ruamel.yaml.YAML()

final_graph = str
with open('simulazione_esame/esercizio_3/modo_browser/graphs_mst.yaml') as fp:
     data = yaml.load(fp)
     final_graph = data['graphml']

xmldoc = minidom.parse(final_graph)

edge_list = xmldoc.getElementsByTagName('edge')
node_list = xmldoc.getElementsByTagName('node')
numero_nodi = len(node_list)
numero_archi = len(edge_list)

def node_edges():
     nodi_grafo = []
     for node_id in range(numero_nodi): 
          nodi_grafo.append(node_list[node_id].attributes['id'].value)
     return nodi_grafo 

def numero_node_edges():
     numero_nodi = len(node_list)
     numero_archi = len(edge_list)
     return numero_nodi, numero_archi

def node_position():
     coordinate_nodi = []
     node_x_y = xmldoc.getElementsByTagName('y:Geometry')

     for node_id in range(numero_nodi):
          x = node_x_y[node_id].attributes['x'].value
          y = node_x_y[node_id].attributes['y'].value
          coordinate_nodi.append([int(int(float(x))/13), int(int(float(y))/8)])         
     return coordinate_nodi

def node_tag():
    node_tag = []
    tmp_node_tag = xmldoc.getElementsByTagName('y:NodeLabel')

    for node_id in range(len(tmp_node_tag)):
        if tmp_node_tag[node_id].getAttribute('tag') != "":
            node_tag.append(tmp_node_tag[node_id].getAttribute('tag'))

    # print(node_tag)

    return node_tag

def node_color():
    colori_nodi = []
    node_color = xmldoc.getElementsByTagName('y:Fill')

    for node_id in range(numero_nodi):
        color = node_color[node_id].attributes['color'].value
        colori_nodi.append(color)
    return colori_nodi

def node_arrow():
     archi_grafo_arrow = []
     arrow_list = xmldoc.getElementsByTagName('y:Arrows')
     arch_weight = xmldoc.getElementsByTagName('y:EdgeLabel')

     for count in range(numero_archi):
         weight = arch_weight[count].firstChild.data
         if weight == " ":
             weight = -13234214325

        #  if arrow_list[count].attributes['type'].value == 'curve':
        #      archi_grafo_arrow.append(
        #          [edge_list[count].attributes['source'].value, edge_list[count].attributes['target'].value, 'curve', weight, arrow_list[count].attributes['type'].value])
        # else:
         if arrow_list[count].attributes['target'].value == 'none' and arrow_list[count].attributes['source'].value == 'none':
             archi_grafo_arrow.append(
                 [edge_list[count].attributes['source'].value, edge_list[count].attributes['target'].value, 'line', weight, arrow_list[count].attributes['type'].value])

         elif arrow_list[count].attributes['target'].value == 'standard' and arrow_list[count].attributes['source'].value == 'none':
             archi_grafo_arrow.append(
                 [edge_list[count].attributes['source'].value, edge_list[count].attributes['target'].value, 'arrow', weight, arrow_list[count].attributes['type'].value])

         elif arrow_list[count].attributes['target'].value == 'standard' and arrow_list[count].attributes['source'].value == 'standard':
             archi_grafo_arrow.append(
                 [edge_list[count].attributes['source'].value, edge_list[count].attributes['target'].value, 'bidirectional', weight, arrow_list[count].attributes['type'].value])
     return archi_grafo_arrow

def edge_string():
     edge_to_string = '['
     
     for count in range(numero_archi):
          edge_to_string += '('
          edge_to_string += edge_list[count].attributes['source'].value + ',' + edge_list[count].attributes['target'].value
          edge_to_string += ')'
     return edge_to_string + ']'
