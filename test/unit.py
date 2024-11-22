import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
import unittest

class TestBuffer(unittest.TestCase):
    def send_command(self, cmd):
        proc = subprocess.Popen(['nc', 'localhost', '5000'], 
                              stdin=subprocess.PIPE, 
                              stdout=subprocess.PIPE)
        response = proc.communicate(json.dumps(cmd).encode())[0]
        return json.loads(response.decode()) if response else None

    def test_reset(self):
        self.send_command({"type": "reset"})
        result = self.send_command({"type": "get", "idx": 0})
        self.assertEqual(result["value"], None)


    def test_basic_put_get(self):
        # Basic put/get. Should be None before swap
        self.send_command({"type": "reset"})
        self.send_command({"type": "put", "value": "test0"})
        result = self.send_command({"type": "get", "idx": 0})
        self.assertEqual(result["value"], None)

    def test_buffer_rotation(self):
        # Fill buffer and verify swap
        self.send_command({"type": "reset"})
        for i in range(12):  # Write past buffer size
            self.send_command({"type": "put", "value": f"test{i}"})
        
        # Verify last 10 values
        for i in range(0, 10):
            result = self.send_command({"type": "get", "idx": i})
            print(result["value"])
            self.assertEqual(result["value"], f"test{i}")

    def test_concurrent_writes(self):
        self.send_command({"type": "reset"})
        def write_value(i):
            return self.send_command({"type": "put", "value": f"concurrent{i}"})

        # Concurrent writes
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(write_value, range(20)))

        # Verify values are stored without gaps
        values = set()
        for i in range(10):
            result = self.send_command({"type": "get", "idx": i})
            if result["value"]:
                values.add(result["value"])
        
        self.assertEqual(len(values), 10)  # Buffer should be full
        self.assertTrue(all("concurrent" in v for v in values))

    def test_concurrent_read_write(self):
        self.send_command({"type": "reset"})
        def read_value():
            return self.send_command({"type": "get", "idx": 0})

        def write_value(i):
            return self.send_command({"type": "put", "value": f"mixed{i}"})

        # Concurrent reads and writes
        for i in range(10):
            write_value(i)
        with ThreadPoolExecutor(max_workers=20) as executor:
            reads = [executor.submit(read_value) for _ in range(50)]
            writes = [executor.submit(write_value, i) for i in range(50)]
            
            # Verify all operations complete without errors
            for future in reads + writes:
                result = future.result()
                self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
