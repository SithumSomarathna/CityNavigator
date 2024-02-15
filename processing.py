import osmnx as ox
import matplotlib.pyplot as plt 

graph = ox.load_graphml("graph.graphml")

graph = ox.graph_to_gdfs(ox.project_graph(graph))

nodes, edges = graph # These are dataframes

nodes = nodes[['x', 'y', 'street_count', 'geometry']]
edges = edges[['osmid', 'length', 'geometry']]

fig, ax = plt.subplots(figsize=(10, 10))
edges.plot(ax=ax, linewidth=1, edgecolor='black')
plt.show()


