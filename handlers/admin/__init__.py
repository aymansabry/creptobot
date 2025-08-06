from .system_control import register_handlers as register_system_control
from .dashboard import register_handlers as register_dashboard

def register_handlers(dp):
    register_system_control(dp)
    register_dashboard(dp)
