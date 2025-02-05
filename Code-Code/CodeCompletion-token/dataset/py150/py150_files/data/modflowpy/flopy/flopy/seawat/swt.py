from ..mbase import BaseModel
from ..pakbase import Package
from .swtvdf import SeawatVdf
import os

class SeawatList(Package):
    """
    List Package class
    """
    def __init__(self, model, extension='list'):
        #Call ancestor's init to set self.parent, extension, name and 
        #unit number
        Package.__init__(self, model, extension, 'LIST', 7) 
        #self.parent.add_package(self) This package is not added to the base 
        #model so that it is not included in get_name_file_entries()
        return

    def __repr__( self ):
        return 'List package class'

    def write_file(self):
        # Not implemented for list class
        return

class Seawat(BaseModel):
    '''
    SEAWAT base class
    '''
    def __init__(self, modelname='mt3dmstest', namefile_ext='nam', 
                 modflowmodel=None, mt3dmsmodel=None, 
                 version='seawat', exe_name='swt_v4.exe', model_ws = None,
                 verbose=False, external_path=None):
        BaseModel.__init__(self, modelname, namefile_ext, exe_name=exe_name, 
                           model_ws=model_ws)

        self.version_types = {'seawat': 'SEAWAT'}
        self.set_version(version)

        self.__mf = modflowmodel
        self.__mt = mt3dmsmodel
        self.lst = SeawatList(self)
        self.__vdf = None
        self.verbose = verbose
        self.external_path = external_path
        return
        
    def __repr__( self ):
        return 'SEAWAT model'

    def getvdf(self):
        if (self.__vdf == None):
            for p in (self.packagelist):
                if isinstance(p, SeawatVdf):
                    self.__vdf = p
        return self.__vdf

    def getmf(self):
        return self.__mf

    def getmt(self):
        return self.__mt

    mf = property(getmf) # Property has no setter, so read-only
    mt = property(getmt) # Property has no setter, so read-only
    vdf = property(getvdf) # Property has no setter, so read-only

    def write_name_file(self):
        """
        Write the name file

        Returns
        -------
        None

        """
        fn_path = os.path.join(self.model_ws,self.namefile)
        f_nam = open(fn_path, 'w')
        f_nam.write('%s\n' % (self.heading) )
        f_nam.write('%s\t%3i\t%s\n' % (self.lst.name[0], 
                                       self.lst.unit_number[0], 
                                       self.lst.file_name[0]))
        f_nam.write('%s\n' % ('# Flow') )
        f_nam.write('%s' % self.__mf.get_name_file_entries())
        for u,f in zip(self.mf.external_units,self.mf.external_fnames):
            f_nam.write('DATA  {0:3d}  '.format(u)+f+'\n'	)
        f_nam.write('%s\n' % ('# Transport') )
        f_nam.write('%s' % self.__mt.get_name_file_entries())
        for u,f in zip(self.mt.external_units,self.mt.external_fnames):
            f_nam.write('DATA  {0:3d}  '.format(u)+f+'\n'	)
        f_nam.write('%s\n' % ('# Variable density flow') )
        f_nam.write('%s' % self.get_name_file_entries())
        f_nam.close()
        return