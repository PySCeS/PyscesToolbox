__all__ = ['cc_list',
           'ec_list',
           'rc_list',
           'prc_list']


def cc_list(mod):
    """
    Retuns a list of control coefficients of a model.

    The list contains both flux and species control coefficients and control
    coefficients follow the syntax of 'cc_controlled_controller'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions and species which is used to
        contruct the control coefficient list.

    Returns
    -------
    values : list
        The cc_list is sorted alphabetically.

    See Also
    --------
    ec_list, rc_list, prc_list

    """
    ccs = []
    for base_reaction in mod.reactions:
        for top_species in mod.species:
            cc = 'cc%s_%s' % (top_species, base_reaction)
            ccs.append(cc)
        for top_reaction in mod.reactions:
            cc = 'ccJ%s_%s' % (top_reaction, base_reaction)
            ccs.append(cc)
    ccs.sort()

    return ccs


def ec_list(mod):
    """
    Retuns a list of elasticity coefficients of a model.

    The list contains both species and parameter elasticity coefficients and
    elasticity coefficients follow the syntax of 'ec_reaction_sp-or-param'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions, species and parameters
        which is used to contruct the elasticity coefficient list.

    Returns
    -------
    values : list
        The ec_list is sorted alphabetically.

    See Also
    --------
    cc_list, rc_list, prc_list

    """
    ecs = []
    for top_reaction in mod.reactions:
        for base_species in mod.species:
            ec = 'ec%s_%s' % (top_reaction, base_species)
            ecs.append(ec)
        for base_param in mod.parameters:
            ec = 'ec%s_%s' % (top_reaction, base_param)
            ecs.append(ec)
    ecs.sort()
    return ecs


def rc_list(mod):
    """
    Retuns a list of response coefficients of a model.

    The list contains both species and flux response coefficients and
    response coefficients follow the syntax of 'rc_responder_parameter'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions, species and parameters
        which is used to contruct the response coefficient list.

    Returns
    -------
    values : list
        The rc_list is sorted alphabetically.

    See Also
    --------
    cc_list, ec_list, prc_list

    """
    rcs = []
    for base_param in mod.parameters:
        for top_species in mod.species:
            rc = 'rc%s_%s' % (top_species, base_param)
            rcs.append(rc)
        for top_reaction in mod.reactions:
            rc = 'rcJ%s_%s' % (top_reaction, base_param)
            rcs.append(rc)
    rcs.sort()
    return rcs


def prc_list(mod):
    """
    Retuns a list of partial response coefficients of a model.

    The list contains both species and flux partial response coefficients and
    partial response coefficients follow the syntax of
    'prc_responder_parameter_route'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions, species and parameters
        which is used to contruct the partial response coefficient list.

    Returns
    -------
    values : list
        The prc_list is sorted alphabetically.

    See Also
    --------
    cc_list, ec_list, rc_list

    """
    prcs = []
    for base_param in mod.parameters:
        for back_reaction in mod.reactions:
            for top_species in mod.species:
                prc = 'prc%s_%s_%s' % (top_species, base_param, back_reaction)
                prcs.append(prc)
            for top_reaction in mod.reactions:
                prc = 'prcJ%s_%s_%s' % (top_reaction,
                                        base_param,
                                        back_reaction)
                prcs.append(prc)
    prcs.sort()
    return prcs
