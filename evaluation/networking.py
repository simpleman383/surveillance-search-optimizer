from abc import ABC, abstractmethod


class Network:
  def __init__(self, receivers):
    self.__receivers = { receiver.id : receiver for receiver in receivers }

  def get_receiver(self, id):
    return self.__receivers[id]

  def send_message(self, src, dest, message):
     receiver = self.get_receiver(dest)
     receiver.on_receive(src, message)

  @staticmethod
  def establish(receivers):
    return Network(receivers)


class Sender:
  def __init__(self, network):
    self.__network = network

  def send(self, src, dest, message):
    self.__network.send_message(src, dest, message)



class Receiver(ABC):
  @property
  @abstractmethod
  def id(self):
    pass

  @abstractmethod
  def on_receive(self, src, message):
    pass


