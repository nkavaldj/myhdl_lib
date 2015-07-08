import os
import sys
import fileinput

from myhdl import toVerilog, toVHDL, Cosimulation, traceSignals


class DUTer(object):
    ''' Returns a simulation instance of a MyHDL function, intended as a DUT in testbench
        The user selects a simulator: MyHDL, or co-simulation with external HDL simulator, e.g. icarus
        The user selects whether traces are generated or not
    '''


    def __init__(self):
        '''  '''
        self._simulator = "myhdl"
        self._trace = False

        self.sim_reg = {}

        self.registerSimulator(
            name="icarus",
            hdl="Verilog",
            analyze_cmd='iverilog -o {topname}.o tb_{topname}.v {topname}.v',
            simulate_cmd="vvp -m ./myhdl.vpi {topname}.o"
        )

    def registerSimulator(self, name=None, hdl=None, analyze_cmd=None, elaborate_cmd=None, simulate_cmd=None):
        ''' Registers an HDL _simulator
                name - str, user defined name, used to identify this _simulator record
                hdl - str, case insensitive, (verilog, vhdl), the HDL to which the simulated MyHDL code will be converted
                analyze_cmd - str, system command that will be run to analyze the generated HDL
                elaborate_cmd - str, optional, system command that will be run after the analyze phase
                simulate_cmd - str, system command that will be run to simulate the analyzed and elaborated design
                Before execution of a command string the following substitutions take place:
                    {topname} is substituted with the name of the simulated MyHDL function
        '''
        if not isinstance(name, str) or (name.strip() == ""):
            raise ValueError("Invalid _simulator name")
        if hdl.lower() not in ("vhdl", "verilog"):
            raise ValueError("Invalid hdl {}".format(hdl))
        if not isinstance(analyze_cmd, str) or (analyze_cmd.strip() == ""):
            raise ValueError("Invalid analyzer command")
        if elaborate_cmd is not None:
            if not isinstance(elaborate_cmd, str) or (elaborate_cmd.strip() == ""):
                raise ValueError("Invalid elaborate_cmd command")
        if not isinstance(simulate_cmd, str) or (simulate_cmd.strip() == ""):
            raise ValueError("Invalid _simulator command")

        self.sim_reg[name] = (hdl.lower(), analyze_cmd, elaborate_cmd, simulate_cmd)

    def selectSimulator(self, simulatorName):
        if not simulatorName:
            raise ValueError("No _simulator specified")
        if not simulatorName=='myhdl' and not self.sim_reg.has_key(simulatorName):
            raise ValueError("Simulator {} is not registered".format(simulatorName))
        self._simulator = simulatorName

    def enableTrace(self):
        self._trace = True

    def disableTrace(self):
        self._trace = False

    def _getCosimulation(self, func, **kwargs):
        ''' Returns a co-simulation instance of func. 
            Uses the _simulator specified by self._simulator. 
            Enables traces if self._trace is True
                func - MyHDL function to be simulated
                kwargs - dict of func interface assignments: for signals and parameters
        '''
        vals = {}
        vals['topname'] = func.func_name
        vals['unitname'] = func.func_name.lower()
        hdlsim = self._simulator
        if not hdlsim:
            raise ValueError("No _simulator specified")
        if not self.sim_reg.has_key(hdlsim):
            raise ValueError("Simulator {} is not registered".format(hdlsim))

        hdl, analyze_cmd, elaborate_cmd, simulate_cmd = self.sim_reg[hdlsim]

        # Convert to HDL
        if hdl == "verilog":
            toVerilog(func, **kwargs)
            if self._trace:
                self._enableTracesVerilog("./tb_{topname}.v".format(**vals))
        elif hdl == "vhdl":
            toVHDL(func, **kwargs)

        # Analyze HDL
        os.system(analyze_cmd.format(**vals))
        # Elaborate
        if elaborate_cmd:
            os.system(elaborate_cmd.format(**vals))
        # Simulate
        return Cosimulation(simulate_cmd.format(**vals), **kwargs)


    def _enableTracesVerilog(self, verilogFile):
        ''' Enables traces in a Verilog file'''
        fname, _ = os.path.splitext(verilogFile)
        inserted = False
        for _, line in enumerate(fileinput.input(verilogFile, inplace = 1)):
            sys.stdout.write(line)
            if line.startswith("end") and not inserted:
                sys.stdout.write('\n\n') 
                sys.stdout.write('initial begin\n')
                sys.stdout.write('    $dumpfile("{}_cosim.vcd");\n'.format(fname)) 
                sys.stdout.write('    $dumpvars(0, dut);\n') 
                sys.stdout.write('end\n\n') 
                inserted = True


    def _getDut(self, func, **kwargs):
        ''' Returns a simulation instance of func. 
            Uses the simulator specified by self._simulator. 
            Enables traces if self._trace is True
                func - MyHDL function to be simulated
                kwargs - dict of func interface assignments: for signals and parameters
        '''
        if self._simulator=="myhdl":
            if not self._trace:
                sim_dut = func(**kwargs)
            else:
                sim_dut = traceSignals(func, **kwargs)
        else:
            sim_dut = self._getCosimulation(func, **kwargs)

        return sim_dut

    def __call__(self, func, **kwargs):
        return self._getDut(func, **kwargs)

