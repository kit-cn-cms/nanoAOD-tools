from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from pprint import pprint

# load class VariableCalculator
from PhysicsTools.snape.VariableCalculator     import VariableCalculator
from PhysicsTools.snape.container.GenWeights   import GenWeights
from PhysicsTools.snape.container.CutFlow      import CutFlow
from PhysicsTools.snape.modules.BaseCalculator import BaseCalculator as base

import os 
import importlib

class Snape(Module):
    def __init__(self):
        self.cutflowpath = ""
        # module for calculating and storing weights before selections
        self.weights = GenWeights()

        # cutflow
        self.cutflow = CutFlow()

    def setup(self, configName = "config_testAnalysis", dataEra = "2017", 
                    runType = "legacy", isData = False, isTopNanoAOD = False,
                    sampleName = None, jecs = [""]):

        # load config module
        configImport = "PhysicsTools.snape.configs.{}".format(configName)
        print("loading config {}".format(configImport))
        configModule = importlib.import_module(configImport)
        config  = configModule.Config(
            dataEra      = dataEra,
            runType      = runType,
            isData       = isData,
            isTopNanoAOD = isTopNanoAOD,
            sampleName   = sampleName,
            jecs         = jecs)

        # init snape module
        self.snape = VariableCalculator()
        self.snape.setConfig(config)

        # init branches in variable calculator
        self.snape.init_values()

    def beginJob(self, cutflowpath):
        self.cutflowpath = os.path.join(cutflowpath, "cutflow.txt")
        self.cutflow.output_file = self.cutflowpath
        print("cutflow path: {}".format(self.cutflowpath))

        weightpath = os.path.join(cutflowpath, "genWeights.root")
        self.weights.output_file = weightpath
        self.weights.initWeightSums(self.snape.config.sampleName)
        print("genWeights path: {}".format(weightpath))
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        nBranches = 0
        
        for sys in self.snape.config.jecs:
            for var in base.vc.variables:
                self.out.branch(
                    var+"_"+sys, 
                    base.vc.varTypes[var])
                print("init branch {}".format(var+"_"+sys))
                nBranches += 1
            for arr in base.vc.arrays:
                self.out.branch(
                    arr+"_"+sys, 
                    base.vc.varTypes[arr], 1, 
                    base.vc.arrayCounters[arr]+"_"+sys)
                print("init array {}".format(arr+"_"+sys))
                nBranches += 1

        print("INFO: Initialized {} branches.".format(nBranches))

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.weights.writeSummary()
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        # do selections
        # # global cutflow
        self.cutflow += 1

        # add inclusive weights
        self.weights += event

        # selections
        isSelected = self.snape.config.isSelected(event, self.cutflow)
        if not isSelected:
            return False
        # convert to dict if only singular value is returned
        if not isinstance(isSelected,  dict):
            isSelected = {sys: isSelected for sys in self.snape.config.jecs}
        if not any(isSelected.values()):
            return False

        # calc vars
        # reset first
        self.snape.resetOutput()
        # for each jec source
        for sys in self.snape.config.jecs:
            self.snape.resetOutput()

            # figure out if event is triggered with jec
            if isSelected[sys]:
                self.snape.sys   = sys
                self.snape.event = event
                self.snape.calculate()

            # write scalar branches
            for var in base.vc.variables:
                #print(var, getattr(base.vc, var))
                self.out.fillBranch(var+"_"+sys, getattr(base.vc, var))

            # Write array branches
            for arr in base.vc.arrays:
                self.out.fillBranch(arr+"_"+sys, getattr(base.vc, arr))

        return True


# define modules using the syntax 'name = lambda : constructor' 
# to avoid having them loaded when not needed
SnapeConstr = lambda: Snape()
