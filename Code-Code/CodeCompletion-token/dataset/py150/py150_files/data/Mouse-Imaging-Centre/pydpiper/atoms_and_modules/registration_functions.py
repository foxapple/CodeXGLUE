#!/usr/bin/env python

from __future__ import print_function
import atoms_and_modules.registration_file_handling as rfh
import pydpiper.file_handling as fh
from os.path import abspath, exists, dirname, splitext, isfile, basename
from os import curdir, walk
from datetime import date
import subprocess
import sys
import time
import re
import csv
import logging
import fnmatch
from pyminc.volumes.factory import volumeFromFile

logger = logging.getLogger(__name__)

def addGenRegArgumentGroup(parser):
    group = parser.add_argument_group("General registration options",
                         "General options for running various types of registrations.")
    group.add_argument("--pipeline-name", dest="pipeline_name", type=str,
                       default=time.strftime("anonymous-pipeline-%d-%m-%Y-at-%H-%m-%S"),
                       help="Name of pipeline and prefix for models.")
    group.add_argument("--input-space", dest="input_space",
                       type=str, default="native", 
                       help="Option to specify space of input-files. Can be native (default), lsq6, lsq12.")
    group.add_argument("--mask-dir", dest="mask_dir",
                       type=str, default=None, 
                       help="Directory of masks. If not specified, no masks are used. If only one mask in directory, same mask used for all inputs.")

class StandardMBMDirectories(object):
    def __init__(self):
        self.lsq6Dir = None
        self.lsq12Dir = None
        self.nlinDir = None
        self.processedDir = None

def checkInputFiles(args):
    # in order to be able to print the version number, the main application
    # class can not require to have at least 1 input file, because then specifying:
    #
    # program.py --version
    # would return:
    # "too few arguments". 
    #
    # As such the number of input files is handled using the nargs=* argument, allowing
    # for zero or more input files. That means that each application that actually requires
    # input files (not all do, some use a .csv file) needs to check this
    # Here we should check that we actually have input files 
    if len(args) < 1:
        print("\nError: no input files are provided. Exiting...\n")
        sys.exit()
    else:
        # here we should also check that the input files can be read
        issuesWithInputs = 0
        for inputF in args:
            mincinfoCmd = subprocess.Popen(["mincinfo", inputF], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
            # the following returns anything other than None, the string matched, 
            # and thus indicates that the file could not be read
            if re.search("Unable to open file", mincinfoCmd.stdout.read()):
                print("Error: can not read input file: " + str(inputF))
                issuesWithInputs = 1
        if issuesWithInputs:
            print("Error: issues reading input files. Exiting...\n")
            sys.exit()
    # lastly we should check that the actual filenames are distinct, because
    # directories are made based on the basename
    seen = set()
    for inputF in args:
        fileBase = splitext(basename(inputF))[0]
        if fileBase in seen:
            print("Error: the following name occurs at least twice in the input file list:\n" + str(fileBase) + "\nPlease provide unique names for all input files. Exiting\n")
            sys.exit()
        seen.add(fileBase)
    

def setupDirectories(outputDir, pipeName, module):
    #Setup pipeline name
    #if not pipeName:
    #    pipeName = str(date.today()) + "_pipeline"
    
    #initialize directories class:
    dirs = StandardMBMDirectories()

    fh.makedirsIgnoreExisting(outputDir)
    
    #create subdirectories based on which module is being run. _processed always created 
    dirs.processedDir = fh.createSubDir(outputDir, pipeName + "_processed", ensure_parent_exists=False)
    
    if (module == "ALL") or (module=="LSQ6"):
        dirs.lsq6Dir = fh.createSubDir(outputDir, pipeName + "_lsq6", ensure_parent_exists=False)
    if (module == "ALL") or (module=="LSQ12"):
        dirs.lsq12Dir = fh.createSubDir(outputDir, pipeName + "_lsq12", ensure_parent_exists=False)
    if (module == "ALL") or (module=="NLIN"):
        dirs.nlinDir = fh.createSubDir(outputDir, pipeName + "_nlin", ensure_parent_exists=False)
    
    return dirs
    

"""
    the "args" argument to this function must be a list.  If only
    one argument is supplied, make sure you don't pass it as a string 
"""
def initializeInputFiles(args, mainDirectory, maskDir=None):
    
    # initial error handling:  verify that at least one input file is specified 
    # and that it is a MINC file
    if(len(args) < 1):
        print("Error: no source image provided\n")
        sys.exit()
    for i in range(len(args)):
        ext = splitext(args[i])[1]
        if(re.match(".mnc", ext) == None):
            print("Error: input file is not a MINC file: %s\n" % args[i])
            sys.exit()
    
    inputs = []
    # the assumption in the following line is that args is a list
    # if that is not the case, convert it to one
    if(not(type(args) is list)):
        args = [args]
    for iFile in range(len(args)):
        inputPipeFH = rfh.RegistrationPipeFH(abspath(args[iFile]), basedir=mainDirectory)
        inputs.append(inputPipeFH)
    """After file handlers initialized, assign mask to each file
       If directory of masks is specified, apply to each file handler.
       Two options:
            1. One mask in directory --> use for all scans. 
            2. Same number of masks as files, with same naming convention. Individual
                 mask for each scan.  
    """
    if maskDir:
        absMaskPath = abspath(maskDir)
        masks = walk(absMaskPath).next()[2]
        numMasks = len(masks)
        numScans = len(inputs)
        if numMasks == 1:
                for inputFH in inputs:
                    inputFH.setMask(absMaskPath + "/" + masks[0])
        elif numMasks >= numScans:
            for m in masks:
                maskBase = fh.removeBaseAndExtension(m).split("_mask")[0]
                for inputFH in inputs:
                    if fnmatch.fnmatch(inputFH.getLastBasevol(), "*" + maskBase + "*"):
                        inputFH.setMask(absMaskPath + "/" + m)
        else:
            logger.error("Number of masks in directory does not match number of scans, but is greater than 1. Exiting...")
            sys.exit()
    else:
        logger.info("No mask directory specified as command line option. No masks included during RegistrationPipeFH initialization.")
    return inputs

def setupTwoLevelDirectories(csvFile, outputDir, pipeName, module):
    """Creates outputDir/pipelineName_firstlevel for twolevel_registration
       Within first level directory, creates _lsq6/12/nlin/processed for each subject,
       based on the name of the first file in the csv
    """
    
    if not pipeName:
        pipeName = str(date.today()) + "_pipeline"
    firstLevelDir = fh.createSubDir(outputDir, pipeName + "_firstlevel")
    fileList = open(csvFile, 'rb')
    subjectList = csv.reader(fileList, delimiter=',', skipinitialspace=True)
    subjectDirs = {} # One StandardMBMDirectories for each subject
    index = 0
    for subj in subjectList:
        base = splitext(basename(subj[0]))[0]
        dirs = setupDirectories(firstLevelDir, base, module)
        subjectDirs[index] = dirs
        index += 1    
    secondLevelDir = fh.createSubDir(outputDir, pipeName + "_secondlevel")
    dirs = setupDirectories(secondLevelDir, "second_level", "ALL")
    return (subjectDirs, dirs)   

def setupSubjectHash(csvFile, dirs, maskDir):
    """Reads in subjects from .csv and returns a hash.
       Each row of the .csv is a series of scans for a single subject."""
    fileList = open(csvFile, 'rb')
    subjectList = csv.reader(fileList, delimiter=',', skipinitialspace=True)
    subjects = {} # One array of images for each subject
    index = 0 
    for subj in subjectList:
        if isinstance(dirs, StandardMBMDirectories):
            pd = dirs.processedDir
        elif isinstance(dirs, dict):
            pd = dirs[index].processedDir
        # if the csv file is saved in a program like 
        # open office or libre office and not all subjects
        # have the same number of time point, the missing
        # time points will be saved as comma separated
        # empty fields. This causes issues when initializing
        # the input files, so we will remove them here:
        usable_time_points = []
        for singlePointInSubj in subj:
            if singlePointInSubj != '':
                usable_time_points.append(singlePointInSubj)
        subjects[index] = initializeInputFiles(usable_time_points, pd, maskDir)
        index += 1
        # reset list of usable time points
        usable_time_points = [] 
    return subjects

def getCurrIndexForInputs(subjects):
    if isinstance(subjects, dict):
        for subj in subjects:
            for i in range(len(subjects[subj])):
                s = subjects[subj]
                if subj== 0 and i == 0:
                    currentGroupIndex = s[i].currentGroupIndex
                else:
                    if s[i].currentGroupIndex != currentGroupIndex:
                        print("Current group indices do not match for all subjects after LSQ6. Exiting...")
                        sys.exit()
    else:
        print("getCurrIndexForInputs function currently only works with a dictionary. Exiting...")
        sys.exit()
        
    return currentGroupIndex

def isFileHandler(inSource, inTarget=None):
    """Source and target types can be either RegistrationPipeFH (or its base class) 
    or strings. Regardless of which is chosen, they must both be the same type.
    If this function returns True - both types are fileHandlers. If it returns
    false, both types are strings. If there is a mismatch, the assert statement
    should cause an error to be raised."""
    errorMsg = 'source and target files must both be same type: RegistrationPipeFH or string'
    if isinstance(inSource, rfh.RegistrationFHBase):
        if inTarget:
            if not isinstance(inTarget, rfh.RegistrationFHBase):
                raise Exception(errorMsg)
        return True
    else:
        if inTarget:
            if isinstance(inTarget, rfh.RegistrationFHBase):
                raise Exception(errorMsg)
        return False

def setupInitModel(inputModel, pipeName, pipeDir=None):
    """
        Creates fileHandlers for the initModel by reading files from.
        The directory where the input is specified.
        The following files and naming scheme are required:
            name.mnc --> File in standard registration space.
            name_mask.mnc --> Mask for name.mnc
        The following can optionally be included in the same directory as the above:
            name_native.mnc --> File in native scanner space.
            name_native_mask.mnc --> Mask for name_native.mnc
            name_native_to_standard.xfm --> Transform from native space to standard space

        we should make sure that files related to the initial model end up in 
        a directory named analogous to all other files, i.e., {pipeline_name}_init_model
        so we need to have the pipeName here:
    """
    errorMsg = "Failed to properly set up initModel."

    try:
        imageFile = abspath(inputModel)
        imageBase = fh.removeBaseAndExtension(imageFile)
        imageDirectory = dirname(imageFile)
        if not pipeDir:
            pipeDir = abspath(curdir)
        initModelDir = fh.createSubDir(pipeDir, pipeName + "_init_model")
        if not exists(imageFile):
            errorMsg = "Specified --init-model does not exist: " + str(inputModel)
            raise
        else:
            mask = imageDirectory + "/" + imageBase + "_mask.mnc"
            if not exists(mask):
                raise Exception("Required mask for the --init-model does not exist: " + str(mask))
            standardFH = rfh.RegistrationPipeFH(imageFile, mask=mask, basedir=initModelDir)            
            #if native file exists, create FH
            nativeFileName = imageDirectory + "/" + imageBase + "_native.mnc"
            if exists(nativeFileName):
                mask = imageDirectory + "/" + imageBase + "_native_mask.mnc"
                if not exists(mask):
                    raise Exception("_native.mnc file included but associated mask not found")
                else:
                    nativeFH = rfh.RegistrationPipeFH(nativeFileName, mask=mask, basedir=initModelDir)
                    nativeToStdXfm = imageDirectory + "/" + imageBase + "_native_to_standard.xfm"
                    if exists(nativeToStdXfm):
                        nativeFH.setLastXfm(standardFH, nativeToStdXfm)
                    else:
                        raise Exception("Your initial model directory has both native and standard files but no transformation between them; you need to supply %s_native_to_standard.xfm" % imageBase)
            else:
                nativeFH = None
                nativeToStdXfm = None
            return (standardFH, nativeFH, nativeToStdXfm)
    except:
        print(errorMsg)
        raise

def setInitialTarget(initModelOption, lsq6Target, targetFileDir, outputDir, pipeName):
    """Function checks to make sure either an init model or inital target are specified.
       Sets up and returns target and initial model."""
    if(initModelOption == None and lsq6Target == None):
        print("Error: please specify either a target file for the registration (--lsq6-target or --bootstrap), or an initial model (--init-model)\n")
        sys.exit()   
    if(initModelOption != None and lsq6Target != None):
        print("Error: please specify ONLY ONE of the following options: --lsq6-target, --bootstrap, --init-model\n")
        sys.exit()
        
    initModel = None
    if(lsq6Target != None):
        targetPipeFH = rfh.RegistrationPipeFH(abspath(lsq6Target), basedir=targetFileDir)
    else: # options.init_model != None  
        initModel = setupInitModel(initModelOption, pipeName, outputDir)
        if (initModel[1] != None):
            # we have a target in "native" space 
            targetPipeFH = initModel[1]
        else:
            # we will use the target in "standard" space
            targetPipeFH = initModel[0]
    
    return(initModel, targetPipeFH)

def getFinestResolution(inSource):
    """
        This function will return the highest (or finest) resolution 
        present in the inSource file.     
    """
    imageResolution = []
    if isFileHandler(inSource):
        # make sure that pyminc does not complain about non-existing files. During the
        # creation of the overall compute graph the following file might not exist. In
        # that case, use the inputFileName, or raise an exception
        if(isfile(inSource.getLastBasevol())):
            imageResolution = volumeFromFile(inSource.getLastBasevol()).separations
        elif(isfile(inSource.inputFileName)):
            imageResolution = volumeFromFile(inSource.inputFileName).separations
        else:
            # neither the last base volume, nor the input file name exist at this point
            # this could happen when we evaluate an average for instance
            raise
    else: 
        imageResolution = volumeFromFile(inSource).separations
    
    # the abs function does not work on lists... so we have to loop over it.  This 
    # to avoid issues with negative step sizes.  Initialize with first dimension
    finestRes = abs(imageResolution[0])
    for i in range(1, len(imageResolution)):
        if(abs(imageResolution[i]) < finestRes):
            finestRes = abs(imageResolution[i])
    
    return finestRes

def returnFinestResolution(inputFile):
    try:
        fileRes = getFinestResolution(inputFile)
        return fileRes
    except: 
        # if this fails (because file doesn't exist when pipeline is created) grab from
        # initial input volume, which should exist. 
        try:
            fileRes = getFinestResolution(inputFile.inputFileName)
            return fileRes
        except:
            print("------------------------------------------------------------------------------------")
            print("Cannot get file resolution from specified files to setup default registration protocol: " + str(inputFile.inputFileName))
            print("Please specify a registration protocol or a value for the subject matter.")
            print("------------------------------------------------------------------------------------")
            sys.exit()
    
def getXfms(nlinFH, subjects, space, mbmDir, time=None):

    """ This function retrieves the last transform from each subject 
        to a final nlin average, generated during a previously completed build model run. 
       
        subjects passed in must be a dictionary or a list. If a dictionary, function assumes
        use with registration chain code and gets transforms only for subjects at the specified
        common time point (time). Otherwise, assumes an array and gets xfms for all subjects in array.
        
        Input spaces currently allowed: lsq6, lsq12. native is allowed, but until pydpiper
        calculates the back to native xfms, it will return with an error. 
        
    """
    
    #First handle subjects if dictionary or list
    if isinstance(subjects, list):
        inputs = subjects
    elif isinstance(subjects, dict):
        inputs = []
        for s in subjects:
            inputs.append(subjects[s][time])
    else:
        logger.error("getXfms only takes a dictionary or list of subjects. Incorrect type has been passed. Exiting...")
        sys.exit()
    
    #Walk through specified directories and find appropriate transforms. 
    #Note that the names for xfms assume current pydpiper naming conventions. 
    baseNames = walk(mbmDir).next()[1]
    for b in baseNames:
        if space == "lsq6":
            xfmAvgToSubj = abspath(mbmDir + "/" + b + "/transforms/" + b + "-final-nlin_with_additional_inverted.xfm")
            xfmSubjToAvg = abspath(mbmDir + "/" + b + "/transforms/" + b + "-final-nlin_with_additional.xfm")
        elif space == "lsq12":
            xfmAvgToSubj = abspath(mbmDir + "/" + b + "/transforms/" + b + "-final-nlin_inverted.xfm")
            xfmSubjToAvg = abspath(mbmDir + "/" + b + "/transforms/" + b + "-final-nlin.xfm")    
        elif space == "native":
            logger.error("Pydpiper does not currently calculate the transforms back to native space.")
            sys.exit()
        else:
            logger.error("getXfms can only retrieve transforms to lsq6 or lsq12 space. Invalid parameter has been passed.")
            sys.exit()
        for inputFH in inputs:
            if fnmatch.fnmatch(inputFH.getLastBasevol(), "*" + b + "*"):
                nlinFH.setLastXfm(inputFH, xfmAvgToSubj)
                inputFH.newGroup(groupName="final")
                inputFH.setLastXfm(nlinFH, xfmSubjToAvg)
