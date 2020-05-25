import random
import math
from primitives.metrics.paths import find_paths, get_shortest_of_paths
from primitives.graph import Graph
from .utils import Logger

class SurveillanceError(Exception):
  def __init__(self, message):
    self.message = message




def filter_direct_routes(routes, src, dest, all_nodes):
  def is_direct(route, src, dest, all_nodes):
    for point in route:
      if point in all_nodes and point != src and point != dest:
        return False
    return True

  filtered = []

  for route in routes:
    if is_direct(route, src, dest, all_nodes):
      filtered.append(route)

  return filtered



class Surveillance:
  def __init__(self, domain_graph, supervised_objects=[], alpha=1, logger=None):
    self._logger = Logger("Surveillance") if logger is None else logger
    self._surveillance_graph = self.__build_surveillance_graph(domain_graph, alpha)
    self._targets = supervised_objects

    for surveillance_node in self._surveillance_graph.nodes:
      surveillance_node.attribute['active'] = False
    

  def __activate_surveillance_nodes(self):
    for surveillance_node in self._surveillance_graph.nodes:
      surveillance_node.attribute['active'] = False
    

  def __build_surveillance_graph(self, domain_graph, alpha):
    return Surveillance.from_domain_graph(domain_graph, alpha=alpha)


  def __process_frame(self, surveillance_node, timetick):
    observed_domain = surveillance_node.attribute['observed_domain']

    self._logger.info(f"[Node #{surveillance_node.id} Domain #{observed_domain.id}]" ,f"Timetick: {timetick}. Processing...")

    registered_objects = set(observed_domain.attribute['guests'])

    result = registered_objects.intersection(set(self._targets))
    if len(result) > 0:
      self._logger.info(f"[Node #{surveillance_node.id} Domain #{observed_domain.id}]" ,f"Timetick: {timetick}. Match detected - {result}")


  def on_timetick(self, timetick):
    for surveillance_node in self._surveillance_graph.nodes:
      if surveillance_node.attribute['active']:
        self.__process_frame(surveillance_node, timetick)
    

  @staticmethod
  def from_domain_graph(domain_graph, alpha=1):
    if alpha <= 0 or alpha > 1:
      raise SurveillanceError("alpha should be between 0 and 1")
    
    surveillance_size = math.ceil(alpha * domain_graph.size)
    surveillance_graph = Graph(surveillance_size)

    domain_graph_nodes = list(domain_graph.nodes)
    random.shuffle(domain_graph_nodes)
    supervised_domain_nodes = domain_graph_nodes[0: surveillance_size]

    for idx in range(0, surveillance_size):
      surveillance_node = surveillance_graph.get_node(idx)
      surveillance_node.attribute['observed_domain'] = supervised_domain_nodes[idx]


    supervised_domain_node_ids = [ node.id for node in supervised_domain_nodes ]

    for x in range(0, surveillance_size):
      for y in range(0, x):
        src = surveillance_graph.get_node(x).attribute['observed_domain'].id
        dest = surveillance_graph.get_node(y).attribute['observed_domain'].id

        candidate_paths = find_paths(domain_graph, src, dest)

        filtered_candidate_paths = filter_direct_routes(candidate_paths, src, dest, supervised_domain_node_ids)
        if len(filtered_candidate_paths) == 0:
          continue
        else:
          shortest_distance = get_shortest_of_paths(domain_graph, filtered_candidate_paths)
          surveillance_graph.add_edge(x, y, weight=shortest_distance)

    return surveillance_graph



class BaseSurveillance(Surveillance):
  def __init__(self, domain_graph, supervised_objects=[], alpha=1):
    super().__init__(domain_graph, supervised_objects=supervised_objects, alpha=alpha, logger=Logger("BaseSurveillance"))
    self.__activate_surveillance_nodes()
    self._logger.info("System created")
    self._logger.info("System graph:", self._surveillance_graph)


  def __activate_surveillance_nodes(self):
    for node in self._surveillance_graph.nodes:
      node.attribute['active'] = True
    self._logger.info("All surveillance nodes activated")
    
      
