# ----------------------------
# Imports & constants
# @LexPascal
# Since it is not possible to override math constraints in the current version, the "override" acting on math constraints
# will be conducted through a direct modification of the self defined math file. 
# ----------------------------
import calliope
import yaml
import xarray as xr
import pandas as pd
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq
from pathlib import Path
from typing import Callable, Literal, Dict, List, Union
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logger_config import inter_logs

CUTOFF = 0.001 # MW --> Values below that will be consider numerical dust and therefore 0
_SCENARIO_B_CAP = 0.5  # Scenario B caps china to 50%
_COSTS = ["monetary", "co2", "vul"] # Iterate scenarios over costs
COST_MAPPING = { 
    "monetary" : "monetary_optimization",
    "co2": "emissions_optimization",
    "vul" : "vulnerability_optimization"
} # map costs with overrides


# ----------------------------
# Low-level helpers
# ----------------------------
def repr_inline_list(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


def _validate_overrides(override_file: dict, overrides: list[str]):
    """validate that the passed overrides exist in the YAML file"""
    for item in overrides:
        if item not in override_file['overrides'].keys():
            raise KeyError(f"override {item} not found")


def _extract_country_technologies(keyword: str,
                                  dataset: xr.Dataset) -> list:
    """return a list with the technologies containing the keyword.
    Exclude transmission technologies automatically
    """

    all_techs = dataset.results.flow_cap.coords['techs'].values
    techs = [tech for tech in all_techs 
             if keyword in tech and "transmission" not in tech]
    
    if len(techs) < 1:
        raise KeyError(f"no technologies found with key {keyword}")
    return techs



def _extend_scenarios(scenario_name:str, overrides: list) -> Dict[str, List[str]]:

    scenarios = {}

    for k,v in COST_MAPPING.items():
        override_list=overrides + [v]
        scenarios[f"{scenario_name}_{k}"] = override_list 
    
    inter_logs.debug(f"Extended scenarios: {scenarios}")
    return scenarios
    
# ----------------------------
# Cap dictionary builders
# ----------------------------
def _max_cap(data: pd.Series, cap_name: str) -> List[str]:
    """
    Convert pd.Series indexed by (node,tech) into a dot notation lines (override-like format)
    Define max capacity

    """
    overrides: Dict[str, Dict[str, Union[int, float]]] = {cap_name: {}}

    for (node, tech), val in data.items():
        key = f"nodes.{node}.techs.{tech}.flow_cap_max"
        overrides[cap_name][key] = float(val)

    return overrides


def _equals_cap(data: pd.Series, cap_name: str) -> dict:
    """
    Convert pd.Series indexed by (node,tech) into a dot notation lines (override-like format)
    Define equal capacity
    """
    

    overrides: Dict[str, Dict[str, Union[int, float]]] = {cap_name: {}}

    for (node, tech), val in data.items():
        overrides[cap_name][f"nodes.{node}.techs.{tech}.flow_cap_max"] = float(val)
        overrides[cap_name][f"nodes.{node}.techs.{tech}.flow_cap_min"] = float(val)

    return overrides



CAP_BUILDERS: dict[str, Callable[[pd.Series, str], dict]] = {
    "max": _max_cap,
    "equals": _equals_cap,
}


# ----------------------------
# I/O: read & write YAML
# ----------------------------
def _write_cap_override(caps: pd.Series,
                        overrides_YAML: str,
                        name: str,
                        out_path: str,
                        mode: Literal["max", "equals"] = "max"
                        ) -> None:
    """
    Write a capacity override into a YAML file.
    """
    inter_logs.info(f"Started writing caps...")
    
    caps[caps < CUTOFF] = 0.0  # FLAG: NUMERICAL DUST

    if mode not in CAP_BUILDERS:
        raise ValueError(f"mode must be one of {list(CAP_BUILDERS)}, got {mode!r}")

    with open(overrides_YAML, "r") as f:
        config = yaml.safe_load(f)

    override_dict = CAP_BUILDERS[mode](caps, name)
    config["overrides"].update(override_dict) #TODO: FIX HERE

    yaml.add_representer(list, repr_inline_list)

    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
    yaml_str = yaml_str.replace(f"{name}:", f'"{name}":', 1)

    with open(out_path, "w") as f:
        f.write(yaml_str)
    
    inter_logs.debug(f"Caps applied: {override_dict}")
    inter_logs.info(f"Finished writing caps...")



def build_scenario(overrides_file: str,
                   overrides: list[str],
                   scenario_name: str):
    """
    Append a scenario definition into the YAML file.
    The scenario will be triplicated according to the costs:
    scenario_name_{cost}, including in each single optimization weights
    """
    """
    Append a scenario definition into the YAML file.
    The scenario will be triplicated according to the costs:
    scenario_name_{cost}, including in each single optimization weights
    """
    inter_logs.info(f"Building scenario {scenario_name}")

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.sort_keys = False

    with open(overrides_file, "r") as f:
        config = yaml.load(f)

    _validate_overrides(config, overrides)
    scenarios = _extend_scenarios(scenario_name, overrides)

    # Convert each list to flow-style sequence
    for k, v in scenarios.items():
        seq = CommentedSeq(v)
        seq.fa.set_flow_style()   # force inline
        scenarios[k] = seq

    config['scenarios'].update(scenarios)

    with open(overrides_file, "w") as f:
        yaml.dump(config, f)

    # Debugging
    inter_logs.debug(f"Scenario construction for {scenario_name}: {scenarios}")
    inter_logs.debug(f"Scenarios section after update:\n{config['scenarios']}")
    inter_logs.debug(f"Scenario written in: {os.path.abspath(overrides_file)}")

# ----------------------------
# Domain-level operations
# ----------------------------
def restore_european_capacity(math_yaml: str) -> None:
    """
    This function deactivates a predefined constraint defined in math.yaml
    It directly modifies the file as overrides over math are not allowed
    """
    yaml = YAML()
    yaml.preserve_quotes = True  

    with open(math_yaml, "r") as f:
        config = yaml.load(f)

    
    config["constraints"]["european_capacity_share_cap"]["active"] = False

    inter_logs.info(
        f"Math yaml has been updated {config['constraints']['european_capacity_share_cap']}"
    )

    with open(math_yaml, "w") as f:
        yaml.dump(config, f)  


def fix_european_capacity(math_yaml: str) -> None:
    """
    This function activates a predefined constraint defined in math.yaml
    It directly modifies the file as overrides over math are not allowed
    """
    yaml = YAML()
    yaml.preserve_quotes = True  

    with open(math_yaml, "r") as f:
        config = yaml.load(f)

    
    config["constraints"]["european_capacity_share_cap"]["active"] = True

    inter_logs.info(
        f"Math yaml has been updated {config['constraints']['european_capacity_share_cap']}"
    )

    with open(math_yaml, "w") as f:
        yaml.dump(config, f)   


def cap_half_china(model: calliope.model.Model,
                   override_yaml: str,
                   out_path: str):
    CN_techs = _extract_country_technologies("_CN", model)
    
    
    caps_ = model.results.flow_cap.sel(
        techs=CN_techs, carriers="electricity"
    ).to_series().dropna()

    new_caps = caps_ * _SCENARIO_B_CAP
    _write_cap_override(new_caps, override_yaml, "CHINA_CAP", out_path, mode="max")

    inter_logs.debug(f"technologies filtered: {CN_techs}")
    inter_logs.debug(f"caps passed for CN techs: {caps_}")


def fix_spanish_capacity(model: calliope.model.Model,
                         override_yaml: str,
                         out_path: str):
    inter_logs.info("starting fix spanish capacity")
    
    ESP_techs = _extract_country_technologies("_ESP", model)
    caps_ = model.results.flow_cap.sel(
        techs=ESP_techs, carriers="electricity"
    ).to_series().dropna()

    _write_cap_override(caps_, override_yaml, "FREEZE_SPANISH_CAPACITY", out_path, "max")

    inter_logs.debug(f"technologies filtered: {ESP_techs}")
    inter_logs.debug(f"caps passed for spanish techs: {caps_}")




# ----------------------------
# High-level orchestration
# ----------------------------

def create_scenario_A():
    """
    General call to create scenario A
    """
    inter_logs.info(f"running function {create_scenario_A.__name__}:")
    build_scenario(
        overrides_file="overrides.yaml",
        overrides=["link_cap_X1"],
        scenario_name="scenario_A"
    )

    inter_logs.info(f"scenario A created")



def create_scenario_B(results_file: str,
                      override_yaml: str,
                      new_override: str):
    """
    General call for scenario B
    * results_file: path to the nc files from scenario A
    * override_yaml: path to the overrides.yaml
    * new_override: path to the new override file
    """
    inter_logs.info(f"running function {create_scenario_B.__name__}:")
    inter_logs.info(f"Reading {results_file} and {override_yaml}")

    path_results = Path(results_file)

    model = calliope.read_netcdf(path_results)

    fix_spanish_capacity(model, override_yaml, new_override)

    build_scenario(new_override,
                   ["cap_russia", "exclude_spanish_diversity","FREEZE_SPANISH_CAPACITY", "link_cap_X1"],
                   scenario_name="scenario_B")
    



def create_scenario_C(results_file: str,
                     override_yaml: str,
                     new_override: str):
    """
    General call for scenario C.
    """
    path_results = Path(results_file)
    model = calliope.read_netcdf(path_results)

    cap_half_china(model, override_yaml, new_override)
    fix_spanish_capacity(model, new_override, new_override)

    build_scenario(new_override,
                   ["cap_russia", "CHINA_CAP", "exclude_spanish_diversity", "FREEZE_SPANISH_CAPACITY", "link_cap_X1"],
                   scenario_name="scenario_C")


def create_scenario_D(math_yaml: str,
                      override_yaml: str):
    """
    General call for scenario D
    """
    fix_european_capacity(math_yaml)
    build_scenario(override_yaml,
                   ["link_cap_X1"],
                   scenario_name="scenario_D")
    

def create_scenario_E(override_yaml: str):
    """
    General call for scenario D
    """
    #fix_european_capacity(math_yaml) --> previously activated in D
    build_scenario(override_yaml,
                   ["link_cap_X1", "cap_russia"],
                   scenario_name="scenario_E")
    


