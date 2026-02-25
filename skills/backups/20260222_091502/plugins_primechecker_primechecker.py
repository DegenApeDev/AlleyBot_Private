from plugin_manager import AlleyBotPlugin
import math

class PrimeCheckerPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "primechecker"
        self.version = "1.0.0"
    
    def get_commands(self):
        return {
            "fizzbuzz": self.fizzbuzz_command,
        }
    
    def fizzbuzz_command(self, args):
        if len(args) != 1:
            return "Usage: fizzbuzz <positive integer>"
        
        try:
            n = int(args[0])
            if n <= 0:
                return "Error: Please provide a positive integer greater than 0"
        except ValueError:
            return "Error: Invalid integer provided"
        
        if n == 1:
            return "Not prime, factors: "
        
        is_prime_result, factors = self.is_prime_with_factors(n)
        
        if is_prime_result:
            return "Prime!"
        else:
            factor_str = ", ".join(str(f) for f in factors)
            return f"Not prime, factors: {factor_str}"
    
    def is_prime_with_factors(self, n):
        original_n = n
        factors = []
        
        while n % 2 == 0:
            factors.append(2)
            n //= 2
        
        limit = int(math.isqrt(n))
        for i in range(3, limit + 1, 2):
            while n % i == 0:
                factors.append(i)
                n //= i
        
        if n > 2:
            factors.append(n)
        
        if len(factors) == 1 and factors[0] == original_n:
            return True, []
        
        unique_factors = []
        seen = set()
        for f in factors:
            if f not in seen:
                unique_factors.append(f)
                seen.add(f)
        
        return False, sorted(unique_factors)

PLUGIN_INFO = {
    "name": "primechecker",
    "version": "1.0.0",
    "description": "Check if numbers are prime and find prime factors",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return PrimeCheckerPlugin(config or {})