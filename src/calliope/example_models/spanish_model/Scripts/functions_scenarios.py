# ----------------------------
# Imports & constants
# ----------------------------
import calliope
import yaml
import xarray as xr
import pandas as pd
from ruamel.yaml import YAML
from pathlib import Path
from typing import Callable, Literal


_SCENARIO_B_CAP = 0.5  # Scenario B caps china to 50%


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
    """return a list with the technologies containing the keyword"""
    all_techs = dataset.results.flow_cap.coords['techs'].values
    techs = [tech for tech in all_techs if keyword in tech]
    if len(techs) < 1:
        raise KeyError(f"no technologies found with key {keyword}")
    return techs


# ----------------------------
# Cap dictionary builders
# ----------------------------
def _max_cap(data: pd.Series, cap_name: str) -> dict:
    return {
        cap_name: {
            f"techs.{tech}.flow_cap_max": value
            for tech, value in data.items()
        }
    }


def _equals_cap(data: pd.Series, cap_name: str) -> dict:
    return {
        cap_name: {
            **{f"techs.{tech}.flow_cap_max": value for tech, value in data.items()},
            **{f"techs.{tech}.flow_cap_min": value for tech, value in data.items()},
        }
    }


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
    if mode not in CAP_BUILDERS:
        raise ValueError(f"mode must be one of {list(CAP_BUILDERS)}, got {mode!r}")

    with open(overrides_YAML, "r") as f:
        config = yaml.safe_load(f)

    override_dict = CAP_BUILDERS[mode](caps, name)
    config["overrides"].update(override_dict)

    yaml.add_representer(list, repr_inline_list)

    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
    yaml_str = yaml_str.replace(f"{name}:", f'"{name}":', 1)

    with open(out_path, "w") as f:
        f.write(yaml_str)


def build_scenario(overrides_file: str,
                   overrides: list[str],
                   scenario_name: str):
    """
    Append a scenario definition into the YAML file.
    """
    with open(overrides_file, "r") as f:
        config = yaml.safe_load(f)

    _validate_overrides(config, overrides)

    config['scenarios'].update({scenario_name: overrides})

    yaml.add_representer(list, repr_inline_list)

    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    with open(overrides_file, "w") as f:
        f.write(yaml_str)


# ----------------------------
# Domain-level operations
# ----------------------------
def cap_half_china(model: calliope.model.Model,
                   override_yaml: str,
                   out_path: str):
    CN_techs = _extract_country_technologies("_CN", model)
    caps_ = model.results.flow_cap.sel(
        techs=CN_techs, carriers="electricity"
    ).sum("nodes", skipna=True).to_series()

    new_caps = caps_ * _SCENARIO_B_CAP
    _write_cap_override(new_caps, override_yaml, "CHINA_CAP", out_path, mode="max")


def fix_spanish_capacity(model: calliope.model.Model,
                         override_yaml: str,
                         out_path: str):
    ESP_techs = _extract_country_technologies("_ESP", model)
    caps_ = model.results.flow_cap.sel(
        techs=ESP_techs, carriers="electricity"
    ).sum("nodes", skipna=True).to_series()

    _write_cap_override(caps_, override_yaml, "FREEZE_SPANISH_CAPACITY", out_path, "equals")


# ----------------------------
# High-level orchestration
# ----------------------------
def create_scenrio_C(results_file: str,
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
                   ["CHINA_CAP", "FREEZE_SPANISH_CAPACITY", "link_cap_X1"],
                   scenario_name="SCENARIO_C")



if __name__ == "__main__":
    create_scenrio_C(
        r"C:\Users\1496051\PycharmProjects\Calliope_ESP\output.nc",
        r"C:\Users\1496051\PycharmProjects\Calliope_ESP\src\calliope\example_models\spanish_model\overrides.yaml",
        r"C:\Users\1496051\PycharmProjects\Calliope_ESP\src\calliope\example_models\spanish_model\test_override.yaml"
    )
