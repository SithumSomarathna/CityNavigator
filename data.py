import osmnx as ox

# place_name = "Manhattan, New York City, New York, USA"
# place_name = "Colombo, Sri Lanka"
place_name = "City of Westminster, Greater London, UK"

graph = ox.graph_from_place(place_name, network_type='drive')

ox.save_graphml(graph, filepath='graph.graphml')

ox.plot_graph(ox.project_graph(graph))
