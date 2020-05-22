from primitives.metrics.paths import get_shortest_path


class Coordinates:
  def __init__(self, domain = 0, offset = 0):
    self.domain = domain
    self.offset = offset

  def __eq__(self, other):
    return self.domain == other.domain and self.offset == other.offset

  def get(self):
    return self.domain, self.offset


class Router:
  def __init__(self, area_graph):
    self.__graph = area_graph

  def find_path(self, src_coordinates, dest_coordinates):
    src_id = src_coordinates.domain
    dest_id = dest_coordinates.domain
    return get_shortest_path(self.__graph, src_id, dest_id)