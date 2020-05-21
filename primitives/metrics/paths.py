from ..graph import Graph, GraphInternalError
from enum import Enum
import copy
import math


class NodeColor(Enum):
  WHITE = 0,
  GRAY = 1,
  BLACK = 2,


def deep_first_search(graph):
  g = copy.deepcopy(graph)

  for node in g:
    node.attribute['color'] = NodeColor.WHITE
    node.attribute['parent'] = None

  for node in g:
    if node.attribute['color'] == NodeColor.WHITE:
      _dfs_visit(g, node)


def _dfs_visit(graph, node):
  node.attribute['color'] = NodeColor.GRAY

  for adjacment_node in graph.adjacent_nodes(node.id):
    if adjacment_node.attribute['color'] == NodeColor.WHITE:
      adjacment_node.attribute['parent'] = node.id
      _dfs_visit(graph, adjacment_node)
  
  node.attribute['color'] = NodeColor.BLACK


# Deep first search based 
def find_paths(graph, src_id, dest_id):
  g = copy.deepcopy(graph)

  for node in g:
    node.attribute['visited'] = False

  src = g.get_node(src_id)
  dest = g.get_node(dest_id)

  if src is None or dest is None:
    raise GraphInternalError(f"Nodes with id {src_id} or {dest_id} do not belong to the graph")

  return _find_paths(g, src, dest, paths = [])


def _find_paths(graph, src, dest, path = [], paths = []):
  src.attribute['visited'] = True
  path.append(src.id)

  if src == dest:
    paths.append(path)

  for node in graph.adjacent_nodes(src.id):
    if not node.attribute['visited']:
      _find_paths(graph, node, dest, path.copy(), paths)

  src.attribute['visited'] = False
  return paths


# Deep first search based 
def count_paths(graph, src_id, dest_id):
  g = copy.deepcopy(graph)

  for node in g:
    node.attribute['visited'] = False

  src = g.get_node(src_id)
  dest = g.get_node(dest_id)

  if src is None or dest is None:
    raise GraphInternalError(f"Nodes with id {src_id} or {dest_id} do not belong to the graph")

  return _count_paths(g, src, dest)


def _count_paths(graph, src, dest, acc = 0):
  src.attribute['visited'] = True

  if src == dest:
    acc = acc + 1

  for node in graph.adjacent_nodes(src.id):
    if not node.attribute['visited']:
      acc = _count_paths(graph, node, dest, acc)

  src.attribute['visited'] = False
  return acc


# Dijkstra shortest path
def _initialize_single_source(graph, src_id):
  g = copy.deepcopy(graph)
  src = g.node(src_id)

  for node in g:
    node.attribute['distance'] = math.inf
    node.attribute['predecessor'] = None

  src.attribute['distance'] = 0
  return g


def _relax(src, dest):
  dest_next_upper_bound = src.attribute['distance'] + src.get_weight(dest.id)
  if dest.attribute['distance'] > dest_next_upper_bound:
    dest.attribute['distance'] = dest_next_upper_bound
    dest.attribute['predecessor'] = src.id


def _extract_min(nodes):
  minimal = nodes[0]
  for node in nodes:
    if node.attribute['distance'] <= minimal.attribute['distance']:
      minimal = node
  return minimal


def _collect_shortest_path(graph, src, dest):
  if src == dest:
    return [ src ]
  elif dest.attribute['predecessor'] is None:
    return [ None ]
  else:
    predecessor_id = dest.attribute['predecessor']
    prev_path = _collect_shortest_path(graph, src, graph.get_node(predecessor_id))
    return prev_path + [ dest ]


def _dijkstra(graph, src_id):
  g = _initialize_single_source(graph, src_id)
  
  nodes = list(g.nodes)
  while len(nodes) > 0:
    node = _extract_min(nodes)
    nodes.remove(node)
    
    for adjacent_node in g.adjacent_nodes(node.id):
      _relax(node, adjacent_node)
    
  return g


def get_shortest_path(graph, src_id, dest_id):
  g = _dijkstra(graph, src_id)
  src = g.node(src_id)
  dest = g.node(dest_id)
  path = _collect_shortest_path(g, src, dest)
  distance = dest.attribute['distance']
  return (path, distance)