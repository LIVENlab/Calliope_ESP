@echo off

echo "Run 1"
calliope run model.yaml --scenario IR_test_1 --save_netcdf out_1_IR_test_1.nc

echo "Run 2"
calliope run model.yaml --scenario IR_test_2 --save_netcdf out_2_IR_test_2.nc

echo "Run 3"
calliope run model.yaml --scenario IR_test_3 --save_netcdf out_3_IR_test_3.nc

echo "Run 4"
calliope run model.yaml --scenario IR_test_4 --save_netcdf out_4_IR_test_4.nc
