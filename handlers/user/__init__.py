from .dashboard import register_handlers as register_dashboard
from .system_control import register_handlers as register_system_control

def register_handlers(dp):
    register_dashboard(dp)
    register_system_control(dp)
