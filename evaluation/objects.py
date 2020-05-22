from enum import Enum
from uuid import uuid4
from .utils import EvaluationError
from .tasking import TaskStack, TaskType
from .routing import Router, Coordinates
from .utils import Logger


class State(Enum):
  IDLE = 0,
  MOVING = 1


class SurveillanceObject:

  def __init__(self, router, start_domain = 0, id = None):
    self.__id = id if id is not None else uuid4().hex
    self.__task_stack = TaskStack()

    self.__router = router
    self.__coordinates = Coordinates(start_domain)
    self.__state = State.IDLE
    self.__route = None
    self.__speed = 0

    self.__logger = Logger(f"Object #{self.__id}")


  @property
  def current_task(self):
    return self.__task_stack.current

  @property
  def coordinates(self):
    return self.__coordinates
  

  def __on_task_changed(self):
    if self.current_task is None:
      self.__speed = 0
      self.__route = None
      self.__state = State.IDLE
      return 

    if self.current_task.category == TaskType.WAIT:
      self.__logger.info("Received await task.")
      self.__speed = 0
      self.__route = None
      self.__state = State.IDLE
    elif self.current_task.category == TaskType.MOVE:
      self.__logger.info("Received move task.", f"From: {self.__coordinates.domain}", f"To: {self.current_task.destination.domain}")
      self.__speed = 1
      self.__route, _ = self.__router.find_path(self.__coordinates, self.current_task.destination)
      self.__state = State.MOVING


  def __on_domain_reached(self, domain_id):
    self.__logger.info('Domain changed. New domain: ', domain_id)


  def add_task(self, task):
    self.__task_stack.push(task)
    self.__on_task_changed()

  
  def __process_wait_task(self):
    return self.__coordinates


  def __process_move_task(self):
    current_node = self.__route[0]
    target_node = self.__route[1]
    distance = current_node.get_weight(target_node.id)

    current_domain, current_offset = self.__coordinates.get()

    next_offset = current_offset + self.__speed

    if next_offset >= distance:
      next_domain = target_node.id
      self.__route.pop(0)
      self.__on_domain_reached(next_domain)
      return Coordinates(next_domain, 0)
    else:
      return Coordinates(current_domain, next_offset)      


  def process_current_task(self, timetick):

    if self.current_task.category == TaskType.WAIT:
      self.__coordinates = self.__process_wait_task()
    
    if self.current_task.category == TaskType.MOVE:
      self.__coordinates = self.__process_move_task()

    self.__logger.info('Coordinates changed:', self.__coordinates.domain, self.__coordinates.offset)
    
    if self.current_task.completed(self.__coordinates, timetick):
      self.__logger.info('Task completed', f'Current domain: {self.__coordinates.domain}')
      self.__task_stack.pop()
      self.__on_task_changed()




