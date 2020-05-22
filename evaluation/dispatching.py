from .utils import Logger, EvaluationError
from .objects import SurveillanceObject
from .tasking import TaskGenerator
from .routing import Router


class SurveillanceObjectDispatcher:
  def __init__(self, area_graph):
    self.__logger = Logger("Dispatcher")
    self.__logger.info("Setting up surveillance object dispatcher")
    self.__graph = area_graph
    self.__generator = TaskGenerator(area_graph)


  def setup_objects(self, count = 1):
    self.__logger.info("Initializing surveillance objects. Count:", count)
   
    router = Router(self.__graph)
    self.__surveillance_objects = [ SurveillanceObject(router, id=i) for i in range(0, count) ]


  def on_timetick(self, timetick):
    if self.__surveillance_objects is None:
      raise EvaluationError("No surveillance objects created")

    for surveillance_object in self.__surveillance_objects:
      if surveillance_object.current_task is None:
        task = self.__generator.create_task(surveillance_object, timetick)
        surveillance_object.add_task(task)

      surveillance_object.process_current_task(timetick)


