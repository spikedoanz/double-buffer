from typing import Optional, List
import threading
from dataclasses import dataclass
import socket
import json

VERBOSE = True # print out logs

@dataclass
class Buffer:
  size: int
  idx: int = 0
  write: List[Optional[str]] = None
  read: List[Optional[str]] = None
  _swap_lock: threading.Lock = None
  _idx_lock: threading.Lock = None

  def __post_init__(self):
    self.write = [None] * self.size
    self.read = [None] * self.size
    self._swap_lock = threading.Lock()
    self._idx_lock = threading.Lock()

  def put(self, data: str) -> None:
    with self._idx_lock:
      idx = self.idx  
      self.write[idx] = data
      self.idx += 1
      if self.idx >= self.size:
        with self._swap_lock:
          self.write, self.read = self.read, self.write
          self.idx = 0
          self.write = [None] * self.size
          if VERBOSE:
            print("SWAPPED!")

  def get(self, idx: int) -> Optional[str]:
    return self.read[idx % self.size]

  def reset(self):
    with self._swap_lock:
      with self._idx_lock:
        self.write = [None] * self.size
        self.read = [None] * self.size
        self._swap_lock = threading.Lock()
        self._idx_lock = threading.Lock()
        self.idx = 0


def handle_client(conn, buffer):
  while True:
    try:
      data = conn.recv(1024).decode()
      if not data:
        break
      cmd = json.loads(data)
      
      if cmd["type"] == "put":
        buffer.put(cmd["value"])
        conn.send(json.dumps({"status": "ok"}).encode())
        if VERBOSE:
          print(f"PUT'ed {cmd["value"]}")
      
      elif cmd["type"] == "get":
        value = buffer.get(int(cmd["idx"]))
        conn.send(json.dumps({"value": value}).encode())
        if VERBOSE:
          print(f"GET'ed {value}")

      elif cmd["type"] == "reset":
        buffer.reset()
        conn.send(json.dumps({"status": "ok"}).encode())
        if VERBOSE:
          print("Reset buffer successfully")

    except Exception as e:
      print(f"Error: {e}")
      break
  conn.close()

if __name__ == "__main__":
  buffer = Buffer(size=10)
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind(('0.0.0.0', 5000))
  server.listen(5)
  print("Double buffer is alive on port 5000!")

  while True:
    conn, addr = server.accept()
    thread = threading.Thread(
        target=handle_client, args=(conn, buffer))
    thread.start()
