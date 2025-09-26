import calliope
import os
import traceback
from Scripts.functions_scenarios import create_scenario_E, restore_european_capacity

# ---------- Configuration ----------
model_file = "model.yaml"
results_A_file = "results/results_test_scenario_A.nc"  # output from Scenario A
overrides_file = "overrides.yaml"
math_file = "math.yaml"

nc_out = "results/results_test_scenario_E.nc"
csv_folder = "results/results_test_scenario_E_csv"
done_file = "results/results_test_scenario_E.done"

lp_file = "results/my_model_E.lp"
results_ilp = "results/my_model_E.ilp"

# Ensure output directories exist
os.makedirs(os.path.dirname(nc_out), exist_ok=True)
os.makedirs(csv_folder, exist_ok=True)

# ---------- Build Scenario E ----------
print("--- Running scenario_E (single) ---")

# Prepare scenario E (modifies math.yaml in the background)
create_scenario_E(math_file, overrides_file, expand_costs=False)

try:
    model = calliope.examples.spanish_model(
        filename=model_file,
        scenario="scenario_E"
    )
    model.build()
    model.backend.verbose_strings()
    model.backend.to_lp(lp_file)

    # Restore European capacity constraint after scenario creation
    restore_european_capacity(math_file)

    model.solve()
    model.to_netcdf(nc_out)
    model.to_csv(csv_folder, allow_overwrite=True)

    # Create a .done marker
    with open(done_file, 'w') as f:
        f.write("completed")

    print(f"Scenario E completed successfully: {nc_out}")

except Exception as e:
    print(f"Error running scenario E: {e}")
    traceback.print_exc()

    # Attempt Gurobi fallback if LP exists
    if os.path.exists(lp_file):
        import subprocess
        cmd = ["gurobi_cl", f"ResultFile={results_ilp}", lp_file]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Gurobi report saved at {results_ilp}")

        # Create fallback .done file
        with open(done_file, 'w') as f:
            f.write("completed_with_gurobi_fallback")
