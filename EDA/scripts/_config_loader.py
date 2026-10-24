"""
_config_loader.py
=================
Internal helper – loads 00_config.py and re-exports all constants.
REASON: Python cannot directly import modules whose names start with a digit.
        This shim provides a clean import for all EDA scripts.
"""
import os
from importlib.util import spec_from_file_location, module_from_spec

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = spec_from_file_location("_cfg", os.path.join(_HERE, "00_config.py"))
_cfg  = module_from_spec(_spec)
_spec.loader.exec_module(_cfg)

# Re-export everything
DATA_PATH       = _cfg.DATA_PATH
OUT_FIG         = _cfg.OUT_FIG
OUT_REP         = _cfg.OUT_REP
DEPRESSION_QS   = _cfg.DEPRESSION_QS
ANXIETY_QS      = _cfg.ANXIETY_QS
STRESS_QS       = _cfg.STRESS_QS
SEVERITY        = _cfg.SEVERITY
PALETTE         = _cfg.PALETTE
FIG_DPI         = _cfg.FIG_DPI
FIG_SIZE        = _cfg.FIG_SIZE
VCL_FAKE        = _cfg.VCL_FAKE
GENDER_MAP      = _cfg.GENDER_MAP
EDUCATION_MAP   = _cfg.EDUCATION_MAP
URBAN_MAP       = _cfg.URBAN_MAP
HAND_MAP        = _cfg.HAND_MAP
ENGNAT_MAP      = _cfg.ENGNAT_MAP
MARRIED_MAP     = _cfg.MARRIED_MAP
ORIENTATION_MAP = _cfg.ORIENTATION_MAP
