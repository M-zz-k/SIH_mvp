# Rule Engine module — Person 4's workspace
import importlib.util
import sys
import os

_root_rule_engine_path = os.path.join(os.path.dirname(__file__), "..", "rule_engine.py")
if os.path.exists(_root_rule_engine_path):
    _spec = importlib.util.spec_from_file_location("_root_rule_engine", _root_rule_engine_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    for _attr in dir(_mod):
        if not _attr.startswith("__"):
            globals()[_attr] = getattr(_mod, _attr)

