#!/usr/bin/env python
import os
import sys
import PSet
import glob

from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import *
from importlib import import_module
from pprint import pprint

# this takes care of converting the input files from CRAB
from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis

from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import createJMECorrector


def writeKeepOutFile(vars):
  with open("keepOut.txt", "w") as file:
    file.write("drop *\n")
    # file.write("keep *MET*"+"\n")
    # file.write("keep *"+"\n")
    for v in vars:
        file.write("keep " + v+"\n")

schemes = ["Total","Merged","All"]
default_JEC_scheme = "Total"

from optparse import OptionParser
parser = OptionParser(usage="")
parser.add_option("-t", "--test", dest="test", type="string", default="THIS IS A TEST",
                  help="Testoption")
parser.add_option("-I", "--import", dest="imports", type="string", default=[], action="append",
                  nargs=2, help="Import modules (python package, comma-separated list of ")
parser.add_option("--noRedoJEC", dest="noRedoJEC", default=False, action="store_true",
                  help="DO NOT reapply latest JECs and run systs")
parser.add_option("--JEC", dest="JECscheme",
                  type = "choice", choices = schemes, 
                  default = default_JEC_scheme,
                  help = "Which JEC scheme should be run? Valid choices are %s. Default: %s"\
                         % (schemes, default_JEC_scheme)
                )
parser.add_option("-e", "--era", dest="era", type="string", default="2017",
                  help="Specify era of the dataset. default: 2017")
parser.add_option("--isData", dest="isData", default=False, action="store_true",
                  help="Specify if dataset is real data.")


(options, args) = parser.parse_args()

options.imports = [('PhysicsTools.NanoAODTools.postprocessing.examples.variableCalculatorModule', 'variableCalculatorModuleConstr')]

if not options.noRedoJEC:
    # jetmetCorrector = createJMECorrector(isMC=True, dataYear=2017, jesUncert="Merged", applyHEMfix=False) 
    jetmetCorrector = createJMECorrector(isMC=not options.isData, dataYear=options.era, jesUncert=options.JECscheme, applyHEMfix="2018" in options.era ) 
    jecs = ["nom", "jerUp", "jerDown"] + ["jes" + s + "Up" for s in jetmetCorrector().jesUncertainties] + ["jes" + s + "Down" for s in jetmetCorrector().jesUncertainties]
    print("doing following JEC uncs:")
    print(jecs)

    modules = [jetmetCorrector()]
else:
    modules = []
    jecs = []

# load modules 
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
                mod.setOptions(test=options.test, jecs = jecs)   # pass options to module here!
                varsTosave = []
                for sys in jecs:
                    varsTosave += mod.var_calc.output_ValueswJEC[sys].keys()
                    try:
                        varsTosave += mod.var_calc.output_ArrayswJEC[sys].keys() 
                    except:
                        print("Didn't find key '{key}' in output_ArrayswJEC for module {name}".format(key=sys, name = name))
                # varsTosave = mod.var_calc.output_values.keys() + mod.var_calc.output_arrays.keys()
                writeKeepOutFile(varsTosave)
                modules.append(mod)
                continue
            # if type(getattr(obj, name)) == list:
            #     for mod in getattr(obj, name):
            #         modules.append(mod())
            # else:
            #     modules.append(getattr(obj, name)())

print("running following modules")
print(modules)

# p = PostProcessor(outputDir = ".",
#                   inputFiles = inputFiles(),
#                 #   cut = "",
#                   modules=modules,
#                   provenance=True,
#                   fwkJobReport=True,
#                   jsonInput=runsAndLumis(),
#                   # maxEntries = 2000,
#                   friend = False,
#                   haddFileName = "tree.root",
#                   outputbranchsel="keepOut.txt"
#                   )
# p.run()


p = PostProcessor(outputDir = ".",
                  inputFiles = ["inFile.root"],
                #   cut = "",
                  modules=modules,
                  provenance=True,
                  fwkJobReport=True,
                  # jsonInput=runsAndLumis(),
                  # maxEntries = 2000,
                  friend = False,
                  haddFileName = "tree.root",
                  outputbranchsel="keepOut.txt",
                  maxEntries=100000
                  # maxEntries=1
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
