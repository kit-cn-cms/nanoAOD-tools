#!/usr/bin/env python
import os
import sys
import PSet

from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import *
from importlib import import_module

# this takes care of converting the input files from CRAB
from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis

def writeKeepOutFile(vars):
  with open("keepOut.txt", "w") as file:
    file.write("drop *\n")
    for v in vars:
      file.write("keep " + v+"\n")


from optparse import OptionParser
parser = OptionParser(usage="")
parser.add_option("-t", "--test", dest="test", type="string", default="THIS IS A TEST",
                  help="Testoption")
parser.add_option("-I", "--import", dest="imports", type="string", default=[], action="append",
                  nargs=2, help="Import modules (python package, comma-separated list of ")

(options, args) = parser.parse_args()

options.imports = [('PhysicsTools.NanoAODTools.postprocessing.examples.variableCalculatorModule', 'variableCalculatorModuleConstr')]

modules = []
for mod, names in options.imports:
    import_module(mod)
    obj = sys.modules[mod]
    selnames = names.split(",")
    mods = dir(obj)
    for name in selnames:
        if name in mods:
            print("Loading %s from %s " % (name, mod))
            if "variableCalculatorModule" in name:
              mod = getattr(obj,name)()
              mod.setOptions(test=options.test)   # pass options to module here!
              varsTosave = mod.var_calc.output_values.keys() + mod.var_calc.output_arrays.keys()
              writeKeepOutFile(varsTosave)
              modules.append(mod)
              continue
            if type(getattr(obj, name)) == list:
              if "variableCalculatorModule" in name:
                for mod in getattr(obj, name):
                    modules.append(mod())
            else:
                modules.append(getattr(obj, name)())

print("running following modules")
print(modules)

p = PostProcessor(outputDir = ".",
                  inputFiles = inputFiles(),
                #   cut = "",
                  modules=modules,
                  provenance=True,
                  fwkJobReport=True,
                  jsonInput=runsAndLumis(),
                  # maxEntries = 2000,
                  friend = False,
                  haddFileName = "tree.root",
                  outputbranchsel="keepOut.txt"
                  )
p.run()

# p = PostProcessor(outdir, args,
#                     cut=options.cut,
#                     branchsel=options.branchsel_in,
#                     modules=modules,
#                     compression=options.compression,
#                     friend=options.friend,
#                     postfix=options.postfix,
#                     jsonInput=options.json,
#                     noOut=options.noOut,
#                     justcount=options.justcount,
#                     prefetch=options.prefetch,
#                     longTermCache=options.longTermCache,
#                     maxEntries=options.maxEntries,
#                     firstEntry=options.firstEntry,
#                     outputbranchsel=options.branchsel_out)
# p.run()



print("DONE")
