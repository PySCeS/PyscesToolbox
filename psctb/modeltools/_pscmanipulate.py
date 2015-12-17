from os import path
import cStringIO
import string

from pysces import model, PyscesModel

from ._paths import get_model_name


__all__ = ['psc_to_str',
           'mod_to_str',
           'strip_fixed',
           'augment_fix_sting',
           'fix_metabolite',
           'fix_metabolite_ss']


def psc_to_str(name):
    """
    Takes a filename and returns a path of where this file should be found.

    Parameters
    ----------
    name : str
        A string containing a filename.

    Returns
    -------
    str
        A string indicating the path to a psc file.
    """
    if name[-4:] != '.psc':
        name += '.psc'
    F = file(path.join(PyscesModel.MODEL_DIR, name), 'r')
    fstr = F.read()
    F.close()
    return fstr


def mod_to_str(mod):
    """
    Converts an instantiated PySCeS model to a string.

    Parameters
    ----------
    mod : PysMod
        A Pysces model.

    Returns
    -------
    str
        A string representation of the contents of a PySCeS model file.

    """
    F = cStringIO.StringIO()
    mod.showModel(filename=F)
    fstr = F.getvalue()
    F.close()
    return fstr


def strip_fixed(fstr):
    """
    Take a psc file string and return two strings: (1) The file header
    containing the "FIX: " line and (2) the remainder of file.

    Parameters
    ----------
    fstr : str
        String representation of psc file.

    Returns
    -------
    tuple of str
        1st element contains file header, second the remainder of the file.

    See also
    --------
    psc_to_str
    mod_to_str
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


def augment_fix_sting(OrigFix, fix):
    """
    Adds a species to a psc file header.

    Parameters
    ----------
    OrigFix : str
        A psc file header
    fix : str
        Additional species to add to psc file header.

    Returns
    -------
    str
        A new psc file header that contains the contents of the original
        together with the new fixed species.
    """
    return OrigFix + ' %s' % fix


def fix_metabolite(mod, fix, model_name=None):
    """
    Fix a metabolite in a model and return a new model with the fixed
    metabolite.

    Parameters
    ----------
    mod : PysMod
        The original model.
    fix : str
        The metabolite to fix.
    model_name : str, optional (Default : none)
        The file name to use when saving the model (in psc/orca).
        If None it defaults to original_model_name_fix.

    Returns
    -------
    PysMod
        A new model instance with an additional fixed species.
    """
    assert fix in mod.species, "\nInvalid fixed species."

    if model_name is None:
        model_name = get_model_name(mod) + '_' + fix

    mod_str = mod_to_str(mod)
    fix_head, mod_str_sans_fix = strip_fixed(mod_str)
    new_fix_head = augment_fix_sting(fix_head, fix)
    new_mod = model(model_name, loader="string", fString=new_fix_head
                    + '\n' + mod_str_sans_fix)
    return new_mod


def fix_metabolite_ss(mod, fix, model_name=None):
    """
    Fix a metabolite at its steady state in a model and return a new
    model with the fixed metabolite.

    Parameters
    ----------
    mod : PysMod
        The original model.
    fix : str
        The metabolite to fix.
    model_name : str, optional (Default : none)
        The file name to use when saving the model (in psc/orca).
        If None it defaults to original_model_name_fix.

    Returns
    -------
    PysMod
        A new model instance with an additional fixed species.

    See Also
    --------
    fix_metabolite
    """
    mod.doState()
    fixed_ss = getattr(mod,fix)
    fix_mod = fix_metabolite(mod,fix,model_name)
    setattr(fix_mod,fix,fixed_ss)
    return fix_mod