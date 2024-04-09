import networkx as nx
import matplotlib.pyplot as plt
from utils import graph_modeling as modeling

def create_graphml(edges, graphml_name):
    G = nx.Graph()
    edges = eval(edges)
    for edge in edges:
        x,y = list(edge[0])
        G.add_edge(x, y, weight=edge[1])

    #lay_type = ['twopi', 'osage', 'patchwork', 'fdp', 'circo', 'neato', 'dot', 'sfdp']
    lay_type = []
    pos_type = []
    for layout in  ['twopi', 'osage', 'patchwork', 'fdp', 'circo', 'neato', 'dot', 'sfdp']:
        try:
            pos_type.append(nx.nx_agraph.graphviz_layout(G, prog=layout))
            lay_type.append(layout)
        except Exception:
            pass

    a = 331
    for i in range(len(pos_type)):
        ax = plt.subplot(a)
        ax.set_title(str(i))
        nx.draw_networkx(G, pos=pos_type[i])
        a += 1

    with plt.ion():
        plt.show()

    a = input('Quale layout si preferisce (aggiungre M per modificare tale layout): ')
    if a != '':
        if a[-1] == 'M':
            pos = modeling.main(pos_type[int(a[:-1])], edges)
        else:
            pos = pos_type[int(a)]
    else:
        pos = pos_type[-1]

    max_x, max_y = 0, 0
    for node in pos:
        max_x = max(pos[node][0], max_x)
        max_y = max(pos[node][1], max_y)
    x_factor = 9500/max_x
    y_factor = 1900/max_y

    out = open(graphml_name, 'w')
    out.write("""<?xml version="1.0" encoding='utf-8'?>
   <graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:java="http://www.yworks.com/xml/yfiles-common/1.0/java" xmlns:sys="http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0" xmlns:x="http://www.yworks.com/xml/yfiles-common/markup/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:y="http://www.yworks.com/xml/graphml" xmlns:yed="http://www.yworks.com/xml/yed/3" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
        <key id="data_node" for="node" yfiles.type="nodegraphics"/>
        <key id="data_edge" for="edge" yfiles.type="edgegraphics"/>
        <graph edgedefault="directed">""")

    for node in pos:
        out.write(f'''<node id="{node}">
                <data key="data_node">
                    <y:ShapeNode>
                        <y:Geometry height="35" width="35" x="{int(pos[node][0]*x_factor)}" y="{int(pos[node][1]*y_factor)}"/>
                        <y:Fill color="#ff0000" transparent="false"/>
                        <y:BorderStyle hasColor="false" type="line" width="1.0"/>
                        <y:NodeLabel fontFamily="Dialog" fontSize="20" underlinedText="false" fontStyle="plain" target="label">{node}</y:NodeLabel>
                        <y:NodeLabel tag=" "></y:NodeLabel>
                        <y:Shape type="ellipse"/>
                    </y:ShapeNode>
                </data>
            </node>''')

    for x,y in G.edges:
        weight = '\"\"'
        if 'weight' in G[x][y]:
            weight =G[x][y]['weight']
        out.write(f'''<edge id="{x}_{y}" source="{x}" target="{y}">
                <data key="data_edge">
                    <y:ArcEdge>
                        <y:Arrows source="none" target="standard" type=""/>
                        <y:LineStyle color="#000000" type="line" width="1"/>
                        <y:EdgeLabel>{weight}</y:EdgeLabel>
                    </y:ArcEdge>
                </data>
            </edge>''')

    out.write('</graph></graphml>')
    out.close()

if __name__ == '__main__':
    create_graphml('[{0,1}, 3]', 'grafo_10_graph.graphml')

