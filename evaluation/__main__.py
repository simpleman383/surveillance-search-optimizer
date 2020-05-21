from primitives.graph import GraphGenerator, Graph
from primitives.utils import find_paths




graph = GraphGenerator.create(6)
graph.print()

paths = find_paths(graph, 0, 3)
print(paths)
