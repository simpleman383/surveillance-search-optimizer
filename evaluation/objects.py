from enum import Enum
from uuid import uuid4
from .utils import EvaluationError, Logger
from .tasking import TaskStack, TaskType
from .dispatching import SurveillanceObjectDispatcher, DispatchingInfo
from .coordinate import Coordinates
from numpy import random

class State(Enum):
  IDLE = 0,
  MOVING = 1

def generate_average_speeds(exp=1, sigma=0.5, size=1):
  speeds = []
  while len(speeds) < size:
    candidate = random.normal(exp, sigma, 1)
    if candidate > 0:
      speeds.append(candidate)
  
  return speeds


class SurveillanceObject:

  def __init__(self, dispatcher, start_domain = 0, id = None, average_speed=1):
    self.__id = id if id is not None else uuid4().hex
    self.__task_stack = TaskStack()

    self.__dispatcher = dispatcher
    self.__coordinates = Coordinates(start_domain)
    self.__state = State.IDLE
    self.__route = None
    self.__speed = 0
    self.__average_speed = average_speed

    self.__logger = Logger(f"Object #{self.__id}")
    self.__logger.info(f'Object #{self.__id} created')


  @property
  def current_task(self):
    return self.__task_stack.current

  @property
  def coordinates(self):
    return self.__coordinates
  
  @property
  def snapshot(self):
    return DispatchingInfo(self.__id, self.__coordinates)

  def __on_task_changed(self):
    if self.current_task is None:
      new_task = self.__dispatcher.get_task(self.snapshot)
      self.__add_task(new_task)
      return 

    if self.current_task.category == TaskType.WAIT:
      self.__on_wait_task_received()
    elif self.current_task.category == TaskType.MOVE:
      self.__on_move_task_received()
      

  def __on_wait_task_received(self):
    self.__logger.info("Received await task.", "Timeout:", self.current_task.timeout)
    self.__state = State.IDLE
    self.__speed = 0
    self.__route = None

  def __on_move_task_received(self):
    self.__logger.info("Received move task.", f"From: {self.__coordinates.domain}", f"To: {self.current_task.destination.domain}")
    self.__state = State.MOVING
    self.__speed = self.__average_speed
    self.__route, _ = self.__dispatcher.get_route(self.__coordinates, self.current_task.destination)
  

  def __on_domain_reached(self, domain_id):
    self.__route.pop(0)
    self.__dispatcher.on_domain_enter(self.snapshot, domain_id)


  def __add_task(self, task):
    if task is None:
      raise EvaluationError("Task cannot be none")

    self.__task_stack.push(task)
    self.__on_task_changed()


  def add_task(self, task):
    return self.__add_task(task)

  
  def __process_wait(self):
    return self.__coordinates


  def __process_move(self):
    if len(self.__route) <= 1:
      return self.__coordinates

    current_node = self.__route[0]
    target_node = self.__route[1]
    distance = current_node.get_weight(target_node.id)

    current_domain, current_offset = self.__coordinates.get()

    if current_offset == 0:
      self.__dispatcher.on_domain_leave(self.snapshot, current_domain)
      self.__logger.info(f'Estimated distance to domain {target_node.id}:', distance)

    next_offset = current_offset + self.__speed

    if next_offset >= distance:
      next_domain = target_node.id
      self.__on_domain_reached(next_domain)
      return Coordinates(next_domain, 0)
    else:
      return Coordinates(current_domain, next_offset)      


  def on_timetick(self, timetick):
    if self.current_task is None:
      self.__on_task_changed()

    if self.__state == State.IDLE:
      self.__coordinates = self.__process_wait()
    
    if self.__state == State.MOVING:
      self.__coordinates = self.__process_move()

    self.__logger.info('Coordinates changed:', self.__coordinates.domain, self.__coordinates.offset)

    if self.current_task.completed(self.__coordinates, timetick):
      self.__logger.info('Task completed', f'Current domain: {self.__coordinates.domain}')
      self.__task_stack.pop()
      self.__on_task_changed()




