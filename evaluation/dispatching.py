from .utils import Logger, EvaluationError
from .tasking import TaskGenerator, TaskType
from .coordinate import Coordinates
from primitives.metrics.paths import get_shortest_path
import copy

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

  def __init__(self, graph, objects_count, transitions, moving_degree=0.5, max_await=10):
    self.__graph = graph
    self.__generator = TaskGenerator(graph, transitions, moving_degree=moving_degree, max_await=max_await)
    self.__timetick = 0
    self.__logger = Logger('Dispatcher')
    self.__objects_count = objects_count

    self.history = { x: [] for x in range(objects_count) }
    self.__move_target_counters = { n.id : 0 for n in graph.nodes }

  def reset(self):
    self.history = { x: [] for x in range(self.__objects_count) }
    for node in self.__graph.nodes:
      node.attribute['guests'] = []


  def on_end_of_time(self):
    self.__logger.info("Statisitcs.", "Move task targets:", self.__move_target_counters)


  def __find_path(self, src_coordinates, dest_coordinates):
    src_id = src_coordinates.domain
    dest_id = dest_coordinates.domain
    return get_shortest_path(self.__graph, src_id, dest_id)


  def get_route(self, src_coordinates, dest_coordinates):
    route_info = self.__find_path(src_coordinates, dest_coordinates)
    self.__logger.info("Short path calculated:", [ n.id for n in route_info[0] ])
    return route_info


  def get_task(self, object_snapshot, timetick):
    task = self.__generator.create_task(object_snapshot, timetick)

    if task.category == TaskType.MOVE:
      self.__move_target_counters[task.destination.domain] += 1

    return task


  def on_domain_leave(self, object_snapshot, domain_id):
    self.__logger.info(f"Object #{object_snapshot.id} left domain:", domain_id)
    node = self.__graph.get_node(domain_id)
    
    if 'guests' in node.attribute.keys():
      if object_snapshot.id in node.attribute['guests']:
        node.attribute['guests'].remove(object_snapshot.id)
    else:
      node.attribute['guests'] = []


  def on_domain_enter(self, object_snapshot, domain_id, timetick):
    self.__logger.info(f"Object #{object_snapshot.id} entered domain:", domain_id)
    node = self.__graph.get_node(domain_id)

    self.history[object_snapshot.id].append((domain_id, timetick))

    if 'guests' in node.attribute.keys():
      node.attribute['guests'].append(object_snapshot.id)
    else:
      node.attribute['guests'] = [ object_snapshot.id ]