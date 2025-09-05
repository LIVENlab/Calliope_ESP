import calliope
import yaml
import xarray as xr
import pandas as pd


_SCENARIO_B_CAP = 0.5  # Scenario B caps china to 50%


# Functions to extract data

def cap_half_china(
        results_file: str,
        override_yaml:str):
    model = calliope.read_netcdf(results_file)
    CN_techs= _extract_CN_technologies(model)
    pass

    
    caps_ = model.results.flow_cap.sel(techs=CN_techs,
                                     carriers="electricity").sum("nodes", skipna=True).to_series()

    new_caps= caps_ * _SCENARIO_B_CAP # Apply the scenario B cap here!



def _extract_CN_technologies(dataset: xr.Dataset)-> list:
    """
    return a list of the CN technologies
    """
    all_techs=dataset.results.flow_cap.coords['techs'].values
    return [tech for tech in all_techs if "_CN" in tech]

    
cap_half_china(r"C:\Users\1496051\PycharmProjects\Calliope_ESP\output.nc",
               r"C:\Users\1496051\PycharmProjects\Calliope_ESP\src\calliope\example_models\spanish_model\overrides.yaml")



# functions to write data
def write_china_cap_override(caps:pd.Series, overrides_YAML: yaml):

    with open(overrides_YAML, "r") as f:
        data = yaml.safe_load(f)
    
    override_dict= {
        "CHINESE_CAP": {
            f"techs.{tech}.flow_cap_max": value for tech,value in caps.items()
        }
    }
    pass
