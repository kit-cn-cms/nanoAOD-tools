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
        print("parsed option in constructor directly: "+test)
        self.var_calc = VariableCalculator()
        self.jet_tag_sel = JetSelection()
        self.lep_sel = LeptonSelection()
        self.met_sel = METSelection()
        self.basic_trigger_mc = BasicTriggerMC()
        self.trigger_filter_mc = TriggerFilterMC()
        self.cutflowpath = ""
        self.cutflow = CutFlow()
        self.TestOption =""
        self.jecs = None

        pass

    def setOptions(self, test = "", jecs = [""]):
        self.testOption = test
        self.jecs = jecs
        if self.jecs:
            # reinit JetSelection
            self.jet_tag_sel.jecs = self.jecs
            self.jet_tag_sel.initCounter()

            # reinit variableCalculator
            print("reinitializing variables")
            self.var_calc.jecs = self.jecs
            self.var_calc.output_values = {}
            self.var_calc.output_arrays = {}
            self.var_calc.init_values()
        # print("successfully passed option: " + self.jecs)
        # exit()
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
        nBranches = 0
        
        # pprint(self.var_calc.output_ValueswJEC)
        # pprint(self.var_calc.output_ArrayswJEC)
        if self.jecs:
            for jec in self.jecs:
                # init scalar branches
                for key in self.var_calc.output_ValueswJEC[jec]:
                    # if "N_Jets" in key or "N_TightLeptons" in key:
                    if "N_" in key:
                        self.out.branch(key, "I")
                    else:
                        self.out.branch(key, "F")
                    print("init branch {}".format(key))
                    nBranches +=1

                try:
                    # init array branches
                    outputAr = self.var_calc.output_ArrayswJEC[jec]
                    for key in outputAr:
                        index_var = "n"+key
                        if "Jet" in key:
                            index_var = "N_Jets_"+jec
                        elif "Lepton" in key:
                            index_var = "N_TightLeptons"
                        # print("index_var : {}".format(index_var))
                        self.out.branch(key, "F", 1, index_var)
                        print("init branch {} with index {}".format(key, index_var))
                        nBranches +=1
                except:
                    print("WARNING: No array branches defined in variableCalculator! Make sure this makes sense!")
        else:
            for key in self.var_calc.output_values[jec]:
                    # if "N_Jets" in key or "N_TightLeptons" in key:
                    if "N_" in key:
                        self.out.branch(key, "I")
                    else:
                        self.out.branch(key, "F")
            for key in self.var_calc.output_arrays:
                index_var = "n"+key
                if "Jet" in key:
                    index_var = "N_Jets_"+jec
                elif "Lepton" in key:
                    index_var = "N_TightLeptons"
                self.out.branch(key, "F", 1, index_var) 

        print("INFO: Initialized {} branches.".format(nBranches))

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        # do selections
        # # global cutflow
        self.cutflow += 1



        # Trigger Selection
        triggersel = (self.basic_trigger_mc.apply_basic_trigger_mc(event) and self.trigger_filter_mc.apply_trigger_filter_mc(event))
        if not triggersel:
            return False
        self.cutflow.update_cutflow("Basic Trigger MC Selection", self.basic_trigger_mc.counter)
        self.cutflow.update_cutflow("Filter MC Selection", self.trigger_filter_mc.counter)

        # Lepton Selection
        lepsel = self.lep_sel.apply_lepton_selection(event)
        # print("lepsel is {}".format(lepsel))
        if not lepsel:
            return False
        self.cutflow.update_cutflow("Single Lepton Selection", self.lep_sel.counter)


        # # MET Selection
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
                self.cutflow.update_cutflow(sys+": >=4 Jet, >=3 Tag Selection", self.jet_tag_sel.counter[sys])
        # check jetselection for all JECs and continue if at least one is True
        if not any(jetsels.values()):
            return False



        
        # # # Final Check Selections
        # is_selected = (jetsel and lepsel and metsel and triggersel)
        # if not is_selected:
        #     return False


        # weird event instance stuff...
        # if self.var_calc.eventError == True:
            # return False

        # calc vars
        for sys in self.jecs:
            self.var_calc.resetOutput()
            # print(sys)
            # print("#"*20)
            # print("calculating vars for {}".format(sys))
            if jetsels[sys]:
                self.var_calc.sys = sys
                self.var_calc.event = event
                self.var_calc.calculate()
            # else: # reset values in case event gets not selected for a certain jes-> only write dummy vars
                # self.var_calc.resetOutput()
                # print(sys)
                # pprint(self.var_calc.output_ArrayswJEC[sys])
                # pprint(self.var_calc.resetValuesArray[sys])

            # write scalar branches
            for key in self.var_calc.output_ValueswJEC[sys]:
                self.out.fillBranch(key, self.var_calc.output_ValueswJEC[sys][key])
                # if "N_Jets" in key:
                    # print("Filling {var} with value {val}".format(var=key,val=self.var_calc.output_ValueswJEC[sys][key]))
            # Write array branches
            try:
                for key in self.var_calc.output_ArrayswJEC[sys]:
                    self.out.fillBranch(key, self.var_calc.output_ArrayswJEC[sys][key])
                    # if "Jet_Pt" in key and not jetsels[sys]:
                        # print("Filling {var} with value {val}".format(var=key,val=self.var_calc.output_ArrayswJEC[sys][key]))
            except:
                print("WARNING: No array branches defined, therefore not filling them")

        # print("----------------")
        # pprint(self.var_calc.output_ValueswJEC)
        # pprint(self.var_calc.output_ArrayswJEC[sys])

        return True


# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed
variableCalculatorModuleConstr = lambda: variableCalculatorModule()
