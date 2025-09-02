"""
@LexPascal
This script post-processes the results of a Calliope model run for a Spanish energy system.
"""

import pandas as pd
import os

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
    # Group by the relevant columns and sum 'flow_out'
    result = data.groupby(['nodes', 'techs', 'carriers'], as_index=False)['flow_out'].sum()
    # Optionally rename the flow_out column
    result, _ = rename_flow_out_columns(result, output_name, scenario_name)
    # Save to CSV
    _ = f"{_}.csv"
    output_path = new_path(path, _)
    result.to_csv(output_path, index=False)

flow_out_sum(r'C:\Users\1496051\PycharmProjects\calliope\src\calliope\example_models\spanish_model\results_fix_loc\results_flow_out.csv', 'scenario1')
