import random
import math
from primitives.metrics.paths import find_paths, get_shortest_of_paths
from primitives.graph import Graph, GraphNode
from .utils import Logger

class SurveillanceError(Exception):
  def __init__(self, message):
    self.message = message


class SimpleSurveillanceNode(GraphNode):
  def __init__(self, id, dispatcher):
    super().__init__(id)
    self._dispatcher = dispatcher
    self._active = True
    self._frames_processed = 0


  @property
  def resource_statistic(self):
    return { "Frames processed": self._frames_processed }


  def distance_to(self, adjacent_node_id):
    return self.get_weight(adjacent_node_id)


  def process_frame(self, timetick):
    if self._active:
      observed_domain = self.attribute['observed_domain']
      frame_content = observed_domain.attribute['guests']
      self._frames_processed += 1
      self._dispatcher.on_process_frame((self.id, observed_domain.id), timetick, frame_content)


class SurveillanceDispatcher:
  def __init__(self, targets):
    self._logger = Logger("Surveillance dispatcher")
    self._targets = targets
    self._node_statistics = dict()


  @property
  def node_statistics(self):
    return self._node_statistics


  def _update_statistic(self, source_id):
    if source_id in self._node_statistics.keys():
      self._node_statistics[source_id]['Frames processed'] += 1
    else:
      self._node_statistics[source_id] = { 'Frames processed': 0 }


  def on_process_frame(self, source, timetick, frame_content):
    match_result = set(frame_content).intersection(set(self._targets))

    if len(match_result) > 0:
      self._logger.info(f"[Node #{source[0]} Domain #{source[1]}] Timetick: {timetick} Match detected:", match_result)
    
    self._update_statistic(source[0])




class BaseSurveillanceSystem:
  def __init__(self, domain_graph, supervised_object_ids=[], alpha=1, logger=None):
    self._logger = Logger("Simple Surveillance System") if logger is None else logger

    self._dispatcher = SurveillanceDispatcher(supervised_object_ids)

    self._surveillance_nodes = self.__get_surveillance_nodes(domain_graph, self._dispatcher, alpha)
    self._targets = supervised_object_ids
    
    self._logger.info("System initialized")
    self._logger.info("Target object ids:", self._targets)
    self._logger.info("Surveillance/domain node matching:", [ (x.id, x.attribute['observed_domain'].id) for x in self._surveillance_nodes ])


  @property
  def resource_statistic(self):
    return self._dispatcher.node_statistics


  def __get_surveillance_nodes(self, domain_graph, dispatcher, alpha):
    if alpha <= 0 or alpha > 1:
      raise SurveillanceError("alpha should be between 0 and 1")

    surveillance_size = math.ceil(alpha * domain_graph.size)

    domain_graph_nodes = list(domain_graph.nodes)
    random.shuffle(domain_graph_nodes)
    supervised_domain_nodes = domain_graph_nodes[0: surveillance_size]

    surveillance_nodes = [ SimpleSurveillanceNode(idx, dispatcher) for idx in range(0, surveillance_size) ]
    for idx in range(len(surveillance_nodes)):
      node = surveillance_nodes[idx]
      node.attribute['observed_domain'] = supervised_domain_nodes[idx]

    return surveillance_nodes      


  def on_timetick(self, timetick):
    for surveillance_node in self._surveillance_nodes:
      surveillance_node.process_frame(timetick)
    
    
      
