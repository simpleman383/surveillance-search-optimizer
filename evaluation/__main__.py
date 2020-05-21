from primitives.graph import GraphGenerator, Graph
from primitives.metrics.paths import get_shortest_path


graph = GraphGenerator.create(4)
graph.print()

path, d = get_shortest_path(graph, 0, 3)
print([ node.id for node in path ])
print("Minimal distance is", d)



