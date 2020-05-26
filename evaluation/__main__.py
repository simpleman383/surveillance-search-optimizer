from primitives.graph import GraphGenerator, Graph
from primitives.metrics.paths import get_shortest_path
from .utils import Logger
from .objects import SurveillanceObject, generate_average_speeds
from .dispatching import SurveillanceObjectDispatcher
from .tasking import TaskGenerator
from .transition import TransitionGenerator, TransitionType, GroupType
from .surveillance import BaseSurveillanceSystem as SimpleSystem
from .surveillance_advanced import SpatioTemporalSurveillance as AdvancedSystem
import time

from evaluation import experiment_root_path



class Experiment:
  def __init__(self):
    self.__timetick = 0
    self.__time_limit = 1000
    self.__time_step = 1
    self.__logger = Logger("Main")

    self.__base_domain_graph_size = 4
    self.__base_domain_graph_min_distance = 10
    self.__base_domain_graph_max_distance = 100

    self.__objects_count = 5
    self.__object_speed_exp = 10
    self.__motion_probability = .5

    self.__min_transition_group_size = 2
    self.__transition_group_distribution = GroupType.PLAIN
    self.__transition_probabilities_distribution = TransitionType.GEOMETRIC_MONOPOLAR

    self.__surveillance_nodes_ratio = 1
    self.__surveillance_target_count = 1

    self.__setup_conditions()
    self.print_conditions()


  def print_conditions(self):
    print("Starting experiment")
    print("Parameters")
    print("Domain graph size:", self.__base_domain_graph_size)
    print("Domain graph min distance:", self.__base_domain_graph_min_distance)
    print("Domain graph max distance:", self.__base_domain_graph_max_distance)
    print("-----------------------------")
    print("Objects count:", self.__objects_count)
    print("Objects motion degree:", self.__motion_probability)
    print("Objects speed expectation:", self.__object_speed_exp)
    print("-----------------------------")
    print("Object transition min group size:", self.__min_transition_group_size)
    print("Object transition group size distribution:", self.__transition_group_distribution)
    print("Object transition probabilities distribution:", self.__transition_probabilities_distribution)
    print("-----------------------------")
    print("Surveillance nodes to domains ratio:", self.__surveillance_nodes_ratio)
    print("Surveillance target count:", self.__surveillance_target_count)
    print("-----------------------------")


  def __setup_conditions(self):
    self.__logger.info("Setting up environment")

    # Generating base domain graph
    self.__domain_graph = GraphGenerator.create(self.__base_domain_graph_size, min_weight=self.__base_domain_graph_min_distance, max_weight=self.__base_domain_graph_max_distance)

    self.__logger.info("General domain graph generated.")
    self.__logger.info(self.__domain_graph)
    self.__domain_graph.save_to_file(filename=f"{experiment_root_path}/domain_graph.pkl")
    self.__logger.info("Graph file saved to", f"{experiment_root_path}/domain_graph.pkl")


    # Generating transition matrices for objects
    transition_matrix_generator = TransitionGenerator(self.__base_domain_graph_size, min_group=self.__min_transition_group_size, group_gen_type=self.__transition_group_distribution, transition_gen_type=self.__transition_probabilities_distribution)
    transition_matrices = transition_matrix_generator.get_samples(self.__objects_count)

    self.__logger.info("Transition matrices generated", transition_matrices)

    # Creating auxilary object dispatcher  
    dispatcher = SurveillanceObjectDispatcher(self.__domain_graph, transitions=transition_matrices, objects_count=self.__objects_count)
    dispatcher.reset()
    self.__movement_dispatcher = dispatcher
  
    # Generating average speeds of objects
    average_speeds = generate_average_speeds(exp=self.__object_speed_exp, size=self.__objects_count)
    self.__logger.info("Objects average speeds generated", average_speeds)


    # Initializing surveillance objects
    self.__surveillance_objects = [ SurveillanceObject(dispatcher, id=idx, average_speed=average_speeds[idx], time_step=self.__time_step) for idx in range(0, self.__objects_count) ]
    for s_object in self.__surveillance_objects:
      start_domain_id = s_object.coordinates.domain
      dispatcher.on_domain_enter(s_object.snapshot, start_domain_id, self.__timetick)

    # Setting up a reference surveillance model
    supervised_object_ids = [ obj.id for obj in self.__surveillance_objects ][: self.__surveillance_target_count]

    self.__reference_surveillance = SimpleSystem(self.__domain_graph, supervised_object_ids=supervised_object_ids, alpha=self.__surveillance_nodes_ratio)
    self.__surveillance = AdvancedSystem(self.__domain_graph, supervised_object_ids=supervised_object_ids, alpha=self.__surveillance_nodes_ratio)


  def train(self):
    self.__timetick = 0
    self.__surveillance.set_training_mode(True)
    
    while self.__timetick < self.__time_limit:
      self.__surveillance.on_timetick(self.__timetick)

      for surveillance_object in self.__surveillance_objects:
        surveillance_object.on_timetick(self.__timetick)

      self.__timetick += self.__time_step
      #time.sleep(.5)

    self.__surveillance.on_end_of_time()



  def reset_objects_positions(self):
    self.__timetick = 0

    self.__movement_dispatcher.reset()
    for obj in self.__surveillance_objects:
      obj.reset_state(0)

    for s_object in self.__surveillance_objects:
      start_domain_id = s_object.coordinates.domain
      self.__movement_dispatcher.on_domain_enter(s_object.snapshot, start_domain_id, self.__timetick)


  def inference(self):

    self.__surveillance.set_training_mode(False)

    while self.__timetick < self.__time_limit:
      self.__surveillance.on_timetick(self.__timetick)
      self.__reference_surveillance.on_timetick(self.__timetick)

      for surveillance_object in self.__surveillance_objects:
        surveillance_object.on_timetick(self.__timetick)

      self.__timetick += self.__time_step
   
    self.__logger.info("Experiment finished")

    
    self.__logger.info("Real movements:", self.__movement_dispatcher.history)
    self.__logger.info("Base model history:", self.__reference_surveillance.history)
    self.__logger.info("Advanced model history:", self.__surveillance.history)

    acc_reference = sum([ x['Frames processed'] for x in self.__reference_surveillance.resource_statistic.values() ])
    acc = sum([ x['Frames processed'] for x in self.__surveillance.resource_statistic.values() ])

    print("Reference model processed:", acc_reference)
    print("Advanced model processed:", acc)


if __name__ == '__main__':
  experiment = Experiment()
  experiment.train() 
  experiment.reset_objects_positions()
  experiment.inference()