CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17
PYTHON   ?= python3

SIM := build/micromouse_sim

.PHONY: all sim trace experiments sensor-experiments figures clean

all: sim

sim: $(SIM)

$(SIM): src/micromouse_sim.cpp
	@mkdir -p build
	$(CXX) $(CXXFLAGS) $< -o $@

# Exploration / speed-run trace of maze 0 (used by the maze figure)
trace: $(SIM)
	$(SIM) mode=trace maze=0 braid=0.05 > results/trace_maze0.txt

# Full sweep E1-E9 (rewrites results/all_runs.csv.gz)
experiments: $(SIM)
	$(PYTHON) scripts/run_experiments.py

# Voltage-sensor / transfer sweeps E10, E6b (appended to results/all_runs.csv.gz)
sensor-experiments: $(SIM)
	$(PYTHON) scripts/run_sensor_experiments.py

figures:
	$(PYTHON) scripts/make_figures.py

clean:
	rm -rf build figs
