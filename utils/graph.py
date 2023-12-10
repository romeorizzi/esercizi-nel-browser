import networkx as nx
import matplotlib.pyplot as plt

def create_graphml(edges, graphml_name):
    G = nx.Graph()
    edges = eval(edges)
    for edge in edges:
        x,y = list(edge[0])
        G.add_edge(x, y, weight=edge[1])

    #for i in ['twopi', 'osage', 'patchwork', 'fdp', 'circo', 'neato','dot', 'sfdp']:
    #    pos = nx.nx_agraph.graphviz_layout(G, prog=i)
    #    nx.draw_networkx(G, pos=pos) #nx.drawing.nx_agraph.graphviz_layout(G))
    #    plt.show()

    pos = nx.nx_agraph.graphviz_layout(G, prog='sfdp')
    #nx.write_graphml_lxml(G, 'aa.xml')

    max_x, max_y = 0, 0
    for node in pos:
        max_x = max(pos[node][0], max_x)
        max_y = max(pos[node][1], max_y)
    x_factor = 9500/max_x
    y_factor = 1500/max_y

    out = open(graphml_name, 'w')
    out.write("""<?xml version="1.0" encoding='utf-8'?>
   <graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:java="http://www.yworks.com/xml/yfiles-common/1.0/java" xmlns:sys="http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0" xmlns:x="http://www.yworks.com/xml/yfiles-common/markup/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:y="http://www.yworks.com/xml/graphml" xmlns:yed="http://www.yworks.com/xml/yed/3" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
        <key id="data_node" for="node" yfiles.type="nodegraphics"/>
        <key id="data_edge" for="edge" yfiles.type="edgegraphics"/>
        <graph edgedefault="directed">
""")


    for node in pos:
        #print(pos[node])
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
    create_graphml([], 'grafo_10_graph.graphml')
#nx.draw_networkx(G, pos=pos)

#plt.show()

