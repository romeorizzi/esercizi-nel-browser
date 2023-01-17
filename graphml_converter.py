import sys 
from xml.dom import minidom

sys.setrecursionlimit(10**9)
xmldoc = minidom.parse('graphml/esempio_esame_1_graph.graphml')

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

def node_arrow():
     archi_grafo_arrow = []
     arrow_list = xmldoc.getElementsByTagName('y:Arrows')

     for count in range(numero_archi):
          if arrow_list[count].attributes['target'].value == 'none':
               archi_grafo_arrow.append([edge_list[count].attributes['source'].value, edge_list[count].attributes['target'].value, 'line'])

          elif arrow_list[count].attributes['target'].value == 'standard':
               archi_grafo_arrow.append([edge_list[count].attributes['source'].value, edge_list[count].attributes['target'].value, 'arrow'])
     return archi_grafo_arrow

def edge_string():
     edge_to_string = '['
     
     for count in range(numero_archi):
          edge_to_string += '('
          edge_to_string += edge_list[count].attributes['source'].value + ',' + edge_list[count].attributes['target'].value
          edge_to_string += ')'
     return edge_to_string + ']'
