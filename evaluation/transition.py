import random as rnd
import numpy as np
import math
from enum import Enum
from abc import ABC, abstractmethod

# Group sizes: binomial/geometric/plain
# Transition probabilities: plain/geometric - monopolar/geometric - multipolar 


class GroupType(Enum):
  PLAIN = 0,
  BINOMIAL = 1,
  GEOMETRIC = 2



class GroupSizeGenerator(ABC):
  def __init__(self, min, max):
    self._min = min
    self._max = max

  @abstractmethod
  def get_samples(self, count):
    pass


class PlainGroupSizeGenerator(GroupSizeGenerator):
  def __init__(self, min, max):
      super().__init__(min, max)

  def get_samples(self, count):
    return [ rnd.randint(self._min, self._max) for _ in range(count) ]


class BinomialGroupSizeGenerator(GroupSizeGenerator):
  def __init__(self, min, max, p):
    self._p = p
    super().__init__(min, max)


  def get_samples(self, count):
    return np.random.binomial(self._max, self._p, size=count)


class GeometricGroupSizeGenerator(GroupSizeGenerator):
  def __init__(self, min, max, p):
    self._p = p
    super().__init__(min, max)

  def get_samples(self, count):
    res = []
    while len(res) < count:
      candidate = np.random.geometric(self._p, 1)[0]
      if self._min <= candidate and candidate <= self._max:
        res.append(candidate)
    return res



class TransitionType(Enum):
  PLAIN = 0,
  GEOMETRIC_MONOPOLAR = 1,
  GEOMETRIC_MULTIPOLAR = 2


class TransitionError(Exception):
  def __init__(self, message):
    self.message = message


class TransitionMatrix:
  def __init__(self, keys):
    self.__data = { src: { dest: 0 for dest in keys } for src in keys }

  def __check_keys(self, src, dest):
    if src not in self.__data.keys():
      raise TransitionError(f"src={src} is not in transition matrix")

    if dest not in self.__data[src].keys():
      raise TransitionError(f"dest={dest} is not in transition matrix")

    return True


  def set_transition_probability(self, src, dest, value):
    if self.__check_keys(src, dest):
      self.__data[src][dest] = value

    return self

  
  def get_transition_probabilty(self, src, dest):
    if self.__check_keys(src, dest):
      return self.__data[src][dest]
    else:
      return 0

  def __str__(self):
    body = "\n".join([ f"{src}: {[ f'{str(dest)}: {str(self.__data[src][dest])}' for dest in self.__data[src].keys() ]}" for src in self.__data.keys() ])
    return f"\n{{\n{body}\n}}\n"


  def __repr__(self):
    return self.__str__()
      

  


class TransitionGenerator:
  def __init__(self, max_group, transition_gen_type=TransitionType.PLAIN, group_gen_type=GroupType.PLAIN, min_group=1, group_p=0.5, transition_q=0.5):
    self.__transition_type = transition_gen_type
    self.__transition_geom_q = transition_q
    self.__group_generator = self.__init_group_generator(group_gen_type, min_group, max_group, group_p)
    self.__elements = [ i for i in range(max_group) ]
    rnd.shuffle(self.__elements)


  def __init_group_generator(self, group_gen_type, min, max, p):
    if group_gen_type == GroupType.BINOMIAL:
      return BinomialGroupSizeGenerator(min, max, p)
    elif group_gen_type == GroupType.GEOMETRIC:
      return GeometricGroupSizeGenerator(min, max, p)
    else:
      return PlainGroupSizeGenerator(min, max)


  def __generate_probability_row_monopolar(self, src, destinations):
    q = self.__transition_geom_q
    n = len(destinations)
    base = (1 - q) / (1 - math.pow(q, n))
    probabilities = [ base * math.pow(q, i) for i in range(n) ]
    return { destinations[i] : probabilities[i] for i in range(n) }

  def __generate_probability_row_multipolar(self, src, destinations, shift):
    q = self.__transition_geom_q
    n = len(destinations)
    base = (1 - q) / (1 - math.pow(q, n))
    probabilities = [ base * math.pow(q, i) for i in range(n) ]
    probabilities = probabilities[shift:] + probabilities[:shift]
    return { destinations[i] : probabilities[i] for i in range(n) }


  def __generate_probability_row(self, src, destinations, shift=0):

    if self.__transition_type == TransitionType.GEOMETRIC_MONOPOLAR:
      return self.__generate_probability_row_monopolar(src, destinations)

    if self.__transition_type == TransitionType.GEOMETRIC_MULTIPOLAR:
      return self.__generate_probability_row_multipolar(src, destinations, shift)

    if self.__transition_type == TransitionType.PLAIN:
      return { dest: 1/len(destinations) for dest in destinations }

    return []


  def get_samples(self, count):
    group_sizes = self.__group_generator.get_samples(count)

    matrices = []

    for idx in range(count):
      group_size = group_sizes[idx]
      group = self.__elements[0: group_size]
      rnd.shuffle(group)

      transition_matrix = TransitionMatrix(group)

      row_counter = 0
      for src in group:
        probabilities = self.__generate_probability_row(src, destinations=group, shift=-row_counter)
        row_counter += 1
        for dest in probabilities.keys():
          prob = probabilities[dest]
          transition_matrix.set_transition_probability(src, dest, prob)

      matrices.append(transition_matrix)
  
    return matrices

