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
    size = 20
    surveillance_object_count = 1

    graph = GraphGenerator.create(size, max_weight=50)
    #graph.print()

    dispatcher = SurveillanceObjectDispatcher(graph)
    dispatcher.setup_objects(surveillance_object_count)

    while self.__timetick < self.__time_limit:
      dispatcher.on_timetick(self.__timetick)
      self.__timetick += self.__time_step
      #time.sleep(.01)



if __name__ == '__main__':
  experiment = Experiment()
  experiment.run() 
