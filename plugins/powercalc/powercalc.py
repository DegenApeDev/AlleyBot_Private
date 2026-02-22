from plugin_manager import AlleyBotPlugin

class PowerCalcPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "powercalc"
        self.version = "1.0.0"
    
    def get_commands(self):
        return {
            "power": self.calculate_power,
        }
    
    def calculate_power(self, args):
        if len(args) != 2:
            return "Error: power command requires exactly two positive integers (a b)"
        
        try:
            a = int(args[0])
            b = int(args[1])
            
            if a < 0 or b < 0:
                return "Error: both numbers must be positive integers"
            
            result = 1
            for _ in range(b):
                result *= a
            
            return f"{a}^{b} = {result}"
        except ValueError:
            return "Error: both arguments must be integers"

PLUGIN_INFO = {
    "name": "powercalc",
    "version": "1.0.0",
    "description": "Calculate a^b using pure Python iterative multiplication",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return PowerCalcPlugin(config or {})