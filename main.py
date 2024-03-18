import osmnx as ox
import matplotlib.pyplot as plt 
from shapely.affinity import scale
from shapely.geometry import Point
from shapely.geometry import LineString
import pygame
import math
import heapq
import pandas as pd
from collections import deque

def lanesThickness(lanes):
    if type(lanes) == list: numLanes = max([float(x) for x in lanes])
    elif pd.isnull(lanes): numLanes = 1.0
    else: numLanes = float(lanes)
    return int((numLanes + 1) // 2)

def loadGraph(filename):
    graph = ox.load_graphml(filename)

    graph = ox.graph_to_gdfs(ox.project_graph(graph))

    nodes, edges = graph # These are dataframes

    
    nodes = nodes[['street_count', 'geometry']]
    edges = edges[['osmid', 'length', 'geometry', 'lanes']].sort_values(by='length')
    edges = edges.groupby([edges.index.get_level_values(0), edges.index.get_level_values(1)]).head(1).reset_index(level=2, drop=True)

    return nodes, edges

def calcDistance(linestring: LineString):
    tot = 0
    points = list(linestring.coords)

    for i in range(1, len(points)):
        tot += math.dist(points[i-1], points[i])

    return tot

def transformGraph(nodes, edges, max_width, max_height, padding):
    max_width -= 2 * padding
    max_height -= 2 * padding
    # print(nodes.geometry.x.min(), nodes.geometry.y.min(), nodes.geometry.x.max(), nodes.geometry.y.max())
    min_x = nodes.geometry.x.min()
    min_y = nodes.geometry.y.min()
    max_x = nodes.geometry.x.max()
    max_y = nodes.geometry.y.max()
    dilation = min(max_width / (max_x - min_x), max_height / (max_y - min_y))
    nodes['geometry'] = nodes['geometry'].translate(-min_x, -min_y)
    nodes['geometry'] = nodes['geometry'].apply(lambda coords: scale(coords, xfact=dilation, yfact=-dilation, origin=(0, 0)))
    nodes['geometry'] = nodes['geometry'].translate(padding, dilation * (max_y - min_y) + padding)
    edges['geometry'] = edges['geometry'].translate(-min_x, -min_y)
    edges['geometry'] = edges['geometry'].apply(lambda coords: scale(coords, xfact=dilation, yfact=-dilation, origin=(0, 0)))
    edges['geometry'] = edges['geometry'].translate(padding, dilation * (max_y - min_y) + padding)
    # print(nodes.geometry.x.min(), nodes.geometry.y.min(), nodes.geometry.x.max(), nodes.geometry.y.max())
    edges['distance'] = edges['geometry'].apply(calcDistance)
    edges['thickness'] = edges['lanes'].apply(lanesThickness)
    return dilation * (max_x - min_x) + 2 * padding, dilation * (max_y - min_y) + 2 * padding 

def colourInterpolation(start, end, states, cur_state):
    return (start[0] * cur_state / states + end[0] * (states-cur_state) / states, start[1] * cur_state / states + end[1] * (states-cur_state) / states, start[2] * cur_state / states + end[2] * (states-cur_state) / states)

nodes, edges = loadGraph("graph.graphml")
width, height = transformGraph(nodes, edges, 1400, 800, 50)

start, dest = None, None

visited = set()
parent = dict()
pq = []

pygame.init()

c_white = (255,255,255)
c_grey = (100, 100, 100)

c_lightred = (252, 88, 88)
c_transparent = (0, 0, 0)

c_start = (255,0,0)
c_end = (100, 0, 0)
pre_states = 9
wait_iterations = 10

screen = pygame.display.set_mode((width, height), pygame.SRCALPHA)

node_selection = pygame.Surface((width, height), pygame.SRCALPHA)
node_selection.fill(c_transparent)
node_selection.set_colorkey(c_transparent)

main_path = pygame.Surface((width, height), pygame.SRCALPHA)
main_path.fill(c_transparent)
main_path.set_colorkey(c_transparent)

fade_paths = []
fade_edges = []
for i in range(pre_states):
    path = pygame.Surface((width, height), pygame.SRCALPHA)
    path.fill(c_transparent)
    path.set_colorkey(c_transparent)
    fade_paths.append(path)

    fade_edges.append(deque())
    for j in range(wait_iterations):
        fade_edges[i].append((None, None))



map = pygame.Surface((width, height))
for i, edge in edges.iterrows():
    pygame.draw.lines(map, c_grey, False, list(edge['geometry'].coords), edge['thickness'])
screen.blit(map, (0, 0))

running = True
selected = False
closest_point = None
phase = 1

while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if phase < 3:
            if event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                closest_point = nodes.loc[nodes.distance(Point(mouse_x, mouse_y)).idxmin()]
                node_selection.fill(c_transparent)
                if (start is None or closest_point.name != start) and math.dist(event.pos, (closest_point.geometry.x, closest_point.geometry.y)) <= 30:
                    selected = True
                    pygame.draw.circle(node_selection, c_start, (closest_point.geometry.x, closest_point.geometry.y), 4)
                else: selected = False
                screen.blit(map, (0, 0))
                screen.blit(main_path, (0, 0))
                screen.blit(node_selection, (0, 0))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if selected:
                    if phase == 1:
                        start = closest_point.name
                        pygame.draw.circle(main_path, c_start, (closest_point.geometry.x, closest_point.geometry.y), 4)
                        node_selection.fill(c_transparent)
                        screen.blit(main_path, (0, 0))
                        selected = False
                        phase = 2
                    elif phase == 2:
                        dest = closest_point.name
                        pygame.draw.circle(main_path, c_start, (closest_point.geometry.x, closest_point.geometry.y), 4)
                        node_selection.fill(c_transparent)
                        screen.blit(main_path, (0, 0))
                        heapq.heappush(pq, (nodes.loc[start].geometry.distance(nodes.loc[dest].geometry), (start, None, 0)))
                        phase = 3
    
    if phase == 3:
        
        if len(pq) == 0: 
            print("No path available")
            break
        node, par, dist = heapq.heappop(pq)[1]
        if node in visited: continue
        
        visited.add(node)
        if par is not None: 
            fade_edges[pre_states-1].append((par, node))
            par, node = fade_edges[0].popleft()
            if par is not None and node is not None: pygame.draw.lines(main_path, c_end, False, list(edges.loc[(par, node)]['geometry'].coords), edges.loc[(par, node)]['thickness'] * 3)
            for i in range(pre_states-1):
                fade_edges[i].append(fade_edges[i+1].popleft())
            for i in range(pre_states):
                fade_paths[i].fill(c_transparent)
                for edge in fade_edges[i]:
                    par, node = edge
                    if par is not None and node is not None: pygame.draw.lines(fade_paths[i], colourInterpolation(c_start, c_end, pre_states, i+1), False, list(edges.loc[(par, node)]['geometry'].coords), edges.loc[(par, node)]['thickness'] * 3)
        
        screen.blit(map, (0, 0))
        screen.blit(main_path, (0, 0))
        for i in range(pre_states-1, -1, -1):
            screen.blit(fade_paths[i], (0, 0))
        parent[node] = par
        if node == dest:
            for path in fade_paths: path.fill(c_transparent)
            main_path.fill(c_transparent)
            n = dest
            while n != start:
                p = parent[n]
                pygame.draw.lines(main_path, c_start, False, list(edges.loc[(p, n)]['geometry'].coords), edges.loc[(p, n)]['thickness'] * 3)                
                n = p
            screen.blit(map, (0, 0))
            screen.blit(main_path, (0, 0))
            phase = 4
            continue
        try: edges.loc[node]
        except: continue
        else:
            for i, edge in edges.loc[node].iterrows():
                # print(edge.name)
                if edge.name not in visited:
                    heapq.heappush(pq, (dist + edge.distance + nodes.loc[edge.name].geometry.distance(nodes.loc[dest].geometry), (edge.name, node, dist + edge.distance)))

    pygame.display.update()
pygame.quit()


