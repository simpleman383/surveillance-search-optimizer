class Coordinates:
  def __init__(self, domain = 0, offset = 0):
    self.domain = domain
    self.offset = offset

  def __eq__(self, other):
    return self.domain == other.domain and self.offset == other.offset

  def get(self):
    return self.domain, self.offset