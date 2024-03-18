# CityNavigator

Shows the discovery of a shortest distance path between two intersections of a real-world map. Can be configured to use maps of different world cities.

## Method

This path finder uses the A* algorithm to find the shortest path between two nodes. The incremental node discovery of the A* algorithm is then stylistically visualised using a pygame display.

## data.py

Modify the place_name variable with the name of any city and run to store the graph of desired city

## Usage

On the UI, click two points on the city map to start the search algorithm

## Visualisation

Lines with brigther shades of red represent edges that were traversed recently. This gradual fading of colour from traversed edges helps visualise the new nodes that are being discovered
