from .utils import EvaluationError
from abc import ABC, abstractmethod
from enum import Enum
from .routing import Coordinates

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
    self._completed_timetick = timetick + timeout

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
  def __init__(self):
    pass

  def create_task(self, target_object, timetick):
    coords = target_object.coordinates
    dest_coord = Coordinates((coords.domain + 1) % 3)
    return MoveTask(coords, timetick, dest_coord)