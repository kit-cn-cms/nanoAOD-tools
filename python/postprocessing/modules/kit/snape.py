from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from pprint import pprint

# load class VariableCalculator
from PhysicsTools.snape.VariableCalculator import VariableCalculator
from PhysicsTools.snape.weights.GenWeights import GenWeights
from PhysicsTools.snape.cutflow.CutFlow    import CutFlow

import os 
import importlib

class Snape(Module):
    def __init__(self):

        # module for calculating and storing weights before selections
        self.weightpath   = ""
        self.weights_incl = GenWeights()

        # cutflow
        self.cutflowpath  = ""
        self.cutflow      = CutFlow()

    def setup(self, configName = "config_testAnalysis", dataEra = "2017", 
                    runType = "legacy", isData = False, jecs = [""]):
        # TODO set options for year, data and runType

        # load config module
        configImport = "PhysicsTools.snape.configs.{}".format(configName)
        print("loading config {}".format(configImport))
        configModule = importlib.import_module(configImport)
        config  = configModule.Config(
            dataEra = dataEra,
            runType = runType,
            isData  = isData,
            jecs    = jecs)

        # init snape module
        self.snape = VariableCalculator()
        self.snape.setConfig(config)

        # init branches in variable calculator
        self.snape.init_values()

    def beginJob(self, cutflowpath):
        self.cutflowpath         = os.path.join(cutflowpath, "cutflow.txt")
        self.cutflow.output_file = self.cutflowpath
        print("cutflow path: {}".format(self.cutflowpath))

        self.weightpath               = os.path.join(cutflowpath, "genWeights.root")
        self.weights_incl.output_file = self.weightpath
        self.weights_incl.initWeightSums()
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        nBranches = 0
        
        # loop over jec
        for jec in self.snape.config.jecs:

            # init scalar branches
            for key in self.snape.outputValues[jec]:

                # define list of integer variables
                integer_list = [
                    "N_Jets", 
                    "N_TightLeptons", 
                    "N_TightMuons", 
                    "N_TightElectrons", 
                    "N_BTagsM", 
                    "Evt_ID", 
                    "Evt_Lumi", 
                    "Evt_Run",  
                    "N_GenBJets", 
                    "GenEvt_I_TTPlusCC", 
                    "GenEvt_I_TTPlusBB"
                    ]
                
                if any(key == x for x in integer_list):
                    self.out.branch(key, "I")
                elif key.startswith("N_"):
                    self.out.branch(key, "I")

                else:
                    self.out.branch(key, "F")
                print("init branch {}".format(key))
                nBranches +=1

            # init array branches
            outputAr = self.snape.outputArrays[jec]
            print(outputAr)

            # loop over arrays
            for key in outputAr:

                # determine index variable
                index_var = "N_"+key.split("_")[0]
                if "Jet" in key:
                    index_var = "N_Jets"
                elif "Lepton" in key:
                    index_var = "N_TightLeptons"
                elif "Muon" in key:
                    index_var = "N_TightMuons"
                elif "Electron" in key:
                    index_var = "N_TightElectrons"
                index_var+= "_"+jec

                # initialize branch
                self.out.branch(key, "F", 1, index_var)
                print("init branch {} with index {}".format(key, index_var))
                nBranches +=1

        print("INFO: Initialized {} branches.".format(nBranches))

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.weights_incl.writeSummary()
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        # do selections
        # # global cutflow
        self.cutflow += 1

        # add inclusive weights
        self.weights_incl += event

        # selections
        isSelected = self.snape.config.isSelected(event, self.cutflow)
        if not isSelected:
            return False
        # convert to dict if only singular value is returned
        if not type(isSelected) == dict:
            isSelected = {sys: isSelected for sys in self.snape.config.jecs}
        if not any(isSelected.values()):
            return False

        # calc vars
        # for each jec source
        for sys in self.snape.config.jecs:
            # reset first
            self.snape.resetOutput()

            # figure out if event is triggered with jec
            if isSelected[sys]:
                self.snape.sys = sys
                self.snape.event = event
                self.snape.calculate()

            # write scalar branches
            for key in self.snape.outputValues[sys]:
                self.out.fillBranch(key, self.snape.outputValues[sys][key])

            # Write array branches
            for key in self.snape.outputArrays[sys]:
                self.out.fillBranch(key, self.snape.outputArrays[sys][key])

        return True


# define modules using the syntax 'name = lambda : constructor' 
# to avoid having them loaded when not needed
SnapeConstr = lambda: Snape()
