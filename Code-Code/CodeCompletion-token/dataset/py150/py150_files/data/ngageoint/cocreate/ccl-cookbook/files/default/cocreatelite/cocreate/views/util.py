from ..models import VMPlayground, VMSandbox
from django.conf import settings
import re

def fillContext(opts, req):
    """
    Given a set of already filled in options for a context render, fill in some of the additional
    details.
    """
    nopts = {
        "version": settings.VERSION,
        "request": req
    }
    
    for (k, v) in nopts.items():
        if k not in opts:
            opts[k] = v
    return opts

def generateLogicalName(baseName):
    """
    Turn a human readable name into a logical name for an instance hostname
    """
    
    # turn it into something sane
    baseName = re.sub(r'\W', '', baseName).lower()
    
    # check against known names?
    conflicts = VMSandbox.objects.filter(logical_name__startswith = baseName)
    
    if len(conflicts) == 0:
        return baseName
    else:
        
        # let's find a suitable name
        names = [vms.logical_name for vms in conflicts]
        
        if baseName not in names:
            return baseName
        else:
            # try variants until we find one
            counter = 1
            
            newBaseName = "%s_%d" % (baseName, counter)
            while newBaseName in names:
                counter += 1
                newBaseName = "%s_%d" % (baseName, counter)
            
            return newBaseName