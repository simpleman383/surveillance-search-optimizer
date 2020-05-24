from datetime import datetime
import os
from evaluation import experiment_log_path

class EvaluationError(Exception):
  def __init__(self, message):
    self.message = message

class Logger:
  def __init__(self, title, ignore_mode = False):
    self.__title = title
    self.__ignore = ignore_mode

  def __write_to_file(self, data):
    with open(os.path.join(experiment_log_path, f"{self.__title}.txt"), "a") as log_file:
      log_file.write(data + "\n")

  def __write_record(self, record):
    if not self.__ignore:
      self.__write_to_file(record)
      # print(record)

  def __log(self, t, *message):
    record = f"[{datetime.now()}] [{t}] [{self.__title}] : {' '.join([ str(arg) for arg in message ])}"
    self.__write_record(record)


  def info(self, *message):
    self.__log('I', *message)


  def warn(self, *message):
    self.__log('W', *message)


  def error(self, *message):
    self.__log('E', *message)


