from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from pprint import pprint

# load class VariableCalculator
from PhysicsTools.snape.VariableCalculator          import VariableCalculator

from PhysicsTools.snape.selections.JetSelection     import JetSelection
from PhysicsTools.snape.selections.LeptonSelection  import LeptonSelection
from PhysicsTools.snape.selections.METSelection     import METSelection
from PhysicsTools.snape.selections.TriggerFilterMC  import TriggerFilterMC
from PhysicsTools.snape.selections.BasicTriggerMC   import BasicTriggerMC

from PhysicsTools.snape.weights.GenWeights          import GenWeights

from PhysicsTools.snape.cutflow.CutFlow             import CutFlow

import os 

class Snape(Module):
    def __init__(self, test=""):
        print("parsed option in constructor directly: {}"+test)

        # modules
        self.var_calc           = VariableCalculator()
        self.jet_tag_sel        = JetSelection()
        self.lep_sel            = LeptonSelection()
        self.met_sel            = METSelection()
        self.basic_trigger_mc   = BasicTriggerMC()
        self.trigger_filter_mc  = TriggerFilterMC()

        # module for calculating and storing weights before selections
        self.weightpath         = ""
        self.weights_incl       = GenWeights()

        # cutflow
        self.cutflowpath    = ""
        self.cutflow        = CutFlow()

        # options
        self.TestOption     = ""
        self.jecs           = None


    def setOptions(self, test = "", jecs = [""]):
        # TODO set options for year, data and runType

        # set options
        self.testOption = test
        self.jecs       = jecs

        # set jec related information
        if self.jecs:
            # reinit JetSelection
            self.jet_tag_sel.jecs = self.jecs
            self.jet_tag_sel.initCounter()

            # reinit Snape
            print("reinitializing variables")
            self.var_calc.jecs          = self.jecs
            self.var_calc.output_values = {}
            self.var_calc.output_arrays = {}
            self.var_calc.init_values()

    def beginJob(self, cutflowpath):
        self.cutflowpath         = os.path.join(cutflowpath,"cutflow.txt")
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
        
        # handle jecs
        if self.jecs:
            # loop over jec
            for jec in self.jecs:

                # init scalar branches
                for key in self.var_calc.output_ValueswJEC[jec]:

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

                try:
                    # init array branches
                    outputAr = self.var_calc.output_ArrayswJEC[jec]

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



                except:
                    print("WARNING: No array branches defined in Snape! Make sure this makes sense!")
            # --- jec loop

        # TODO I think this is deprecated as also non jec files will get _nom as jec
        #else:
        #    for key in self.var_calc.output_values[jec]:
        #            if "N_" in key:
        #                self.out.branch(key, "I")
        #            else:
        #                self.out.branch(key, "F")
        #    for key in self.var_calc.output_arrays:
        #        index_var = "n"+key
        #        if "Jet" in key:
        #            index_var = "N_Jets_"+jec
        #        elif "Lepton" in key:
        #            index_var = "N_TightLeptons"
        #        self.out.branch(key, "F", 1, index_var) 
        else:
            print("WOW THERE ARE NO JECs HOW IS THIS POSSIBLE OMG")
            sys.exit(1)

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

        # Trigger Selection
        triggersel = (self.basic_trigger_mc.apply_basic_trigger_mc(event) and \
                      self.trigger_filter_mc.apply_trigger_filter_mc(event))
        if not triggersel: 
            return False
        self.cutflow.update_cutflow("Basic Trigger MC Selection", self.basic_trigger_mc.counter)
        self.cutflow.update_cutflow("Filter MC Selection",        self.trigger_filter_mc.counter)

        # Lepton Selection
        lepsel = self.lep_sel.apply_lepton_selection(event)
        if not lepsel:
            return False
        self.cutflow.update_cutflow("Single Lepton Selection", self.lep_sel.counter)


        # MET Selection
        metsel = self.met_sel.apply_met_selection(event)
        if not metsel:
            return False
        self.cutflow.update_cutflow("MET Selection", self.met_sel.counter)

        # # Jet Selection
        # check each JEC individually
        jetsels = {}
        for sys in self.jecs:
            jetsel = self.jet_tag_sel.apply_jet_selection(event, sys = sys)
            jetsels[sys] = jetsel
            if jetsel:
                self.cutflow.update_cutflow(sys+": >=4 Jet, >=3 Tag Selection", 
                    self.jet_tag_sel.counter[sys])

        # check jetselection for all JECs and continue if at least one is True
        if not any(jetsels.values()):
            return False

        # calc vars
        # for each jec source
        for sys in self.jecs:
            # reset first
            self.var_calc.resetOutput()

            # figure out if event is triggered with jec
            if jetsels[sys]:
                self.var_calc.sys   = sys
                self.var_calc.event = event
                self.var_calc.calculate()

            # write scalar branches
            for key in self.var_calc.output_ValueswJEC[sys]:
                self.out.fillBranch(key, self.var_calc.output_ValueswJEC[sys][key])

            # Write array branches
            try:
                for key in self.var_calc.output_ArrayswJEC[sys]:
                    self.out.fillBranch(key, self.var_calc.output_ArrayswJEC[sys][key])
            except:
                print("WARNING: No array branches defined, therefore not filling them")

        return True


# define modules using the syntax 'name = lambda : constructor' 
# to avoid having them loaded when not needed
SnapeConstr = lambda: Snape()
