from primitives.graph import GraphGenerator, Graph
from primitives.metrics.paths import get_shortest_path
from .utils import Logger
from .objects import SurveillanceObject, generate_average_speeds

from .dispatching import SurveillanceObjectDispatcher
from .tasking import TaskGenerator
from .transition import TransitionGenerator, TransitionType, GroupType
import time

from evaluation import experiment_root_path



class Experiment:
  def __init__(self):
    self.__timetick = 0
    self.__time_limit = 1000
    self.__time_step = 1
    self.__logger = Logger("Main")


  def run(self):
    size = 3
    surveillance_object_count = 1
    self.__logger.info("Experiment started")

    graph = GraphGenerator.create(size, min_weight=3, max_weight=10)

    self.__logger.info("General domain graph generated.")
    self.__logger.info(graph)
    graph.save_to_file(filename=f"{experiment_root_path}/domain_graph.pkl")
    self.__logger.info("Graph file saved to", f"{experiment_root_path}/domain_graph.pkl")
    
    transition_matrix_generator = TransitionGenerator(size, min_group=2, group_gen_type=GroupType.PLAIN, transition_gen_type=TransitionType.GEOMETRIC_MONOPOLAR)
    transition_matrices = transition_matrix_generator.get_samples(surveillance_object_count)

    self.__logger.info("Transition matrices generated", transition_matrices)

    dispatcher = SurveillanceObjectDispatcher(graph, transitions=transition_matrices, objects_count=surveillance_object_count)
    average_speeds = generate_average_speeds(size=surveillance_object_count)

    self.__logger.info("Objects average speeds generated", average_speeds)

    surveillance_objects = [ SurveillanceObject(dispatcher, id=idx, average_speed=average_speeds[idx]) for idx in range(0, surveillance_object_count) ]

    while self.__timetick < self.__time_limit:

      for surveillance_object in surveillance_objects:
        surveillance_object.on_timetick(self.__timetick)

      dispatcher.on_timetick(self.__timetick)
      
      self.__timetick += self.__time_step
      # time.sleep(1)

    dispatcher.on_end_of_time()
    self.__logger.info("Experiment finished")



if __name__ == '__main__':
  experiment = Experiment()
  experiment.run() 
