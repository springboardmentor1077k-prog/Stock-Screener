@echo off
echo Starting All Demos...

echo Starting Demo 1...
cd "Demo 1 (valid query execution)"
start "Demo 1" run_demo.bat
cd ..

echo Starting Demo 2...
cd "Demo 2 (valid query but no matching data)"
start "Demo 2" run_demo.bat
cd ..

echo Starting Demo 3...
cd "Demo 3 (invalid or unsupported query)"
start "Demo 3" run_demo.bat
cd ..

echo All demos started in separate windows.
