from WMCore.Configuration import Configuration
# from CRABClient.UserUtilities import config, getUsernameFromSiteDB
from CRABClient.UserUtilities import config

config = Configuration()

config.section_("General")
config.General.requestName = 'Test'
# config.General.requestName = 'NanoPost_eventAware'
config.General.workArea = 'crab_projects'
config.General.transferLogs = True

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.scriptExe = 'crab_script.sh'
# hadd nano will not be needed once nano tools are in cmssw
config.JobType.inputFiles = ['crab_script.py', '../scripts/haddnano.py']
config.JobType.outputFiles = ["tree.root", "cutflow.txt"]
# config.JobType.scriptArgs = ["--test 'THIS IS A CRAB TEST'"]
config.JobType.scriptArgs = ['--test="THISISCRABTEST"']
config.JobType.sendPythonFolder = True
config.JobType.allowUndistributedCMSSW = True

config.section_("Data")
config.Data.inputDataset = '/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM'
#config.Data.inputDBS = 'phys03'
config.Data.inputDBS = 'global'
# config.Data.splitting = 'Automatic'
# config.Data.unitsPerJob = 500
config.Data.splitting = 'EventAwareLumiBased'
# config.Data.unitsPerJob = 800000
config.Data.unitsPerJob = 5000
config.Data.totalUnits = 10000
config.Data.outLFNDirBase = '/store/user/swieland/NanoPost'
# config.Data.outLFNDirBase = '/store/user/%s/NanoPost' % (
#     getUsernameFromSiteDB())
config.Data.publication = False
# config.Data.outputDatasetTag = 'NanoPost'
config.Data.outputDatasetTag = 'Test'

config.section_("Site")
config.Site.storageSite = "T2_DE_DESY"

config.section_("User")
config.User.voGroup = 'dcms'

#config.Site.storageSite = "T2_CH_CERN"
# config.section_("User")
#config.User.voGroup = 'dcms'
