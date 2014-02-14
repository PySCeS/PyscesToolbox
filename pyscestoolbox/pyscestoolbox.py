from os import path, mkdir
from sympy import latex,sympify
from pysces import model
import cStringIO,string


def make_path(mod,subdir,subsubdir = None):
    base_dir = mod.ModelOutput
    main_dir = base_dir + '/' + subdir
    mod_dir = main_dir + '/' + mod.ModelFile[:-4]
    if not path.exists(main_dir):
        mkdir(main_dir)
    if not path.exists(mod_dir):
        mkdir(mod_dir)
    if subsubdir:
        branch_dir = mod_dir + '/' + subsubdir
        if not path.exists(branch_dir):
            mkdir(branch_dir)
        return branch_dir + '/'
    else:
        return mod_dir + '/'


def make_subs_dict(mod,vars_only = True):
    ec_subs = {}
    j_subs = {}
    cc_subs = {}

    for reaction in mod.reactions:
        j_subs['J' + reaction] = 'J_' + reaction.replace('_','')
        
        for species in mod.species:
            ec_orig_expr = ('ec' +
                            reaction + 
                            '_' + 
                            species
            )
            ec_new_expr = ('varepsilon__' +  
                           reaction.replace('_','') + 
                           '_' + 
                           species.replace('_','')
            )  

            ec_subs[ec_orig_expr] = ec_new_expr 

        for each in mod.reactions:
            cc_orig_expr = ('ccJ' + 
                            reaction +
                            '_' +
                            each
            )
            cc_new_expr = ('C__J' + 
                           reaction.replace('_','') + 
                           '_' + 
                           each.replace('_','')
            )

            cc_subs[cc_orig_expr] = cc_new_expr

    for species in mod.species: 
        for reaction in mod.reactions:
            cc_orig_expr = ('cc' +
                            species + 
                            '_' + 
                            reaction
            )
            cc_new_expr = ('C__' +
                           species.replace('_','') + 
                           '_' +
                           reaction.replace('_','')
            )
            
            cc_subs[cc_orig_expr] = cc_new_expr

    if vars_only == False:
        for reaction in mod.reactions:
            for param in mod.parameters:
                ec_orig_expr = ('ec' +
                            reaction + 
                            '_' + 
                            param
                )
                ec_new_expr = ('varepsilon__' +  
                               reaction.replace('_','') + 
                               '_' + 
                               param.replace('_','')
                )  

                ec_subs[ec_orig_expr] = ec_new_expr

    subs = {}
    subs.update(ec_subs)
    subs.update(cc_subs)
    subs.update(j_subs)

    return subs


def expression_to_latex(subs_dict,expression):
    if type(expression) == str:
        expr = sympify(expression)
    else:
        expr = expression

    latex_expr = latex(expr.subs(subs_dict),long_frac_ratio = 10)

    return latex_expr


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


def strip_fixed( fstr):
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
        model_name = mod.ModelFile[:-4] + '_' + fix

    mod_str = mod_to_str(mod)
    fix_head, mod_str_sans_fix = strip_fixed(mod_str)
    new_fix_head = augment_fix_sting(fix_head, fix)
    new_mod = model(model_name, loader="string", fString=new_fix_head
        +'\n'+mod_str_sans_fix)
    return new_mod