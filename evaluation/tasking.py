from .utils import EvaluationError
from abc import ABC, abstractmethod
from enum import Enum
from .coordinate import Coordinates
import random
import numpy as np

class TaskType(Enum):
  WAIT = 0
  MOVE = 1


class Task(ABC):
  def __init__(self, coordinates, timetick):
    self._start_coordinates = coordinates
    self._start_timetick = timetick
    self._type = None

  @property
  def category(self):
    return self._type

  @abstractmethod
  def completed(self, coordinates, timetick):
    pass


class WaitTask(Task):
  def __init__(self, coordinates, timetick, timeout):
    super().__init__(coordinates, timetick)
    self._type = TaskType.WAIT
    self._timeout = timeout
    self._completed_timetick = timetick + timeout

  @property
  def timeout(self):
    return self._timeout

  def completed(self, coordinates, timetick):
    return timetick >= self._completed_timetick


class MoveTask(Task):
  def __init__(self, coordinates, timetick, destination_coordinates):
    super().__init__(coordinates, timetick)
    self._type = TaskType.MOVE
    self._target = destination_coordinates

  @property
  def destination(self):
    return self._target

  def completed(self, coordinates, timetick):
    return self._target == coordinates





class TaskStack:
  def __init__(self):
    self.__stack = []

  @property
  def current(self):
    if len(self.__stack) > 0:
      return self.__stack[len(self.__stack) - 1]
    else:
      return None

  def push(self, task):
    if task is None:
      raise EvaluationError('Task can not be of type None')
    else:
      self.__stack.append(task)

  def pop(self):
    if len(self.__stack) > 0:
      task = self.__stack.pop()
      return task
    else:
      raise EvaluationError('Failed to pop: task stack is empty')



class TaskGenerator:
  def __init__(self, graph, transitions, moving_degree=0.5, max_await=10):
    self.__graph = graph
    self.__transitions = transitions
    
    self.__moving_degree = moving_degree
    self.__max_await_time = max_await


  def __generate_destination(self, current_domain_id, object_id):
    transition_matrix = self.__transitions[object_id]

    destinations = transition_matrix.possible_destinations

    point = random.random()
    acc = 0
    idx = 0
    target_dest_id = None

    while point > acc:
      target_dest_id = destinations[idx]
      acc += transition_matrix.get_transition_probabilty(current_domain_id, target_dest_id)
      idx += 1

    return target_dest_id


  def create_task(self, object_snapshot, timetick):
    next_task_type = np.random.binomial(1, self.__moving_degree, 1)[0]

    if next_task_type == TaskType.MOVE.value:
      target_dest_id = self.__generate_destination(object_snapshot.coordinates.domain, object_snapshot.id)
      dest_coord = Coordinates(target_dest_id)
      return MoveTask(object_snapshot.coordinates, timetick, dest_coord)


    return WaitTask(object_snapshot.coordinates, timetick, random.randint(1, self.__max_await_time))