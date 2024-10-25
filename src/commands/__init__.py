from .admin import commands as admin_commands
from .user import commands as user_commands

commands = [*user_commands, *admin_commands]
