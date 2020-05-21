import random
import pickle
from enum import IntFlag

class GraphNode:
  def __init__(self, id):
    self._id = id
    self.attribute = dict()
    self._adjacency_edge_weights = dict()

  def get_weight(self, adjacment_node_id):
    if adjacment_node_id in self._adjacency_edge_weights.keys():
      return self._adjacency_edge_weights[adjacment_node_id]
    else:
      raise GraphInternalError(f'Get weight: node {adjacment_node_id} is not adjacment to {self._id}')

  def set_weight(self, weight, adjacment_node_id):
    self._adjacency_edge_weights[adjacment_node_id] = weight

  @property
  def id(self):
    return self._id

  def __hash__(self):
    return self._id

  def __eq__(self, other):
    return self.__hash__() == other.__hash__()

  def __str__(self):
    return f"{{ id:{self._id} }}"


class GraphInternalError(Exception):
  def __init__(self, message):
    self.message = message


class Graph:
  def __init__(self, size):
    self._nodes = { x: GraphNode(x) for x in range(0, size) }
    self._adjacency = { x: set() for x in range(0, size) }

  @property
  def size(self):
    return len(self._nodes.values())

  @property
  def edges(self):
    edges = set()
    for node in self:
      adjacent_nodes = self.adjacent_nodes(node.id)
      for adjacent_node in adjacent_nodes:
        src = node
        dest = adjacent_node
        edge_candidate = ( src, dest )
        if ( dest, src ) not in edges:
          edges.add(edge_candidate)

    return edges

  @property
  def nodes(self):
    return set(self._nodes.values())

  def __iter__(self):
    self.__iter = iter(self._nodes.values())
    return self

  def __next__(self):
    return next(self.__iter)

  def __contains__(self, node_id):
    return node_id in self._nodes.keys()
 
  def contains_node(self, node):
    return self.__contains__(node.id)

  def add_node(self):
    self._nodes[self.size] = GraphNode(self.size)
    self._adjacency[self.size] = set()
    return self

  def get_node(self, id):
    return self._nodes[id] if id in self else None

  def node(self, id):
    return self._nodes[id] if id in self else None

  def adjacent_nodes(self, node_id):
    if node_id in self:
      return list(self._adjacency[node_id])
    else:
      return []

  def contains_edge(self, node_a, node_b):
    res = node_a in self and node_b in self and self._nodes[node_b] in self.adjacent_nodes(node_a) and self._nodes[node_a] in self.adjacent_nodes(node_b)
    return res

  def add_edge(self, node_a, node_b, weight = 0):
    if node_a in self and node_b in self:
      if not self.contains_edge(node_a, node_b):
        adjacent_node_a = self._nodes[node_a]
        adjacent_node_b = self._nodes[node_b]

        adjacent_node_a.set_weight(weight, node_b)
        adjacent_node_b.set_weight(weight, node_a)

        self._adjacency[node_a].add(adjacent_node_b)
        self._adjacency[node_b].add(adjacent_node_a)
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
    for source in self._nodes.values():
      print(f"Node #{source.id}:", [ (dest.id, source.get_weight(dest.id)) for dest in self.adjacent_nodes(source.id) ] )


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
        weight = random.randint(0, max_weight) if GraphCategory.WEIGHTED in preset else 0

        if node_a == node_b and GraphCategory.LOOPS not in preset:
          continue
        
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

  print("Edges: ", [ (edge[0].id, edge[1].id, edge[0].get_weight(edge[1].id) ) for edge in graph.edges ])
  graph.print()

 
