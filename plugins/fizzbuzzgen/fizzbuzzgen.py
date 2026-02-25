# plugins/fizzbuzzgen/fizzbuzzgen.py
from plugin_manager import AlleyBotPlugin

class FizzBuzzGenPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "fizzbuzzgen"
        self.version = "1.0.0"
    
    def get_commands(self):
        return {
            "fizzbuzz": self.fizzbuzz_command,
        }
    
    def fizzbuzz_command(self, args):
        if not args:
            return "Usage: /fizzbuzz <n> (where n is a positive integer)"
        
        try:
            n = int(args[0])
        except ValueError:
            return f"Error: '{args[0]}' is not a valid integer"
        
        if n <= 0:
            return "Error: n must be a positive integer greater than 0"
        
        if n > 1000:
            return "Error: n is too large (max 1000 for performance)"
        
        result_list = []
        for i in range(1, n + 1):
            if i % 15 == 0:
                result_list.append("FizzBuzz")
            elif i % 3 == 0:
                result_list.append("Fizz")
            elif i % 5 == 0:
                result_list.append("Buzz")
            else:
                result_list.append(str(i))
        
        output = " ".join(result_list)
        
        max_length = 4000
        if len(output) > max_length:
            output = output[:max_length] + "... (truncated)"
        
        return f"FizzBuzz sequence from 1 to {n}:\n{output}"

PLUGIN_INFO = {
    "name": "fizzbuzzgen",
    "version": "1.0.0",
    "description": "Generates FizzBuzz sequences from 1 to n",
    "author": "AlleyBot",
}

def create_plugin(config=None):
    return FizzBuzzGenPlugin(config or {})