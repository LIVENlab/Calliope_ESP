import calliope
import calliope
from Spanish_model.Scripts.extract_data import Extractor
# We increase logging verbosity
calliope.set_log_verbosity("DEBUG", include_solver_output=False)
model= calliope.examples.urban_scale()
model.build()
model.solve()
#data=Extractor(spanish_model).extract_all_inputs_to_excel(excel_path='extracted_data_example.xlsx')
