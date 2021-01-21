from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from pprint import pprint

# load class VariableCalculator
from PhysicsTools.variablecalculator.VariableCalculator import VariableCalculator

from PhysicsTools.variablecalculator.selections.JetSelection import JetSelection
from PhysicsTools.variablecalculator.selections.LeptonSelection import LeptonSelection
from PhysicsTools.variablecalculator.selections.METSelection import METSelection
from PhysicsTools.variablecalculator.selections.TriggerFilterMC import TriggerFilterMC
from PhysicsTools.variablecalculator.selections.BasicTriggerMC import BasicTriggerMC
from PhysicsTools.variablecalculator.cutflow.CutFlow import CutFlow


class variableCalculatorModule(Module):
    def __init__(self, test=""):
        self.var_calc = VariableCalculator()
        self.jet_tag_sel = JetSelection()
        self.lep_sel = LeptonSelection()
        self.met_sel = METSelection()
        self.basic_trigger_mc = BasicTriggerMC()
        self.trigger_filter_mc = TriggerFilterMC()
        self.cutflowpath = ""
        self.cutflow = CutFlow()
        self.TestOption =""
        pass

    def setOptions(self, test = ""):
        self.testOption = test
        print("successfully passed test option: " + self.testOption)
        pass

    def beginJob(self, cutflowpath):
        self.cutflowpath = cutflowpath+"/cutflow.txt"
        self.cutflow.output_file = self.cutflowpath
        print(self.cutflowpath)
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        
        # init scalar branches
        for key in self.var_calc.output_values:
            if key == "N_Jets" or key =="N_TightLeptons":
                self.out.branch(key, "I")
            else:
                self.out.branch(key, "F")

        # init array branches
        for key in self.var_calc.output_arrays:
            index_var = "n"+key
            if "Jet" in key:
                index_var = "N_Jets"
            elif "Lepton" in key:
                index_var = "N_TightLeptons"
            self.out.branch(key, "F", 1,index_var)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        self.var_calc.event = event


        # do selections
        # # global cutflow
        self.cutflow += 1
        
        # # Trigger Selection
        triggersel = (self.basic_trigger_mc.apply_basic_trigger_mc(event) and self.trigger_filter_mc.apply_trigger_filter_mc(event))
        if not triggersel:
            return False
        self.cutflow.update_cutflow("Basic Trigger MC Selection", self.basic_trigger_mc.counter)
        self.cutflow.update_cutflow("Filter MC Selection", self.trigger_filter_mc.counter)

        # # Lepton Selection
        lepsel = self.lep_sel.apply_lepton_selection(event)
        # print("lepsel is {}".format(lepsel))
        if not lepsel:
            return False
        self.cutflow.update_cutflow("Single Lepton Selection", self.lep_sel.counter)

        # # Jet Selection
        jetsel = self.jet_tag_sel.apply_jet_selection(event)
        # print("jetsel is {}".format(jetsel))
        if not jetsel:
            return False
        self.cutflow.update_cutflow(">=4 Jet, >=3 Tag Selection", self.jet_tag_sel.counter)

        # # MET Selection
        metsel = self.met_sel.apply_met_selection(event)
        if not metsel:
            return False
        self.cutflow.update_cutflow("MET Selection", self.met_sel.counter)
        
        # # Final Check Selections
        is_selected = (jetsel and lepsel and metsel and triggersel)
        if not is_selected:
            return False


        # weird event instance stuff...
        # if self.var_calc.eventError == True:
            # return False
        # calc vars
        self.var_calc.calculate()
        
        # write scalar branches
        for key in self.var_calc.output_values:
            self.out.fillBranch(key, self.var_calc.output_values[key])
        
        # write array branches
        # pprint(self.var_calc.output_arrays)
        for key in self.var_calc.output_arrays:
            self.out.fillBranch(key, self.var_calc.output_arrays[key])
        
        return True


# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

variableCalculatorModuleConstr = lambda: variableCalculatorModule("TEST")
