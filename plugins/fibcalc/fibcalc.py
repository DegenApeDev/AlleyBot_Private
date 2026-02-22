from plugin_manager import AlleyBotPlugin

class FibCalcPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "fibcalc"
        self.version = "1.0.0"
    
    def get_commands(self):
        return {
            "run fib": self.run_fib,
        }
    
    def fib(self, n):
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def run_fib(self, args):
        if not args:
            return "Usage: run fib <n> (n must be a non-negative integer)"
        
        try:
            n = int(args[0])
            if n < 0:
                return f"Error: Fibonacci sequence is defined for non-negative integers only. Got: {n}"
            
            result = self.fib(n)
            return f"fib({n}) = {result}"
        
        except ValueError:
            return f"Error: '{args[0]}' is not a valid integer"

PLUGIN_INFO = {
    "name": "fibcalc",
    "version": "1.0.0",
    "description": "Computes nth Fibonacci number using iterative algorithm",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return FibCalcPlugin(config or {})