import random
import pickle
from enum import IntFlag

class GraphNode:
  def __init__(self, id, edge_weight = 0):
    self._id = id
    self._edge_weight = edge_weight
    self.attribute = dict()

  @property
  def weight(self):
    return self._edge_weight

  @property
  def id(self):
    return self._id

  def __hash__(self):
    return self._id

  def __eq__(self, other):
    return self.__hash__() == other.__hash__()

  def __str__(self):
    return f"{{ id:{self._id}, w:{self._edge_weight} }}"


class GraphInternalError(Exception):
  def __init__(self, message):
    self.message = message


class Graph:
  def __init__(self, size):
    self._adjacment = { x: ( GraphNode(x), set() ) for x in range(0, size) }

  @property
  def size(self):
    return len(self._adjacment.keys())

  @property
  def edges(self):
    edges = set()
    for id in self._adjacment.keys():
      src = id
      for node in self.get_adjacement_nodes(src):
        dest = node.id
        edge = (src, dest, node.weight)
        if not (dest, src, node.weight) in edges:
          edges.add(edge)
    return edges

  def __iter__(self):
    self.__iter = iter(self._adjacment.keys())
    return self

  def __next__(self):
    next_id = next(self.__iter)
    return self._adjacment[next_id]

  def __contains__(self, node_id):
    return node_id in self._adjacment.keys()
 
  def contains_node(self, node):
    return self.__contains__(node.id)

  def add_node(self):
    self._adjacment[self.size] = ( GraphNode(self.size), set() ) 
    return self
    
  def get_adjacement_nodes(self, node_id):
    if node_id in self:
      return list(self._adjacment[node_id][1])
    else:
      return []

  def contains_edge(self, node_a, node_b):
    return self.get_adjacement_nodes(node_a) and node_a in self.get_adjacement_nodes(node_b)

  def add_edge(self, node_a, node_b, weight = 0):
    if node_a in self and node_b in self:
      if not self.contains_edge(node_a, node_b):
        adjacent_node_a = GraphNode(node_a, weight)
        adjacent_node_b = GraphNode(node_b, weight)
        self._adjacment[node_a][1].add(adjacent_node_b)
        self._adjacment[node_b][1].add(adjacent_node_a)
        return True
      else:
        return False
    else:
      raise GraphInternalError(f"Nodes {node_a} or {node_b} do not belong to the graph")

  def save_to_file(self, filename="graph.pkl"):
    with open(filename, 'wb') as output:
      pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

  @staticmethod
  def load(filename):
    graph = None
    with open(filename, 'rb') as input:
      graph = pickle.load(input)
    return graph

  def print(self):
    for id in self._adjacment.keys():
      print(f"Node #{id}:", [ str(x) for x in self.get_adjacement_nodes(id) ] )


class GraphCategory(IntFlag):
  LOOPS = 1 << 0
  CONNECTED = 1 << 1
  WEIGHTED = 1 << 2


class GraphCategorySet:
  def __init__(self, *flags):
    self._preset = 0
    for f in flags:
      self._preset |= GraphCategory[str(f).upper()]

  def __contains__(self, preset):
    return (self._preset & preset) == preset


class GraphGenerator:
  
  @staticmethod
  def create(size, presets=('weighted', 'connected'), max_weight=100):
    preset = GraphCategorySet(*presets)

    MIN_EDGES_LOOPS = size
    MIN_EDGES_CONNECTED = size - 1
    MAX_EDGES = (size * (size - 1)) / 2

    min_edges = 0
    if GraphCategory.LOOPS in preset:
      min_edges += MIN_EDGES_LOOPS
    if GraphCategory.CONNECTED in preset:
      min_edges += MIN_EDGES_CONNECTED

    max_edges = MAX_EDGES
    if GraphCategory.LOOPS in preset:
      max_edges += MIN_EDGES_LOOPS

    graph = Graph(size)
    edges_count = random.randint(min_edges, max_edges)

    if GraphCategory.LOOPS in preset:
      for i in range(0, size):
        graph.add_edge(i, i, 0)
      edges_count -= MIN_EDGES_LOOPS

    if GraphCategory.CONNECTED in preset:
      for i in range(0, size - 1):
        weight = random.randint(0, max_weight) if GraphCategory.WEIGHTED in preset else 0
        graph.add_edge(i, i + 1, weight)
      edges_count -= MIN_EDGES_CONNECTED

    while edges_count > 0:
      while True:
        node_a = random.randint(0, size - 1)
        node_b = random.randint(0, size - 1)
        if node_a == node_b and GraphCategory.LOOPS not in preset:
          continue

        weight = random.randint(0, max_weight) if GraphCategory.WEIGHTED in preset else 0
        
        if graph.add_edge(node_a, node_b, weight):
          break
      
      edges_count -= 1

    return graph



if __name__ == "__main__":
  size = 3
  print("Test started...")
  print("Size: ", size)
  graph = GraphGenerator.create(size, presets=('connected', 'weighted'))

  print('Graph created')
  print("Edges count: ", len(graph.edges))
  print("Nodes count: ", graph.size)
  print("Graph adjacency lists:")
  graph.print()

 
