CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17

SIM := build/micromouse_sim

.PHONY: all sim clean

all: sim

sim: $(SIM)

$(SIM): src/micromouse_sim.cpp
	@mkdir -p build
	$(CXX) $(CXXFLAGS) $< -o $@

clean:
	rm -rf build
