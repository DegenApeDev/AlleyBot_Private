from plugin_manager import AlleyBotPlugin

class ModInversePlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "mod_inverse"
        self.version = "1.0.0"
    
    def get_commands(self):
        return {
            "mod_inverse": self.mod_inverse_command,
        }
    
    def mod_inverse_command(self, args):
        if len(args) != 2:
            return "Error: Requires exactly two arguments 'a m'"
        
        try:
            a = int(args[0])
            m = int(args[1])
        except ValueError:
            return "Error: Both arguments must be integers"
        
        if m <= 0:
            return "Error: Modulus m must be positive"
        
        # Extended Euclidean algorithm (iterative)
        t, new_t = 0, 1
        r, new_r = m, a % m
        
        while new_r != 0:
            quotient = r // new_r
            t, new_t = new_t, t - quotient * new_t
            r, new_r = new_r, r - quotient * new_r
        
        if r > 1:
            return f"Error: No modular inverse exists (gcd({a}, {m}) != 1)"
        
        if t < 0:
            t += m
        
        return str(t)

PLUGIN_INFO = {
    "name": "mod_inverse",
    "version": "1.0.0",
    "description": "Compute modular inverse using extended Euclidean algorithm",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return ModInversePlugin(config or {})