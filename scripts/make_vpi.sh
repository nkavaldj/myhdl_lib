#!/bin/sh
git clone https://github.com/jandecaluwe/myhdl

make -C myhdl/cosimulation/icarus

cp myhdl/cosimulation/icarus/myhdl.vpi ./