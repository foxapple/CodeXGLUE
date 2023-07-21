#!/usr/bin/env python

from __future__ import print_function
from pydpiper.application import AbstractApplication
import atoms_and_modules.registration_functions as rf
import atoms_and_modules.registration_file_handling as rfh
import atoms_and_modules.minc_modules as mm
import atoms_and_modules.minc_atoms as ma
import atoms_and_modules.LSQ6 as lsq6
import atoms_and_modules.LSQ12 as lsq12
import atoms_and_modules.NLIN as nlin
import atoms_and_modules.stats_tools as st
from os.path import abspath, isdir, isfile
import logging
import sys
from datetime import date
import csv

logger = logging.getLogger(__name__)

def addRegChainArgumentGroup(parser):
    """option group for the command line argument parser"""
    group = parser.add_argument_group("Registration-chain options",
                       "Options for registering consecutive timepoints of longitudinal data.")
    group.add_argument("--avg-time-point", dest="avg_time_point",
                       type=int, default=1,
                       help="Time point averaged prior to this registration to get common nlin space."
                            "If you want to use the last time point from each of your input files, "
                            "(they might differ per input file) specify -1. [Default = %(default)s]")
    group.add_argument("--common-space-name", dest="common_name",
                       type=str, default="common", 
                       help="Option to specify a name for the common space. This is useful for the "
                            "creation of more readable output file names. Default is common. Note "
                            "that the common space is the one created by an iterative group-wise " 
                            "registration, either within this code or one that was run previously.")
    group.add_argument("--run-groupwise", dest="run_groupwise",
                       action="store_true",
                       help="Run an iterative, groupwise registration (MBM) on the specified average "
                            " time point. [Default]")
    group.add_argument("--no-run-groupwise", dest="run_groupwise",
                       action="store_false", 
                       help="If specified, do not run a groupwise registration on the specified "
                            "average time point [Opposite of --run-groupwise.]. If an iterative "
                            "group-wise registration was run previously, the average and transforms "
                            "from that registration can be accessed using the --MBM-directory and "
                            "--nlin-average options. (See below.)")
    group.add_argument("--MBM-directory", dest="mbm_dir",
                       type=str, default=None, 
                       help="_processed directory from MBM used to average specified time point ")
    group.add_argument("--nlin-average", dest="nlin_avg",
                       type=str, default=None, 
                       help="Final nlin average from MBM run.")
    parser.set_defaults(run_groupwise=True)

class RegistrationChain(AbstractApplication):
    def setup_options(self):
        """Add option groups from specific modules"""
        addRegChainArgumentGroup(self.parser)
        rf.addGenRegArgumentGroup(self.parser)
        lsq6.addLSQ6ArgumentGroup(self.parser)
        lsq12.addLSQ12ArgumentGroup(self.parser)
        nlin.addNlinRegArgumentGroup(self.parser)
        st.addStatsArguments(self.parser)
        
    def setup_appName(self):
        appName = "Registration-chain"
        return appName

    def run(self):

        # we should start with some input file checking. The paths to the input files
        # all reside in self.args[0] (a .csv file)
        all_input_files = []
        fileList = open(self.args[0], 'rb')
        subjectList = csv.reader(fileList, delimiter=',', skipinitialspace=True) 
        for subjLine in subjectList:
            for subj in subjLine:
                if subj != "":
                    all_input_files.append(subj)
        rf.checkInputFiles(all_input_files)

        # if no pipeline name was provided, initialize it here with the current date
        # setupDirectories deals with a missing pipeline name well, but we use this variable
        # in some more places
        if not self.options.pipeline_name:
            self.options.pipeline_name = str(date.today()) + "_pipeline"

        #Setup output directories for registration chain (_processed only)       
        dirs = rf.setupDirectories(self.outputDir, self.options.pipeline_name, module="ALL")
        
        #Check that correct registration method was specified
        if self.options.reg_method != "minctracc" and self.options.reg_method != "mincANTS":
            logger.error("Incorrect registration method specified: " + self.options.reg_method)
            sys.exit()
        
        if self.options.avg_time_point == -1:
            # In this case we are simply using the very last
            # scan from each of the input files
            avgTime = -1
        else:
            #Take average time point, subtract 1 for proper indexing
            avgTime = self.options.avg_time_point - 1

        if avgTime == -1 and self.options.run_groupwise:
            print("\nThe groupwise registration will be run using the last time points for each of the input files.\n")

        # Read in files from csv
        # What is returned (subjects) is a dictionary where each entry is numbered
        # from 0 .. #subjects -1, where each value associated with a key is an
        # array of the file handlers for the files related to that entry. For instance:
        # {0: [<FH for fileA_1.mnc>, <FH for fileA_2.mnc>],
        #  1: [<FH for fileB_1.mnc>, <FH for fileB_2.mnc>]}
        #
        subjects = rf.setupSubjectHash(self.args[0], dirs, self.options.mask_dir)
        
        resolutionForGroupWiseRegistration = None
        
        # If input = native space then do LSQ6 first on all files.
        if self.options.input_space == "native":
            initModel, targetPipeFH = rf.setInitialTarget(self.options.init_model, 
                                                          self.options.lsq6_target, 
                                                          dirs.lsq6Dir,
                                                          self.outputDir,
                                                          self.options.pipeline_name)
            #LSQ6 MODULE, NUC and INORM
            inputFiles = []
            for subj in subjects:
                for i in range(len(subjects[subj])):
                    inputFiles.append(subjects[subj][i])
            # We will create an initial verification image here. This
            # will show the user whether it is likely for the alignment to
            # work altogether (potentially the orientation of the target
            # and the input files is too different.) 
            montageBeforeRegistration = self.outputDir + "/" + self.options.pipeline_name + "_quality_control_target_and_inputfiles.png"
            initialVerificationImages = mm.createQualityControlImages([targetPipeFH] + inputFiles,
                                                                   montageOutPut=montageBeforeRegistration,
                                                                   message="at the very start of the registration.")
            self.pipeline.addPipeline(initialVerificationImages.p)
                
            runLSQ6NucInorm = lsq6.LSQ6NUCInorm(inputFiles,
                                                targetPipeFH,
                                                initModel, 
                                                dirs.lsq6Dir, 
                                                self.options)
            # TODO: This is a temporary hack: we add the output of the verification 
            # image as an input to all stages from the LSQ6 stage to make
            # sure that this image is created as soon as possible
            # This obviously is overkill, but it doens't really hurt either
            for lsq6Stage in runLSQ6NucInorm.p.stages:
                lsq6Stage.inputFiles.append(montageBeforeRegistration)
            self.pipeline.addPipeline(runLSQ6NucInorm.p)
        
        elif self.options.input_space == "lsq6":
            initModel = None
            # In this case the input files are already aligned. We can 
            # the finest resolution of one of the provided input files:
            # resolution of first file:
            resolutionForGroupWiseRegistration = rf.getFinestResolution(subjects[0][0])
            for subj in subjects:
                for i in range(len(subjects[subj])):
                    if rf.getFinestResolution(subjects[subj][i]) < resolutionForGroupWiseRegistration:
                        resolutionForGroupWiseRegistration = rf.getFinestResolution(subjects[subj][i])
        else:
            print("""Only native and lsq6 are allowed as input_space options for the registration chain. You specified: """ + str(self.options.input_space))
            print("Exiting...")
            sys.exit()
            
        
        # Due to the way the current file handling works, we should run the
        # chain part of the registrations first. In the toy scenario below: 
        # subject A    A_time_1   ->   A_time_2   ->   A_time_3
        # subject B    B_time_1   ->   B_time_2   ->   B_time_3
        # subject C    C_time_1   ->   C_time_2   ->   C_time_3
        # 
        # The following registrations are run:
        # 1) A_time_1   ->   A_time_2
        # 2) A_time_2   ->   A_time_3
        #
        # 3) B_time_1   ->   B_time_2
        # 4) B_time_2   ->   B_time_3
        #
        # 5) C_time_1   ->   C_time_2
        # 6) C_time_2   ->   C_time_3
        #
        # Prior to starting the registration chain, we will add a new group "chain"
        # to each of the file handlers. That way the transformations we later need
        # in order to determine the stats can all be retrieved from this group.
        for subjKey in subjects:
            s = subjects[subjKey]
            count = len(s)
            for i in range(count):
                s[i].newGroup(groupName = "chain")
        # now run the actual registrations
        for subjKey in subjects:
            s = subjects[subjKey]
            count = len(s) 
            for i in range(count - 1):
                if self.options.reg_method == "mincANTS":
                    register = mm.LSQ12ANTSNlin(s[i], 
                                                s[i+1],
                                                lsq12_protocol=self.options.lsq12_protocol,
                                                nlin_protocol=self.options.nlin_protocol)
                    self.pipeline.addPipeline(register.p)
                elif self.options.reg_method == "minctracc":
                    hm = mm.HierarchicalMinctracc(s[i], 
                                                  s[i+1], 
                                                  lsq12_protocol=self.options.lsq12_protocol,
                                                  nlin_protocol=self.options.nlin_protocol)
                    self.pipeline.addPipeline(hm.p)
                # Resample s[i] into space of s[i+1]. The common time point will be
                # created after this, so as like file we should use the "larger"
                # time point of the two.
                resample = ma.mincresample(s[i], s[i+1], likeFile=s[i+1], argArray=["-sinc"])
                self.pipeline.addStage(resample)
                """Invert transforms for use later in stats"""
                lastXfm = s[i].getLastXfm(s[i+1])
                inverseXfm = s[i+1].getLastXfm(s[i])
                if not inverseXfm:
                    "invert xfm and calculate"
                    xi = ma.xfmInvert(lastXfm, FH=s[i]) 
                    self.pipeline.addStage(xi)
                    s[i+1].addAndSetXfmToUse(s[i], xi.outputFiles[0])
        
        # If requested, run iterative groupwise registration for all subjects at the specified
        # common timepoint, otherwise look to see if files are specified from a previous run.
        # For example, if the avgTime is timepoint 2, the following is run in this toy scenario:
        #
        #                            ------------
        # subject A    A_time_1   -> | A_time_2 | ->   A_time_3
        # subject B    B_time_1   -> | B_time_2 | ->   B_time_3
        # subject C    C_time_1   -> | C_time_2 | ->   C_time_3
        #                            ------------
        #                                 |
        #                            group_wise registration on time point 2
        #
        if self.options.run_groupwise:
            inputs = []
            for s in subjects:
                if avgTime >= 0:
                    inputs.append(subjects[s][avgTime])
                else:  
                    # avgTime == -1:
                    lastTimePoint = len(subjects[s]) - 1
                    inputs.append(subjects[s][lastTimePoint])
            #Run full LSQ12 and NLIN modules.
            lsq12Nlin = mm.FullIterativeLSQ12Nlin(inputs, 
                                                  dirs, 
                                                  self.options, 
                                                  avgPrefix=self.options.common_name, 
                                                  initModel=initModel,
                                                  fileResolution=resolutionForGroupWiseRegistration)
            self.pipeline.addPipeline(lsq12Nlin.p)
            nlinFH = lsq12Nlin.nlinFH
        else: 
            if self.options.mbm_dir and self.options.nlin_avg:
                if (not isdir(self.options.mbm_dir)) or (not isfile(self.options.nlin_avg)):
                    logger.error("The specified MBM-directory or nlin-average do not exist.") 
                    logger.error("Specified MBM-directory: " + abspath(self.options.mbm_dir))
                    logger.error("Specified nlin average: " + abspath(self.options.nlin_avg))
                    sys.exit()
                # create file handler for nlin average
                nlinFH = rfh.RegistrationPipeFH(abspath(self.options.nlin_avg), basedir=dirs.processedDir)
                # Get transforms from subjects at avg time point to final nlin average and vice versa 
                rf.getXfms(nlinFH, subjects, "lsq6", abspath(self.options.mbm_dir), time=avgTime)
            else:
                logger.info("MBM directory and nlin_average not specified.")
                logger.info("Calculating registration chain only") 
                nlinFH = None

        """Now that all registration is complete, calculate stats, concat transforms and resample"""
        car = mm.LongitudinalStatsConcatAndResample(subjects, 
                                                    avgTime, 
                                                    nlinFH, 
                                                    self.options.stats_kernels, 
                                                    self.options.common_name) 
        self.pipeline.addPipeline(car.p)

if __name__ == "__main__":
    
    application = RegistrationChain()
    application.start()
