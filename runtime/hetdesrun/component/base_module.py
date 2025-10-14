import sys
from types import ModuleType

base_module_path = "hetdesrun_loaded_components"

# Register base_module_path. This is necessary in order for serialization
# to work with custom classes in user components.
#
# Note: As long as base_module_path is not configurable and only has one
# level we do not need to recursively register modules:
sys.modules[base_module_path] = ModuleType(base_module_path, "base module")
