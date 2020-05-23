from .utils import Logger, EvaluationError
from .tasking import TaskGenerator
from .coordinate import Coordinates
from primitives.metrics.paths import get_shortest_path


class DispatchingInfo:
  def __init__(self, id, coordinates):
    self.__id = id
    self.__coordinates = coordinates

  @property
  def id(self):
    return self.__id

  @property
  def coordinates(self):
    return self.__coordinates

  def __eq__(self, other):
    return self.id == other.id and self.coordinates == other.coordinates



class SurveillanceObjectDispatcher:

  def __init__(self, graph):
    self.__graph = graph
    self.__generator = TaskGenerator(graph)
    self.__timetick = 0
    self.__logger = Logger('Dispatcher')

  def on_timetick(self, timetick):
    self.__timetick = timetick


  def __find_path(self, src_coordinates, dest_coordinates):
    src_id = src_coordinates.domain
    dest_id = dest_coordinates.domain
    return get_shortest_path(self.__graph, src_id, dest_id)


  def get_route(self, src_coordinates, dest_coordinates):
    route_info = self.__find_path(src_coordinates, dest_coordinates)
    self.__logger.info("Short path calculated:", [ n.id for n in route_info[0] ])
    return route_info


  def get_task(self, object_snapshot):
    return self.__generator.create_task(object_snapshot, self.__timetick)


  def on_domain_leave(self, object_snapshot, domain_id):
    self.__logger.info(f"Object #{object_snapshot.id} left domain:", domain_id)
    node = self.__graph.get_node(domain_id)
    
    if 'guests' in node.attribute.keys():
      node.attribute['guests'].remove(object_snapshot.id)
    else:
      node.attribute['guests'] = []


  def on_domain_enter(self, object_snapshot, domain_id):
    self.__logger.info(f"Object #{object_snapshot.id} entered domain:", domain_id)
    node = self.__graph.get_node(domain_id)

    if 'guests' in node.attribute.keys():
      node.attribute['guests'].append(object_snapshot.id)
    else:
      node.attribute['guests'] = [ object_snapshot.id ]