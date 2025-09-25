import calliope
import os

# Optional: Check where Calliope is installed
print(calliope.__file__)
print("Starting Scenario A run...")

# Set logging to debug to see more detailed messages
calliope.set_log_verbosity("DEBUG")

# Define output paths
nc_out = "results/results_test_scenario_A.nc"
csv_folder = "results/results_test_scenario_A_csv"

# Ensure output directories exist
os.makedirs(os.path.dirname(nc_out), exist_ok=True)
os.makedirs(csv_folder, exist_ok=True)

# Load the Spanish model for Scenario A
model = calliope.examples.spanish_model(
    filename="model.yaml",
    scenario="scenario_A"  # Or use "scenario_A" depending on your Snakefile
)

# Build and solve
model.build()
model.solve()

# Save results
model.to_netcdf(nc_out)
model.to_csv(csv_folder, allow_overwrite=True)

print("Scenario A completed successfully.")


