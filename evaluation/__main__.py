from primitives.graph import GraphGenerator, Graph
from primitives.metrics.paths import get_shortest_path
from .utils import Logger
from .objects import SurveillanceObject

from .dispatching import SurveillanceObjectDispatcher
from .tasking import TaskGenerator
import time


class Experiment:
  def __init__(self):
    self.__timetick = 0
    self.__time_limit = 10000
    self.__time_step = 1


  def run(self):
    size = 3
    surveillance_object_count = 1

    graph = GraphGenerator.create(size, min_weight=5, max_weight=25)

    dispatcher = SurveillanceObjectDispatcher(graph, objects_count=surveillance_object_count)
    
    surveillance_objects = [ SurveillanceObject(dispatcher, id=idx) for idx in range(0, surveillance_object_count) ]

    while self.__timetick < self.__time_limit:

      for surveillance_object in surveillance_objects:
        surveillance_object.on_timetick(self.__timetick)

      dispatcher.on_timetick(self.__timetick)
      
      self.__timetick += self.__time_step
      time.sleep(1)



if __name__ == '__main__':
  experiment = Experiment()
  experiment.run() 
