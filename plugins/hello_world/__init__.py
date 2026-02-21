from plugin_manager import AlleyBotPlugin

class HelloWorldPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "hello_world"
        self.version = "1.0.0"
    
    def get_commands(self):
        return {
            "hello_world": self.hello_world_command,
        }
    
    def hello_world_command(self, args):
        print("HelloWorldPlugin: hello_world command executed")
        return "Hello World from AlleyBot! 🦞"

PLUGIN_INFO = {
    "name": "hello_world",
    "version": "1.0.0",
    "description": "Simple hello world plugin for testing",
    "author": "AlleyBot",
}

def create_plugin(config=None):
    return HelloWorldPlugin(config or {})