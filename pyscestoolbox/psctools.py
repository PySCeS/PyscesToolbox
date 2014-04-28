from os import path, mkdir
from pysces import model, model_dir, output_dir
import cStringIO,string

def get_model_name(mod):
    """Returns the name of a model 'mod' sans the extension

    Arguments:
    ==========
    mod             - The model of interest
    """
    return path.split(mod.ModelFile)[1][:-4]


def make_path(mod,analysis_method,subdirs = []):
    """
    make_path(mod,analysis_method,subdirs = [])

    This function is used to create directories 
    (if they don't exist) to write analysis
    results to and return the path name. The 
    return value will be:

    /path/to/Pysces/model_name/analysis_method/subdir1/subdir2/

    Arguments:
    ==========
    mod             - The model being analysed 
    analysis_method - The tool being used to analyse the model
    subdirs         - An optional list of subdirectories


    """

    model_name = path.split(mod.ModelFile)[1][:-4]
    
    model_path = path.join(output_dir,
                           model_name)

    analysis_path = path.join(output_dir,
                              model_name,
                              analysis_method)

    dirs = [model_path,analysis_path]

    for i,each in enumerate(subdirs):
        tpth = path.join(dirs[1+i], each)
        dirs.append(tpth)

    for each in dirs:
        if not path.exists(each):
            mkdir(each)

    return dirs[-1] + '/'



def psc_to_str(name):
    """
    psc_to_str(name)

    Read psc file and return as string

    Arguments:
    ==========
    name - string containing filename
    """
    if name[-4:] != '.psc':
        name += '.psc'
    F = file(os.path.join(pysces.PyscesModel.MODEL_DIR, name),'r')
    fstr = F.read()
    F.close()
    return fstr


def mod_to_str(mod):
    """
    mod_to_str(name)

    Write PySCeS model out to string

    Arguments:
    ==========
    mod - instantiated PySCeS model
    """
    F = cStringIO.StringIO()
    mod.showModel(filename=F)
    fstr = F.getvalue()
    F.close()
    return fstr


def strip_fixed(fstr):
    """
    strip_fixed(fstr)

    Take a psc file string and return (Fhead, stripped_fstr)
    where Fhead is the file header containing the "FIX: " line
    and stripped_fstr is remainder of file as string

    Arguments:
    ==========
    fstr - string representation of psc file

    See also:
    =========
    psc_to_str(name)
    """
    Fi = cStringIO.StringIO()
    Fi.write(fstr)
    Fi.seek(0)
    Fo = cStringIO.StringIO()
    Fhead = None
    for line in Fi:
        if line[:4] == "FIX:":
            Fhead = string.strip(line)
            Fo.write('\n')
        else:
            Fo.write(line)
    Fo.seek(0)
    return Fhead, Fo.read()


def augment_fix_sting( OrigFix, fix):
    """
    augment_fix_sting(OrigFix, fix)

    Add fix to FixString

    Arguments:
    ==========
    OrigFix - original FixString
    fix     - additional species to add to FixString
    """
    return OrigFix + ' %s' % fix


def fix_metabolite(mod, fix, model_name = 0):
    """
    fix_metabolite(mod,fix,modelname)

    Fix a metabolite in a model and return a new model with the fixed
    metabolite.

    Arguments:
    ==========
    mod         - The original model
    fix         - The metabolite to fix
    model_name  - The file name to use when saving the model (in psc/orca).
                  The default value is original_model_name_fix.
    """

    assert fix in mod.species, "\nInvalid fixed species."

    if model_name == 0:
        model_name = path.split(mod.ModelFile)[1][:-4] + '_' + fix

    mod_str = mod_to_str(mod)
    fix_head, mod_str_sans_fix = strip_fixed(mod_str)
    new_fix_head = augment_fix_sting(fix_head, fix)
    new_mod = model(model_name, loader="string", fString=new_fix_head
        +'\n'+mod_str_sans_fix)
    return new_mod