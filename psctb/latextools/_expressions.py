from sympy import latex,sympify

__all__ = ['make_subs_dict',
           'make_prc_subs_dic',
           'expression_to_latex']

def make_subs_dict(mod,vars_only = True, partials =False):
    """Returns a dictionary of sympy formatted strings
    for the fluxes, control and elasticity 
    coefficients for a model 'mod'. Eg:

    For a model with 
    reactions:
    v_1, v_2
    species:
    S, x_1, P
    the dictionary will look like:

    {'J_v_1'      : 'J_v1',
     'J_v_2'      : 'J_v2',
     'ecv_1_S'   : 'varepsilon__v1_S',
     'ecv_1_x_1' : 'varepsilon__v1_x1',
     'ecv_2_x_1' : 'varepsilon__v2_x1',
     'ecv_2_P'   : 'varepsilon__v1_P',
     'ccJ_v_1_v_1': 'C__Jv1_v1',
     'ccJ_v_1_v_2': 'C__Jv1_v2',
     'ccJ_v_2_v_1': 'C__Jv2_v1',
     'ccJ_v_2_v_2': 'C__Jv2_v2',
     'ccJ_S_v_1'  : 'C__S_v1',
     'ccJ_S_v_2'  : 'C__S_v2',
     'ccJ_x_1_v_1': 'C__x1_v1',
     'ccJ_x_1_v_2': 'C__x1_v2',
     'ccJ_P_v_1': 'C__P_v1',
     'ccJ_P_v_2': 'C__P_v2'}

    }

    Used in conjunction with expression to latex, but
    might be useful on its own. 

    Arguments:
    ==========
    mod       - The model object
    vars_only - If 'False' elasticity coefficient expression for model 
                parameters are included (optional - default='True')
    """
    ec_subs = {}
    j_subs = {}
    cc_subs = {}
    rc_subs = {}
    prc_subs = {}

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

            rc_orig_expr = ('rcJ' +
                             reaction +
                             '_' +
                             species
            )
            rc_new_expr = ('R__J' +
                           reaction.replace('_','') + 
                           '_' + 
                           species.replace('_','')
            )

            rc_subs[rc_orig_expr] = [rc_new_expr]

        for reaction2 in mod.reactions:
            cc_orig_expr = ('ccJ' + 
                            reaction +
                            '_' +
                            reaction2
            )
            cc_new_expr = ('C__J' + 
                           reaction.replace('_','') + 
                           '_' + 
                           reaction2.replace('_','')
            )

            cc_subs[cc_orig_expr] = cc_new_expr
            if partials:
                for species in mod.species:
                    prc_orig_expr = ('prc' +
                                      reaction2 +
                                      '_J' +
                                      reaction +
                                      '_' +
                                      species
                    )
                    prc_new_expr = ('R__' +
                                    reaction2.replace('_','') +
                                    '__J' +
                                    reaction.replace('_','') +
                                    '_' +
                                    species.replace('_','')
                    )
                    prc_subs[prc_orig_expr] = prc_new_expr

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

        for species2 in mod.species:
            rc_orig_expr = ('rc' +
                             species2 +
                             '_' +
                             species
            )
            rc_new_expr = ('R__' +
                           species2.replace('_','') + 
                           '_' + 
                           species.replace('_','')
            )

            rc_subs[rc_orig_expr] = [rc_new_expr]


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
    subs.update(rc_subs)
    subs.update(prc_subs)


    return subs

def make_prc_subs_dic(mod):
    prc_subs = {}
    
    for reaction1 in mod.reactions:
        for reaction2 in mod.reactions:
            for species in mod.species:
                prc_orig_expr  = ('R^{'+
                                  reaction2.replace('_','')+
                                  ' J'+
                                  reaction1.replace('_','')+
                                  '}_{'+
                                  species.replace('_','')+
                                  '}'
                )
                prc_new_expr  = ('\,^{' +
                                reaction2.replace('_','')+
                                '}R^{' +
                                'J'+
                                reaction1.replace('_','')+
                                '}_{'+
                                species.replace('_','')+
                                '}'
                )
                prc_subs[prc_orig_expr] = prc_new_expr
    return prc_subs



def expression_to_latex(expression,mod=None,subs_dict=None,prc_subs_dic = None):
    """Returns a latex expression from a sympy (or string) expression
    using a subtitution dictionary generated by 'make_subs_dict(model)' 
    (or a custom dictionary). If the expression contains partial 
    response coefficients a 'prc_subs_dic' is needed as provided
    by 'make_prc_subs_dic(model)'. A model (mod) can provided instead
    to create these dictionaries automatically.
    :

    For subs_dict = {'J_v_2'  : 'J_v2',
                    'ecv_1_S': 'varepsilon__v1_S'}
    and

    expression = 'J_v_2*ec_v_1_S/10'

    the output will be:

    '\\frac{J_{v2}\\varepsilon^{v1}_{S}}{10}'

    Arguments:
    ==========
    mod          - The model 
    subs_dict    - The substitution dictionary
    expression   - The sympy or string dictionary
    prc_subs_dic - Needed if expression contains a partial response
    """
    assert mod or subs_dict, 'Must provide either a model or a subs_dict'
    if mod:
        subs_dict = make_subs_dict(mod, vars_only = False, partials=True)
        prc_subs_dic = make_prc_subs_dic(mod)
    
    if type(expression) == str:
        expr = sympify(expression)
    else:
        expr = expression

    latex_expr = latex(expr.subs(subs_dict),long_frac_ratio = 10)

    if prc_subs_dic:
        for each in prc_subs_dic:
            latex_expr = latex_expr.replace(each,prc_subs_dic[each])

    return latex_expr