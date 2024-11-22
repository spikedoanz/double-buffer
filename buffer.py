from typing import Optional, List
import threading
from dataclasses import dataclass
import time

@dataclass
class Buffer:
  size: int
  idx : int = 0
  write: List[Optional[str]] = None
  read : List[Optional[str]] = None 
  _swap_lock: threading.Lock = None
  _idx_lock : threading.Lock = None

  def __post_init__(self):
    self.write = [None] * self.size
    self.read  = [None] * self.size
    self._swap_lock = threading.Lock()
    self._idx_lock= threading.Lock()

  def put(self, data:str) -> None:
    with self._idx_lock:
      idx = self.idx
      self.write[idx] = data
      self.idx += 1
      if self.write_idx >= self.size:
        with self._swap_lock:
          self.write, self.read = self.read, self.write
          self.idx = 0
          self.write = [None] * self.size

    def get(self, idx: int) -> Optional[str]:
      return self.read[idx % self.size]

if __name__ == "__main__":
  double_buffer = Buffer(size=1000)
  print("Double buffer is alive!")
  while True:
    time.sleep(0.1)
