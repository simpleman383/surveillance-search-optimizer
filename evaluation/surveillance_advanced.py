import math
import random 

from abc import ABC, abstractmethod
from enum import Enum
from .utils import Logger
from .surveillance import SurveillanceError, SimpleSurveillanceNode, SurveillanceDispatcher
from primitives.graph import Graph, GraphNode
from primitives.metrics.paths import find_paths, get_shortest_of_paths
from .networking import Network, Sender, Receiver
from .tasking import TaskStack

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



class Event(Enum):
  ENTERED = 0,
  LEFT = 1,


class Signal(Enum):
  DEACTIVATE = 0,
  ACTIVATE = 1


class Message:
  def __init__(self, signal_type, timeout=0):
    self.__signal_type = signal_type
    self.__timeout = timeout
  
  @property
  def signal_type(self):
    return self.__signal_type

  @property
  def timeout(self):
    return self.__timeout
    

class SmartSurveillanceNode(SimpleSurveillanceNode, Receiver):
  def __init__(self, id, dispatcher):
    super().__init__(id, dispatcher)
    self.__prev_frame_object_ids = set()
    self._tasks = set()
    self._active = True


  def connect(self, network):
    self._sender = Sender(network)

  def activate(self):
    self._active = True

  def deactivate(self):
    self._active = False

  def on_receive(self, src, message):
    print('receive!')
    pass

  def update_state(self, timetick):
    pass

  
  def __broadcast_signal(self, signal_type):
    adjacent_node_ids = self._adjacency_edge_weights.keys()
    print('Broadcast', signal_type)

    for dest_node_id in adjacent_node_ids:
      self._sender.send(self.id, dest_node_id, signal_type)


  def __process_frame(self, timetick):
    current_frame_object_ids = self.get_frame_content()
    self._dispatcher.on_process_frame((self.id, self.observed_domain.id), timetick, current_frame_object_ids)

    incoming_objects_count = len(set(current_frame_object_ids).difference(self.__prev_frame_object_ids))
    outcoming_objects_count = len(set(self.__prev_frame_object_ids).difference(current_frame_object_ids))

    if incoming_objects_count > 0 and outcoming_objects_count > 0:
      self.__broadcast_signal(Signal.ACTIVATE)
    elif incoming_objects_count == 0 and outcoming_objects_count > 0:
      self.__broadcast_signal(Signal.ACTIVATE)
    elif incoming_objects_count > 0 and outcoming_objects_count == 0:
      self.__broadcast_signal(Signal.DEACTIVATE)
    else:
      pass

    self.__prev_frame_object_ids = current_frame_object_ids
  
  
  def process(self, timetick):
    if self._active:
      self.__process_frame(timetick)



class SurveillanceGraph(Graph):
  def __init__(self, size, dispatcher):
    self._nodes = { x: SmartSurveillanceNode(x, dispatcher) for x in range(0, size) }
    self._adjacency = { x: set() for x in range(0, size) }



class SpatioTemporalSurveillance:
  def __init__(self, domain_graph, supervised_object_ids=[], alpha=1, logger=None):
    self._logger = Logger("SpatioTemporalSurveillance")

    self._dispatcher = SurveillanceDispatcher(supervised_object_ids)
    self._surveillance_graph = self.__build_surveillance_graph(domain_graph, alpha, self._dispatcher)

    self._network = Network.establish(self._surveillance_graph.nodes)
    for node in self._surveillance_graph.nodes:
      node.connect(self._network)

    
  def on_timetick(self, timetick):
    for surveillance_node in self._surveillance_graph.nodes:
      surveillance_node.update_state(timetick)

    for surveillance_node in self._surveillance_graph.nodes:
      surveillance_node.process(timetick)


  def __build_surveillance_graph(self, domain_graph, alpha, dispatcher):
    if alpha <= 0 or alpha > 1:
      raise SurveillanceError("alpha should be between 0 and 1")
    
    surveillance_size = math.ceil(alpha * domain_graph.size)
    surveillance_graph = SurveillanceGraph(surveillance_size, dispatcher)

    domain_graph_nodes = list(domain_graph.nodes)
    random.shuffle(domain_graph_nodes)
    supervised_domain_nodes = domain_graph_nodes[0: surveillance_size]

    for idx in range(0, surveillance_size):
      surveillance_node = surveillance_graph.get_node(idx)
      surveillance_node.set_observed_domain(supervised_domain_nodes[idx])

    supervised_domain_node_ids = [ node.id for node in supervised_domain_nodes ]

    for x in range(0, surveillance_size):
      for y in range(0, x):
        src = surveillance_graph.get_node(x).observed_domain.id
        dest = surveillance_graph.get_node(y).observed_domain.id

        candidate_paths = find_paths(domain_graph, src, dest)

        filtered_candidate_paths = filter_direct_routes(candidate_paths, src, dest, supervised_domain_node_ids)
        if len(filtered_candidate_paths) == 0:
          continue
        else:
          shortest_distance = get_shortest_of_paths(domain_graph, filtered_candidate_paths)
          surveillance_graph.add_edge(x, y, weight=shortest_distance)

    return surveillance_graph