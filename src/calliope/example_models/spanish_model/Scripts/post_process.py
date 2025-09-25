"""
@LexPascal
This script post-processes the results of a Calliope model run for a Spanish energy system.
"""

import pandas as pd
import os

european_techs_list =  [
    "battery_CZ",
    "battery_ESP",
    "battery_HU",
    "battery_PL",
    "biogas_to_electricity_supply_BEL",
    "biogas_to_electricity_supply_FR",
    "biomass_ESP",
    "biomass_FR",
    "biomass_IT",
    "open_field_pv_DE",
    "open_field_pv_ESP",
    "open_field_pv_NL",
    "open_field_pv_PT",
    "pumped_hydro_ESP",
    "roof_mounted_pv_DE",
    "roof_mounted_pv_ESP",
    "roof_mounted_pv_NL",
    "roof_mounted_pv_PT",
    "wind_offshore_DE",
    "wind_offshore_ESP",
    "wind_offshore_FR",
    "wind_offshore_NDL",
    "wind_offshore_PT",
    "wind_onshore_competing_DE",
    "wind_onshore_competing_ESP",
    "wind_onshore_competing_FR",
    "wind_onshore_competing_NDL",
    "wind_onshore_competing_PT",
    "wind_onshore_monopoly_DE",
    "wind_onshore_monopoly_ESP",
    "wind_onshore_monopoly_FR",
    "wind_onshore_monopoly_NDL",
    "wind_onshore_monopoly_PT"
]


existing_techs_list= [
    "existing_biogas_to_electricity_supply",
    "existing_biomass",
    "existing_ccgt",
    "existing_chp",
    "existing_coal",
    "existing_hydro_reservoir",
    "existing_hydro_run_of_river",
    "existing_nuclear",
    "existing_oil_and_other",
    "existing_open_field_pv",
    "existing_pumped_hydro",
    "existing_rooftop_pv",
    "existing_wind_onshore",
    "existing_wte"
]


def read_csv_to_dataframe(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)

def new_path(original_path: str, new_filename: str) -> str:
    directory = os.path.dirname(original_path)
    return os.path.join(directory, new_filename)

def rename_flow_out_columns(df: pd.DataFrame,
                            new_filename: str,
                            scenario_name: str) -> pd.DataFrame:
    """
    Sparks expects to name the flow_out column as the name of the file
    - It also expects locs instead of nodes
    """
    new_col_name = f"{scenario_name}_{new_filename}"
    df = df.rename(columns={'flow_out': new_col_name, 'nodes': 'locs'})
    return df, new_col_name

def flow_out_sum(path: str,
                 scenario_name: str,
                 output_name='results_flow_out_sum') -> None:
    """
    Pass the path to the flow_out.csv file to this function
    Returns the sum of all flow_out values for the time period per technology and location
    Don't pass the extension, it will be added automatically
    """
    data = read_csv_to_dataframe(path)
    data = data.drop(columns=['timesteps'])
    # Exclude transmission technologies from all computations
    data = data[~data['techs'].str.contains('transmission|liquid', case=False, na=False)]
    # Group by the relevant columns and sum 'flow_out'
    result = data.groupby(['nodes', 'techs', 'carriers'], as_index=False)['flow_out'].sum()
    # Optionally rename the flow_out column
    check_node_production(result)
    check_uranium_production(result, path)
    check_coal_production(result, path)
    check_natural_gas_production(result, path)
    check_oil_production(result, path)
    check_coal_production(result, path)
    result, _ = rename_flow_out_columns(result, output_name, scenario_name)
    
    # Save to CSV
    _ = f"{_}.csv"
    output_path = new_path(path, _)
    result.to_csv(output_path, index=False)



def check_uranium_production(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the uranium production is greater than the uranium demand
    """
    uranium_df = df[df['carriers'].str.contains('ranium', case=False, na=False)].copy()
    uranium_df = uranium_df[~uranium_df['techs'].str.contains('transmission', case=False, na=False)]
    if uranium_df.empty:
        print("No rows found with carriers matching 'uranium'. Skipping share calculation.")
        return

    by_tech = (
        uranium_df.groupby(['techs'], as_index=False)['flow_out']
        .sum()
        .rename(columns={'flow_out': 'uranium_flow_out'})
    )

    total_uranium = by_tech['uranium_flow_out'].sum()
    if total_uranium == 0:
        print("Total uranium production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['uranium_flow_out'] / total_uranium) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Uranium production share by technology (% of total):")
    print(by_tech.to_string(index=False))


def check_coal_production(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the coal production is greater than the coal demand
    """
    coal_df = df[df['carriers'].str.contains('coal', case=False, na=False)].copy()
    coal_df = coal_df[~coal_df['techs'].str.contains('transmission', case=False, na=False)]
    if coal_df.empty:
        print("No rows found with carriers matching 'coal'. Skipping share calculation.")
        return

    by_tech = (
        coal_df.groupby(['techs'], as_index=False)['flow_out']
        .sum()
        .rename(columns={'flow_out': 'coal_flow_out'})
    )

    total_coal = by_tech['coal_flow_out'].sum()
    if total_coal == 0:
        print("Total coal production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['coal_flow_out'] / total_coal) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Coal production share by technology (% of total):")
    print(by_tech.to_string(index=False))


def check_natural_gas_production(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the natural gas production is greater than the natural gas demand
    """
    natural_gas_df = df[df['carriers'].str.contains('natural_gas', case=False, na=False)].copy()
    natural_gas_df = natural_gas_df[~natural_gas_df['techs'].str.contains('transmission', case=False, na=False)]
    if natural_gas_df.empty:
        print("No rows found with carriers matching 'natural_gas'. Skipping share calculation.")
        return

    by_tech = (
        natural_gas_df.groupby(['techs'], as_index=False)['flow_out']
        .sum()
        .rename(columns={'flow_out': 'natural_gas_flow_out'})
    )

    total_natural_gas = by_tech['natural_gas_flow_out'].sum()
    if total_natural_gas == 0:
        print("Total natural gas production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['natural_gas_flow_out'] / total_natural_gas) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Natural gas production share by technology (% of total):")
    print(by_tech.to_string(index=False))


def check_oil_production(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the oil production is greater than the oil demand
    """
    oil_df = df[df['carriers'].str.contains('oil', case=False, na=False)].copy()
    oil_df = oil_df[~oil_df['techs'].str.contains('transmission', case=False, na=False)]
    if oil_df.empty:
        print("No rows found with carriers matching 'oil'. Skipping share calculation.")
        return

    by_tech = (
        oil_df.groupby(['techs'], as_index=False)['flow_out']
        .sum()
        .rename(columns={'flow_out': 'oil_flow_out'})
    )

    total_oil = by_tech['oil_flow_out'].sum()
    if total_oil == 0:
        print("Total oil production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['oil_flow_out'] / total_oil) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Oil production share by technology (% of total):")
    print(by_tech.to_string(index=False))

def check_open_field_pv_capacities(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the open field PV production is greater than the open field PV demand
    """
   #open_field_pv_df = df[df['carriers'].str.contains('electricity', case=False, na=False)].copy()
    open_field_pv_df = df[df['techs'].str.contains('open_field_pv', case=False, na=False)]
    open_field_pv_df = open_field_pv_df[~open_field_pv_df['techs'].str.contains('transmission|existing', case=False, na=False)]
    if open_field_pv_df.empty:
        print("No rows found with carriers matching 'open_field_pv'. Skipping share calculation.")
        return

    by_tech = (
        open_field_pv_df.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
        .rename(columns={'flow_cap': 'open_field_pv_flow_cap'})
    )

    total_open_field_pv = by_tech['open_field_pv_flow_cap'].sum()
    if total_open_field_pv == 0:
        print("Total open field PV production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['open_field_pv_flow_cap'] / total_open_field_pv) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Open field PV production share by technology (% of total):")
    print(by_tech.to_string(index=False))


def check_rooftop_capacities(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the rooftop production is greater than the open field PV demand
    """
   #open_field_pv_df = df[df['carriers'].str.contains('electricity', case=False, na=False)].copy()
    open_field_pv_df = df[df['techs'].str.contains('rooftop', case=False, na=False)]
    open_field_pv_df = open_field_pv_df[~open_field_pv_df['techs'].str.contains('transmission|existing', case=False, na=False)]
    if open_field_pv_df.empty:
        print("No rows found with carriers matching 'open_field_pv'. Skipping share calculation.")
        return

    by_tech = (
        open_field_pv_df.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
        .rename(columns={'flow_cap': 'open_field_pv_flow_cap'})
    )

    total_open_field_pv = by_tech['open_field_pv_flow_cap'].sum()
    if total_open_field_pv == 0:
        print("Total open field PV production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['open_field_pv_flow_cap'] / total_open_field_pv) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Rooftop capacity share by technology (% of total):")
    print(by_tech.to_string(index=False))

def check_biogas_capacities(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the rooftop production is greater than the open field PV demand
    """
   #open_field_pv_df = df[df['carriers'].str.contains('electricity', case=False, na=False)].copy()
    open_field_pv_df = df[df['techs'].str.contains('biogas', case=False, na=False)]
    open_field_pv_df = open_field_pv_df[~open_field_pv_df['techs'].str.contains('transmission|existing', case=False, na=False)]
    if open_field_pv_df.empty:
        print("No rows found with carriers matching 'open_field_pv'. Skipping share calculation.")
        return

    by_tech = (
        open_field_pv_df.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
        .rename(columns={'flow_cap': 'open_field_pv_flow_cap'})
    )

    total_open_field_pv = by_tech['open_field_pv_flow_cap'].sum()
    if total_open_field_pv == 0:
        print("Total open field PV production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['open_field_pv_flow_cap'] / total_open_field_pv) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Biogas capacity share by technology (% of total):")
    print(by_tech.to_string(index=False))

def check_wind_monopoly_capacities(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the rooftop production is greater than the open field PV demand
    """
   #open_field_pv_df = df[df['carriers'].str.contains('electricity', case=False, na=False)].copy()
    open_field_pv_df = df[df['techs'].str.contains('monopoly', case=False, na=False)]
    open_field_pv_df = open_field_pv_df[~open_field_pv_df['techs'].str.contains('transmission|existing', case=False, na=False)]
    if open_field_pv_df.empty:
        print("No rows found with carriers matching 'open_field_pv'. Skipping share calculation.")
        return

    by_tech = (
        open_field_pv_df.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
        .rename(columns={'flow_cap': 'open_field_pv_flow_cap'})
    )

    total_open_field_pv = by_tech['open_field_pv_flow_cap'].sum()
    if total_open_field_pv == 0:
        print("Total open field PV production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['open_field_pv_flow_cap'] / total_open_field_pv) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Wind monopoly capacity share by technology (% of total):")
    print(by_tech.to_string(index=False))

def check_biogas_capacities(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the rooftop production is greater than the open field PV demand
    """
   #open_field_pv_df = df[df['carriers'].str.contains('electricity', case=False, na=False)].copy()
    open_field_pv_df = df[df['techs'].str.contains('biogas', case=False, na=False)]
    open_field_pv_df = open_field_pv_df[~open_field_pv_df['techs'].str.contains('transmission|existing', case=False, na=False)]
    if open_field_pv_df.empty:
        print("No rows found with carriers matching 'open_field_pv'. Skipping share calculation.")
        return

    by_tech = (
        open_field_pv_df.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
        .rename(columns={'flow_cap': 'open_field_pv_flow_cap'})
    )

    total_open_field_pv = by_tech['open_field_pv_flow_cap'].sum()
    if total_open_field_pv == 0:
        print("Total open field PV production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['open_field_pv_flow_cap'] / total_open_field_pv) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Biogas capacity share by technology (% of total):")
    print(by_tech.to_string(index=False))

def check_battery_capacities(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the rooftop production is greater than the open field PV demand
    """
   #open_field_pv_df = df[df['carriers'].str.contains('electricity', case=False, na=False)].copy()
    open_field_pv_df = df[df['techs'].str.contains('battery', case=False, na=False)]
    open_field_pv_df = open_field_pv_df[~open_field_pv_df['techs'].str.contains('transmission|existing', case=False, na=False)]
    if open_field_pv_df.empty:
        print("No rows found with carriers matching 'open_field_pv'. Skipping share calculation.")
        return

    by_tech = (
        open_field_pv_df.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
        .rename(columns={'flow_cap': 'open_field_pv_flow_cap'})
    )

    total_open_field_pv = by_tech['open_field_pv_flow_cap'].sum()
    if total_open_field_pv == 0:
        print("Total open field PV production is 0. Skipping share calculation.")
        return

    by_tech['share_pct'] = (by_tech['open_field_pv_flow_cap'] / total_open_field_pv) * 100.0
    by_tech = by_tech.sort_values('share_pct', ascending=False).reset_index(drop=True)

    print("Battery capacity share by technology (% of total):")
    print(by_tech.to_string(index=False))


def check_european_capacity(df: pd.DataFrame, source_csv_path: str | None = None) -> None:
    """
    Check if the rooftop production is greater than the open field PV demand
    """
   #open_field_pv_df = df[df['carriers'].str.contains('electricity', case=False, na=False)].copy()
    

    local_capacity = df[df['nodes'].str.contains("ESP_", case=False, na=False)] 
    local_capacity = local_capacity[~local_capacity['techs'].str.contains("transmission|demand|existing", case=False, na=False)] 

    
    
    filter_european_techs = '|'.join(european_techs_list)
    european_techs = df[df['techs'].str.contains(filter_european_techs, case=False, na=False)] 
    

    

    by_tech = (
        european_techs.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
    )
    pass
    european_techs_group = by_tech['flow_cap'].sum()

    by_tech = (
        local_capacity.groupby(['techs'], as_index=False)['flow_cap']
        .sum()
    )
    pass
    total_capacity = by_tech['flow_cap'].sum()

    percentage = 100*european_techs_group / (total_capacity)

    print( f"European percentatge {percentage} %")
    pass


def check_capacities(path:str) -> None:
    df=pd.read_csv(path)
    check_european_capacity(df)
    pass
    check_open_field_pv_capacities(df)
    check_biogas_capacities(df)
    check_rooftop_capacities(df)
    check_wind_monopoly_capacities(df)
    check_battery_capacities(df)
    

def check_node_production(df:pd.DataFrame):
    df=df[df['carriers'].str.contains('electricity', case=False, na=False)]
    df = df.groupby(['nodes'], as_index=False)['flow_out'].sum()
    print("Production by node")
    print(df)
    pass

#wind_capacity_check(r'C:\Users\1496051\PycharmProjects\Calliope_ESP\src\calliope\example_models\spanish_model\output_uranium_testing\results_flow_cap.csv')
flow_out_sum(r'C:\Users\1496051\PycharmProjects\Calliope_ESP\src\calliope\example_models\spanish_model\results\results_test_scenario_A_monetary_csv\results_flow_out.csv', 'EXPORT')
#check_capacities(r'C:\Users\1496051\PycharmProjects\Calliope_ESP\src\calliope\example_models\spanish_model\results\results_test_scenario_B_monetary_csv\results_flow_cap.csv')