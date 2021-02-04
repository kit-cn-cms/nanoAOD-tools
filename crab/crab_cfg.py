from WMCore.Configuration import Configuration
from CRABClient.UserUtilities import config
from CRABClient import getUsername
username = getUsername()

config = Configuration()

config.section_("General")
config.General.requestName = 'Test_Syst'
config.General.workArea = 'crab_projects'
config.General.transferLogs = True

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.scriptExe = 'crab_script.sh'
# hadd nano will not be needed once nano tools are in cmssw
config.JobType.inputFiles = ['crab_script.py', '../scripts/haddnano.py']
config.JobType.outputFiles = ["tree.root", "cutflow.txt"]
config.JobType.scriptArgs = ["--JEC=Total","--noSyst=false","--isData=False","--era=2017"]

config.JobType.sendPythonFolder = True
config.JobType.allowUndistributedCMSSW = True

config.section_("Data")
config.Data.inputDataset = '/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM'
#config.Data.inputDBS = 'phys03'
config.Data.inputDBS = 'global'
# config.Data.splitting = 'Automatic'
# config.Data.unitsPerJob = 500
config.Data.splitting = 'EventAwareLumiBased'
config.Data.unitsPerJob = 100000
# config.Data.totalUnits = 200000

config.Data.outLFNDirBase = '/store/user/swieland/NanoPost'
config.Data.outLFNDirBase = '/store/user/%s/NanoPost' % (username)
config.Data.publication = False
config.Data.outputDatasetTag = 'Test'

config.section_("Site")
config.Site.storageSite = "T2_DE_DESY"

config.section_("User")
config.User.voGroup = 'dcms'
