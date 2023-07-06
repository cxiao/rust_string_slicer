from binaryninja.log import Logger
from binaryninja.plugin import PluginCommand

from . import actions

logger = Logger(session_id=0, logger_name=__name__)

PLUGIN_NAME = "Rust String Slicer"

plugin_commands = [
    (
        f"{PLUGIN_NAME}\\Recover String Slices from Readonly Data",
        "Recover String Slices from Readonly Data",
        actions.action_recover_string_slices_from_readonly_data,
    )
]


def plugin_init():
    for command_name, command_description, command_action in plugin_commands:
        PluginCommand.register(
            name=command_name, description=command_description, action=command_action
        )
