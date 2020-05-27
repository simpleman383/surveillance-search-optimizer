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

 

class EdgeWeightSet:
  def __init__(self, distance, min_time, intensity):
    self.distance = distance
    self.min_time = math.inf
    self.intensity = intensity


class SpatioTemporalSurveillanceGraph(Graph):
  def __init__(self, size, dispatcher, supervised_object_ids):
    self._nodes = { x: SmartSurveillanceNode(x, dispatcher, target_objects=supervised_object_ids) for x in range(0, size) }
    self._adjacency = { x: set() for x in range(0, size) }


class Signal(Enum):
  OBJECT_LEFT_DOMAIN = 0,
  OBJECT_ENTERED_DOMAIN = 1,
  CANCEL_WAITING = 2,


class SmartSurveillanceNode(SimpleSurveillanceNode, Receiver):
  def __init__(self, id, dispatcher, target_objects=[]):
    super().__init__(id, dispatcher)
    self.__logger = Logger(f"Surveillance_Node_#{id}")
    self.__prev_frame = []
    
    self.__targets = target_objects
    self.__awaiting_objects = dict()

  def reset(self):
    self.__awaiting_objects = dict()
    self.__prev_frame = []


  def connect(self, network):
    self.__sender = Sender(network)

  @property
  def adjacent_nodes(self):
    return self._adjacency_edge_weights.keys()

  def on_receive(self, src, message):
    signal_type, object_id, timetick, training = message

    if training:

      if signal_type == Signal.OBJECT_LEFT_DOMAIN:
        self.__awaiting_objects[object_id] = (src, timetick)
        
      if signal_type == Signal.OBJECT_ENTERED_DOMAIN:
        for node_id in self.adjacent_nodes:
          self.__sender.send(self.id, node_id, (Signal.CANCEL_WAITING, object_id, 0, training))
      
      if signal_type == Signal.CANCEL_WAITING:
        if object_id in self.__awaiting_objects.keys():
          del self.__awaiting_objects[object_id]
    
    else:
      self.__logger.info(f"Received message from {src}:", signal_type, object_id, timetick)
      
      if signal_type == Signal.OBJECT_LEFT_DOMAIN:
        if not math.isinf(self.get_weight(src).min_time):
          estimated_activation_time = timetick + self.get_weight(src).min_time - 1
          self.__awaiting_objects[object_id] = (src, estimated_activation_time)
          self.__logger.info(f"Awaiting for object from {src}.", "Estimated act time:", estimated_activation_time)

      
      if signal_type == Signal.OBJECT_ENTERED_DOMAIN:
        for node_id in self.adjacent_nodes:
          if node_id != src:
            self.__sender.send(self.id, node_id, (Signal.CANCEL_WAITING, object_id, 0, training))

      if signal_type == Signal.CANCEL_WAITING:
        if object_id in self.__awaiting_objects.keys():
          del self.__awaiting_objects[object_id]
      


  def __on_training_timetick(self, timetick):
    frame = self.get_frame_content()

    incoming = set(frame).difference(self.__prev_frame)
    outcoming = set(self.__prev_frame).difference(frame)

    for object_id in outcoming:
      self.__awaiting_objects[object_id] = (self.id, timetick)
      for node_id in self.adjacent_nodes:
        self.__sender.send(self.id, node_id, (Signal.OBJECT_LEFT_DOMAIN, object_id, timetick, True))


    for object_id in incoming:
      if object_id in self.__awaiting_objects.keys():
        src_domain_id, start_time = self.__awaiting_objects[object_id]

        self.__update_weight_set(src_domain_id, start_time, timetick)
        self.__sender.send(self.id, src_domain_id, (Signal.OBJECT_ENTERED_DOMAIN, object_id, timetick, True))

    self.__prev_frame = frame
    


  def __update_weight_set(self, domain_id, start_time, end_time):
    if self.id == domain_id:
      return

    weight_object = self.get_weight(domain_id)
    weight_object.intensity += 1

    time_candidate = end_time - start_time
    if time_candidate < weight_object.min_time:
      weight_object.min_time = time_candidate


  def __process_frame(self, timetick):
    frame = self.get_frame_content()

    incoming_objects = set(frame).difference(self.__prev_frame)
    outcoming_objects = set(self.__prev_frame).difference(frame)

    detected_objects = []

    for object_id in outcoming_objects:
      if object_id in self.__targets:
        self.__awaiting_objects[object_id] = (self.id, timetick)
        for node_id in self.adjacent_nodes:
          self.__sender.send(self.id, node_id, (Signal.OBJECT_LEFT_DOMAIN, object_id, timetick, False))

    for object_id in incoming_objects:
      if object_id in self.__targets:
        
        detected_objects.append(object_id)
        
        if object_id in self.__awaiting_objects.keys():
          src_domain_id, _ = self.__awaiting_objects[object_id]
          self.__sender.send(self.id, src_domain_id, (Signal.OBJECT_ENTERED_DOMAIN, object_id, timetick, False))
        else:
          pass
          # print('Non-expectable object in frame') 

    self._dispatcher.on_process_frame((self.id, self.observed_domain.id), timetick, detected_objects)
    self.__prev_frame = frame


  def __relevant_activation_tasks(self, timetick):
    res = []
    for object_id in self.__awaiting_objects.keys():
      _, estimated_activation_time = self.__awaiting_objects[object_id]
      if estimated_activation_time <= timetick:
        res.append(object_id)
    return res


  def __on_inference_timetick(self, timetick):
    if self._active:
      self.__process_frame(timetick)


  def on_timetick(self, timetick, training=True):
    if training:
      self.__on_training_timetick(timetick)
    else:
      self.__on_inference_timetick(timetick)

  
  def update_active_status(self, timetick):
    current_activation_tasks = self.__relevant_activation_tasks(timetick)
    if len(current_activation_tasks) == 0 and len(self.get_frame_content()) == 0 :
      self.__logger.info(f"Deactivating due to the absense of relevant tasks", current_activation_tasks, "timetick:", timetick)
      self._active = False
      self.__prev_frame = []
    else:
      self.__logger.info(f'Activating [timetick={timetick}]', current_activation_tasks)
      self._active = True




class SpatioTemporalSurveillance:
  def __init__(self, domain_graph, supervised_object_ids=[], alpha=1, logger=None):
    self._logger = Logger("SpatioTemporalSurveillance")

    self.__training = False
    self._dispatcher = SurveillanceDispatcher(targets=supervised_object_ids)
    self._surveillance_graph = self.__build_surveillance_graph(domain_graph, alpha, self._dispatcher, supervised_object_ids)

    network = Network.establish(self._surveillance_graph.nodes)
    for node in self._surveillance_graph.nodes:
      node.connect(network)

  @property
  def history(self):
    return self._dispatcher.history

  def get_history_formatted(self):
    return "".join([ f"{x}: {self._dispatcher.history[x]}\n" for x in self._dispatcher.history.keys() ])

  @property
  def resource_statistic(self):
    return self._dispatcher.node_statistics

  def set_training_mode(self, active):
    self.__training = active
    for node in self._surveillance_graph.nodes:
      node.reset()


  def on_timetick(self, timetick):
    for node in self._surveillance_graph.nodes:
      node.on_timetick(timetick, training=self.__training)

    if not self.__training:
      for node in self._surveillance_graph.nodes:
        node.update_active_status(timetick)


  def on_end_of_time(self):
    if self.__training:
      print('Training results:')
      print('Edge Dist Int Min_time')
      for src in self._surveillance_graph.nodes:
        for dest in src.adjacent_nodes:
          print((src.id, dest), src.get_weight(dest).distance, src.get_weight(dest).intensity, src.get_weight(dest).min_time )



  def __build_surveillance_graph(self, domain_graph, alpha, dispatcher, supervised_object_ids):
    if alpha <= 0 or alpha > 1:
      raise SurveillanceError("alpha should be between 0 and 1")
    
    surveillance_size = math.ceil(alpha * domain_graph.size)
    surveillance_graph = SpatioTemporalSurveillanceGraph(surveillance_size, dispatcher, supervised_object_ids)

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
          weight_set = EdgeWeightSet(shortest_distance, 0, 0)
          surveillance_graph.add_edge(x, y, weight=weight_set)

    return surveillance_graph