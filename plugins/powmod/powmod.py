from plugin_manager import AlleyBotPlugin

class PowModPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "powmod"
        self.version = "1.0.0"
    
    def get_commands(self):
        return {
            "powmod": self.powmod_command,
        }
    
    def powmod_command(self, args):
        if len(args) != 3:
            return "Error: powmod requires exactly 3 positive integers: a b m"
        
        try:
            a = int(args[0])
            b = int(args[1])
            m = int(args[2])
        except ValueError:
            return "Error: all arguments must be positive integers"
        
        if a <= 0 or b <= 0 or m <= 0:
            return "Error: all arguments must be positive integers"
        
        result = 1
        base = a % m
        exponent = b
        
        while exponent > 0:
            if exponent % 2 == 1:
                result = (result * base) % m
            base = (base * base) % m
            exponent //= 2
        
        return str(result)

PLUGIN_INFO = {
    "name": "powmod",
    "version": "1.0.0",
    "description": "Modular exponentiation: compute a^b mod m efficiently",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return PowModPlugin(config or {})