from os import path
from re import match, findall, sub

import pysces
from sympy import Symbol, sympify
from datetime import datetime



# File reading/validation functions
def get_term_types_from_raw_data(raw_data_dict):
    """
    Determines the types of terms defined for ThermoKin based on the
    file contents. This allows for generation of latex expressions
    based on these terms.

    Parameters
    ----------
    raw_data_dict : dict of str:{str:str}

    Returns
    -------
    set of str

    """
    term_types = set()
    for v in raw_data_dict.itervalues():
        for k in v.iterkeys():
            term_types.add(k)
    return term_types


class FormatException(Exception):
    pass


def read_reqn_file(path_to_file):
    """
    Reads the contents of a file and returns it as a list of lines.

    Parameters
    ----------
    path_to_file : str
        Path to file that is to read in

    Returns
    -------
    list of str
        The file contents as separate strings in a list

    """
    with open(path_to_file) as f:
        lines = f.readlines()
    return lines


def get_terms(raw_lines, term_type):
    """
    Takes a list of strings and returns a new list containing only
    lines starting with `term_type` and strips line endings.

    Term can be either of the "main" (or `!T`) type or additional (or
    `!G`) type

    Parameters
    ----------
    raw_lines : list of str
        List of lines from a '.reqn' file.
    term_type : str
        This string specifies the type of term.

    Returns
    -------
    list of str
    """
    assert term_type == '!T' or term_type == '!G', 'Invalid term type specified'
    valid_prefix_lines = [line for line in raw_lines if line.startswith(term_type)]
    no_line_endings = []
    for line in valid_prefix_lines:
        if line[-1] == '\n':
            no_line_endings.append(line[:-1])
        else:
            no_line_endings.append(line)
    return no_line_endings


def check_term_format(lines, term_type):
    """
    Inspects a list of string for the correct ThermoKin syntax. Returns
    `True` in case of correct format. Throws exception otherwise.

    Correct format is a str matching the pattern "X{\w*}{\w*} .*" . Where
    "X" is either "!G" or "!T" as specified by `term_type`.

    Parameters
    ----------
    lines : list of str
        Clean list of lines from a '.reqn' file.

    term_type : str
        This string specifies the type of term.

    Returns
    -------
    bool

    """
    assert term_type == '!T' or term_type == '!G', 'Invalid term type specified'
    errors_in = []
    for i, line in enumerate(lines):
        if not match(term_type + '{\w*}{\w*} .*', line):
            errors_in.append(str(i))
    if len(errors_in) == 0:
        return True
    else:
        error_str = ', '.join(errors_in)
        raise FormatException('Incorrect syntax in lines:' + error_str)


def construct_dict(lines):
    """
    Constructs a dictionary of dictionaries for each reaction.

    Here keys of the outer dictionary is reaction name strings while
    the inner dictionary keys are the term names. The inner dictionary
    values are the term expressions

    Parameters
    ----------
    lines : list of str

    Returns
    -------
    dict of str:{str:str}
    """
    outer_dict = {}
    for line in lines:
        in_brackets = findall('(?<={)\w+', line)
        r_name = in_brackets[0]
        t_name = in_brackets[1]
        expr = findall('(?<=\w} ).*', line)[0]

        inner_dict = {t_name: expr}
        if r_name in outer_dict:
            outer_dict[r_name].update(inner_dict)
        else:
            outer_dict[r_name] = inner_dict
    return outer_dict


def get_subs_dict(expression, mod):
    """
    Builds a substitution dictionary of an expression based of the
    values of these symbols in a model.

    Parameters
    ----------
    expression : sympy expression
    mod : PysMod

    Returns
    -------
    dict of sympy.Symbol:float

    """
    subs_dict = {}
    symbols = expression.atoms(Symbol)
    for symbol in symbols:
        attr = str(symbol)
        subs_dict[attr] = getattr(mod, attr)
    return subs_dict


def get_reqn_path(mod):
    """
    Gets the default path and filename of`.reqn` files belonging to a model

    The `.reqn` files which contain rate equations split into different
    (arbitrary) components should be saved in the same directory as the model
    file itself by default. It should have the same filename (sans extension)
    as the model file.

    Parameters
    ----------
    mod : PysMod
        A pysces model which has corresponding `.reqn` file saved in the same
        directory with the same file name as the model file.

    Returns
    -------
    str
        A sting with the path and filename of the `.reqn` file.
    """

    fname = mod.ModelFile
    dot_loc = fname.find('.')
    fname_min_ext = fname[:dot_loc]
    fname_ext = fname_min_ext + '.reqn'
    return path.join(mod.ModelDir, fname_ext)


def get_term_dict(raw_lines, term_type):
    """
    Returns the term dictionary from a list of raw lines from a file.

    The contents of a '.reqn' file is read and passed to this function.
    Here the contents is parsed and 'main terms' are extracted and
    returned as a dict of str:{str:str}.

    Parameters
    ----------
    raw_lines : list of str
        List of lines from a '.reqn' file.

    Returns
    -------
    dict of str:{str:str}
    """
    clean_terms = get_terms(raw_lines, term_type)
    if check_term_format(clean_terms, term_type):
        term_dict = construct_dict(clean_terms)
        return term_dict


def get_all_terms(path_to_read):
    raw_lines = read_reqn_file(path_to_read)
    main_terms = get_term_dict(raw_lines, '!T')
    add_terms = get_term_dict(raw_lines, '!G')
    return  main_terms, add_terms




# File writing/validation functions
def get_str_formulas(mod):
    """
    Returns a dictionary with reaction_name:string_formula as  key:value
    pairs.

    Goes through mod.reactions and constructs a dictionary where
    reaction_name is the key and mod.reaction_name.formula is  the
    value.

    Parameters
    ----------
    mod : PysMod
        The model which will be used to construct the dictionary

    Returns
    -------
    dict of str:str
        A dictionary with reaction_name:string_formula as
        key:value pairs

    """
    string_formulas = {}
    for reaction in mod.reactions:
        string_formulas[reaction] = getattr(mod, reaction).formula
    return string_formulas


def replace_pow(str_formulas):
    """
    Creates new dict from an existing dict with "pow(x,y)" in values
    replaced with "x**y".

    Goes through the values of an dictionary and uses regex to convert
    the pysces internal syntax for powers with  standard python syntax.
    This is needed before conversion to sympy expressions. This use case
    requires reaction  names as they appear in pysces as keys.

    Parameters
    ----------
    str_formulas : dict of str:str
        A dictionary where the values as contain pysces format strings
        representing rate equation expressions with powers in the syntax
        "pow(x,y)"

    Returns
    -------
    dict of str:str
        A new dictionary with str rate equations where powers are
        represented by standard python syntax e.g. x**y

    """
    new_str_formulas = {}
    for k, v in str_formulas.iteritems():
        new_str_formulas[k] = sub(r'pow\((\S*?),(\S*?)\)', r'\1**\2', v)
    return new_str_formulas


def get_sympy_formulas(str_formulas):
    """
    Converts dict with str values to sympy expression values.

    Used to convert key:string_formula to key:sympy_formula. Intended
    use case is for automatic separation of rate equation terms into
    mass action and binding terms. This  use case requires reaction
    names as they appear in  pysces as keys.

    Parameters
    ----------
    str_formulas : dict of str:str
        Dictionary with str values that represent reaction expressions.
        This dictionary needs to have already  passed through all
        sanitising functions/methods (e.g. `replace_pow`).

    Returns
    -------
    dict with sympy_expression values and original keys
        Dictionary where values are symbolic sympy expressions

    """
    return {k: sympify(v) for (k, v) in str_formulas.items()}


def get_sympy_terms(sympy_formulas):
    """
    Converts a dict with sympy expressions as values to a new dict with
    list values containing either the  original expression or a negative
    and a positive  expressions.

    This is used to separate reversible and irreversible  reactions.
    Reversible reactions will have two terms, one negative and one
    positive. Here expressions are expanded and split into terms and
    tested for the  above criteria: If met the dict value will be a list
    of two expressions, each representing a term of the  rate equation.
    Otherwise the dict value will be a list with a single item - the
    original expression. This  use case requires reaction names as they
    appear  in pysces as keys.

    Parameters
    ----------
    sympy_formulas : dict of str:sympy expression values
        Dictionary with values representing rate equations as sympy
        expressions. Keys are reaction names

    Returns
    -------
    dict of str:list sympy expression
        Each list will have either have one item, the original dict
        value OR two items -the original dict value split into a
        negative and positive expression.

    See Also
    --------
    check_for_negatives
    """
    sympy_terms = {}
    for name, formula in sympy_formulas.iteritems():
        terms = formula.expand().as_coeff_add()[1]
        if len(terms) == 2 and check_for_negatives(terms):
            sympy_terms[name] = terms
        else:
            sympy_terms[name] = [formula.factor()]
    return sympy_terms


def get_ma_terms(mod, sympy_terms):
    """
    Returns dict with reaction names as keys and mass action terms as
    values from a dict with reaction names as keys and lists of sympy
    expressions as values.

    Only reversible reactions are handled. Any list in the ``sympy_terms``
    dict that does not have a length of 2 will be ignored.

    Parameters
    ----------
    mod : PysMod
        The model from which the `sympy_terms` dict was originally
        constructed.
    sympy_terms: dict of str:list of sympy expressions
        This dictionary should be created by `get_sympy_terms`.

    Returns
    -------
    dict of str:sympy expression
        Each value will be a mass action term for each reaction key with
        a form depending on reversibility as described above.

    See Also
    --------
    get_st_pt_keq
    get_sympy_terms
    sort_terms
    """
    model_map = pysces.ModelMap(mod)  # model map to get substrates, products
    # and parameters for each reaction

    messages = {}
    ma_terms = {}
    for name, terms in sympy_terms.iteritems():
        reaction_map = getattr(model_map, name)

        substrates = [sympify(substrate) for substrate in
                      reaction_map.hasSubstrates()]

        products = [sympify(product) for product in reaction_map.hasProducts()]

        if len(terms) == 2:  # condition for reversible reactions
            # make sure negative term is second in term list
            terms = sort_terms(terms)
            # divide pos term by neg term and factorise
            expressions = (-terms[0] / terms[1]).factor()
            # get substrate, product and keq terms (and strategy)
            st, pt, keq, message = get_st_pt_keq(expressions, substrates,
                                                 products)
            if all([st, pt, keq]):
                ma_terms[name] = st - pt / keq
            messages[name] = message
        else:
            messages[
                name] = 'rate equation not included - irreversible or unknown form'
    return ma_terms, messages


def get_st_pt_keq(expression, substrates, products):
    """
    Takes an expression representing "substrates/products *
    Keq_expression" and returns substrates, products and keq_expression
    separately.


    Parameters
    ----------
    expression : sympy expression
        The expression containing "substrates/products * Keq_expression"
    substrates : list of sympy symbols
        List with symbolic representations for each substrate involved
        in the reaction which `expression` represents.
    products : list of sympy symbols
        List with symbolic representations for each product involved in
        the reaction which `expression` represents.
        Returns
    -------
    tuple of sympy expressions and int
        This tuple contains sympy expressions for the substrates,
        products and keq_expression in that order. The final value will
        be an int which indicates the strategy followed.

    See Also
    --------
    st_pt_keq_from_expression

    """

    res = st_pt_keq_from_expression(expression,
                                    substrates,
                                    products)
    subs_term, prod_term, keq, message = res

    return subs_term, prod_term, keq, message


def st_pt_keq_from_expression(expression, substrates, products,
                              failure_threshold=10):
    """
    Take an expression representing "substrates/products *
    Keq_expression" and returns substrates, products and keq_expression
    separately.

    In this strategy there is no inspection of the stoichiometry as
    provided by the model map. Here the expressions is
    divided/multiplied by each substrate/product until it no longer
    appears in the expression. If the substrates or products are not
    removed after a defined number of attempts a total failure occurs
    and the function returns `None`

    This is a fallback for cases where
    defined stoichiometry does not correspond to the actual rate
    equation.

    Here cases where the substrate/product do not appear in the rate
    equation at all throws an assertion error.

    Parameters
    ----------
    expression : sympy expression
        The expression containing "substrates/products * Keq_expression"
    substrates : list of sympy symbols
        List with symbolic representations for each substrate involved
        in the reaction which `expression` represents.
    products : list of sympy symbols
        List with symbolic representations for each product involved in
        the reaction which `expression` represents.
    failure_threshold : int, optional (Default: 10)
        A threshold value the defines the number of times the metabolite
        removal strategy should be tried before failure.

    Returns
    -------
    tuple of sympy_expressions or `None`
        This tuple contains sympy expressions for the substrates,
        products and keq_expression in that order. None is returned if
        this strategy fails.

    """
    new_expression = expression
    subs_term = 1
    prod_term = 1
    fail = False
    message = 'successful separation of rate equation terms'
    # Remove substrates from expression by division
    # Each division multiplies subs_term with substrate
    for substrate in substrates:
        # divide expr by subs while subs in expr
        if substrate not in new_expression.atoms(Symbol):
            fail = True
            message = 'failure: substrate %s not in rate equation' % str(
                substrate)
            break
        tries = 0
        while substrate in new_expression.atoms(Symbol):
            new_expression = new_expression / substrate
            subs_term *= substrate
            tries += 1
            if tries > failure_threshold:
                message = 'failure: cannot remove substrate %s from rate equation' % str(
                    substrate)
                fail = True
                break
        if fail:
            break
    # Same as above but for products
    # Product removed by multiplication
    if not fail:
        for product in products:
            if product not in new_expression.atoms(Symbol):
                fail = True
                message = 'failure: product %s not in rate equation' % str(
                    product)
                break
            tries = 0
            while product in new_expression.atoms(Symbol):
                new_expression = new_expression * product
                prod_term *= product
                tries += 1
                if tries > failure_threshold:
                    message = 'failure: cannot remove product %s from rate equation' % str(
                        product)
                    fail = True
                    break
            if fail:
                break
    keq = new_expression.subs({1.0: 1})
    if fail:
        return 0, 0, 0, message
    else:
        return subs_term, prod_term, keq, message


def sort_terms(terms):
    """
    Returns a list of two sympy expressions where the expression is
    positive and the second expression is negative.

    Parameters
    ----------
    terms : list of sympy expressions
        A list with length of 2 where one element is positive and
        the other is negative (starts with a minus symbol)

    Returns
    -------
    tuple of sympy expressions
        A tuple where the first element is positive and the
        second is negative.
    """

    neg = None
    pos = None
    for term in terms:
        if str(term)[0] == '-':  # negative terms should start with a '-'
            neg = term
        else:
            pos = term
    assert neg, 'No negative terms ' + str(terms)
    assert pos, 'No positive terms ' + str(terms)
    return pos, neg


def get_binding_vc_terms(sympy_formulas, ma_terms):
    """
    Returns dictionary with a combined "rate capacity" and "binding"
    term as values.

    Uses the symbolic rate equations dictionary and mass action term
    dictionaries to construct a new dictionary with "rate capacity-
    binding" terms. The symbolic rate equations are divided by their
    mass action terms. The results are the "rate capacity-binding"
    terms. This use case requires reaction names as they appear in
    pysces as keys for both dictionaries.

    Parameters
    ----------
    sympy_formulas : dict of str:sympy expression

        Full rate equations for all reactions in model. Keys are
        reaction names and correspond to this in `ma_terms`.

    ma_terms : dict of str:sympy expression

        Mass action terms for all reactions in model. Keys are reaction
        names and correspond to this in `sympy_formulas`.

    Returns
    -------
    dict of str:sympy expression
        A dictionary with reaction names as keys and sympy
        expressions representing "rate capacity-binding"
        terms as values.
    """
    binding_terms = {}
    for name, ma_term in ma_terms.iteritems():
        binding_terms[name] = (sympy_formulas[name] / ma_term).factor().factor()
    return binding_terms


def check_for_negatives(terms):
    """
    Returns `True` for a list of sympy expressions contains any
    expressions that are negative.

    Parameters
    ----------
    terms : list of sympy expressions
        A list where expressions may be either positive or  negative.

    Returns
    -------
    bool
        `True` if any negative terms in expression. Otherwise
        `False`

    """
    any_negs = False
    for term in terms:
        if str(term)[0] == '-':
            any_negs = True
    return any_negs


def create_reqn_data(mod):
    string_formulas = get_str_formulas(mod)
    string_formulas = replace_pow(string_formulas)
    sympy_formulas = get_sympy_formulas(string_formulas)
    sympy_terms = get_sympy_terms(sympy_formulas)
    non_irr = filter_irreversible(sympy_terms)
    gamma_keq_terms, _ = get_gamma_keq_terms(mod, non_irr)
    ma_terms, messages = get_ma_terms(mod, sympy_terms)
    binding_vc_terms = get_binding_vc_terms(sympy_formulas, ma_terms)
    return ma_terms, binding_vc_terms, gamma_keq_terms, messages


def create_gamma_keq_reqn_data(mod):
    string_formulas = get_str_formulas(mod)
    string_formulas = replace_pow(string_formulas)
    sympy_formulas = get_sympy_formulas(string_formulas)
    sympy_terms = get_sympy_terms(sympy_formulas)
    sympy_terms = filter_irreversible(sympy_terms)
    gamma_keq, messages = get_gamma_keq_terms(mod, sympy_terms)
    return gamma_keq, messages


def get_gamma_keq_terms(mod, sympy_terms):
    model_map = pysces.ModelMap(mod)  # model map to get substrates, products
    # and parameters for each reaction

    messages = {}
    gamma_keq_terms = {}
    for name, terms in sympy_terms.iteritems():
        reaction_map = getattr(model_map, name)

        substrates = [sympify(substrate) for substrate in
                      reaction_map.hasSubstrates()]

        products = [sympify(product) for product in reaction_map.hasProducts()]

        if len(terms) == 2:  # condition for reversible reactions
            # make sure negative term is second in term list
            terms = sort_terms(terms)
            # divide pos term by neg term and factorise
            expressions = (-terms[0] / terms[1]).factor()
            # get substrate, product and keq terms (and strategy)
            st, pt, keq, _ = get_st_pt_keq(expressions, substrates,
                                                 products)
            if all([st, pt, keq]):
                gamma_keq_terms[name] = pt / (keq*st)
                messages[name] = 'successful generation of gamma/keq term'
            else:
                messages[name] = 'generation of gamma/keq term failed'

    return gamma_keq_terms, messages


def filter_irreversible(sympy_terms):
    new_sympy_terms = {}
    for k, v in sympy_terms.iteritems():
        if len(v) == 2:
            new_sympy_terms[k] = v
    return new_sympy_terms


def write_reqn_file(file_name, model_name, ma_terms, vc_binding_terms, gamma_keq_terms, messages):
    already_written = []
    date = datetime.strftime(datetime.now(), '%H:%M:%S %d-%m-%Y')
    with open(file_name, 'w') as f:
        f.write('# Automatically parsed and split rate equations for model: %s\n' % model_name)
        f.write('# generated on: %s\n\n' % date)
        f.write('# Note that this is a best effort attempt that is highly dependent\n')
        f.write('# on the form of the rate equations as defined in the model file.\n')
        f.write('# Check correctness before use.\n\n')
        for reaction_name, ma_term in ma_terms.iteritems():
            already_written.append(reaction_name)
            f.write('# %s :%s\n' % (reaction_name, messages[reaction_name]))
            f.write('!T{%s}{ma} %s\n' % (reaction_name, ma_term))
            f.write('!T{%s}{bind_vc} %s\n' % (
                reaction_name, vc_binding_terms[reaction_name]))
            f.write('!G{%s}{gamma_keq} %s\n' % (reaction_name, gamma_keq_terms[reaction_name]))
            f.write('\n')
        for k, v in messages.iteritems():
            if k not in already_written:
                f.write('# %s :%s\n' % (k, v))


def term_to_file(file_name, expression, parent_name=None, term_name=None ):
    date = datetime.strftime(datetime.now(), '%H:%M:%S %d-%m-%Y')
    if not parent_name:
        parent_name = 'undefined'
    if not term_name:
        term_name = 'undefined'
    with open(file_name,'a') as f:
        f.write('\n')
        f.write('# Additional term appended on %s\n' % date)
        if 'undefined' in (term_name,parent_name):
            print 'Warning: writing partially defined term to %s. Please inspect file for further details.' % file_name
            f.write('# The term below is partially defined - fix term manually by defining reaction and term names\n')
        f.write('!G{%s}{%s} %s\n' % (parent_name,
                                     term_name,
                                     expression))





# There functions are not used anymore
#
# def get_gamma_keq_terms(mod, sympy_terms):
#     model_map = pysces.ModelMap(mod)  # model map to get substrates, products
#     # and parameters for each reaction
#
#     messages = {}
#     gamma_keq_terms = {}
#     for name, terms in sympy_terms.iteritems():
#         reaction_map = getattr(model_map, name)
#
#         substrates = [sympify(substrate) for substrate in
#                       reaction_map.hasSubstrates()]
#
#         products = [sympify(product) for product in reaction_map.hasProducts()]
#
#         if len(terms) == 2:  # condition for reversible reactions
#             # make sure negative term is second in term list
#             terms = sort_terms(terms)
#             # divide pos term by neg term and factorise
#             expressions = (-terms[0] / terms[1]).factor()
#             # get substrate, product and keq terms (and strategy)
#             st, pt, keq, _ = get_st_pt_keq(expressions, substrates,
#                                                  products)
#             if all([st, pt, keq]):
#                 gamma_keq_terms[name] = pt / (keq*st)
#                 messages[name] = 'successful generation of gamma/keq term'
#             else:
#                 messages[name] = 'generation of gamma/keq term failed'
#
#     return gamma_keq_terms, messages
#
# def create_gamma_keq_reqn_data(mod):
#     string_formulas = get_str_formulas(mod)
#     string_formulas = replace_pow(string_formulas)
#     sympy_formulas = get_sympy_formulas(string_formulas)
#     sympy_terms = get_sympy_terms(sympy_formulas)
#     sympy_terms = filter_irreversible(sympy_terms)
#     gamma_keq, messages = get_gamma_keq_terms(mod, sympy_terms)
#     return  gamma_keq, messages
#
# def get_irr_ma(expression, parameters, substrates, stoichiometry):
#     """
#     Returns a mass action expression for an irreversible reaction (which
#     simply consists of substrates).
#
#     Here two strategies are tried - if both fail, the answer from the
#     first strategy is used. For details refer to functions mentioned
#     under `See Also`.
#
#     Parameters
#     ----------
#     expression : sympy expression
#         A sympy expression representing a rate equation of an
#         irreversible reaction.
#     parameters : list of sympy symbols
#         List with symbolic representations for each parameter involved
#         in the reaction which `expression` represents.
#     substrates : list of sympy symbols
#         List with symbolic representations for each substrate involved
#         in the reaction which `expression` represents.
#     stoichiometry : dict of sympy.Symbol:float
#         Symbolic representations of the substrates and products are used
#         for the keys of this dict while the stoichiometric coefficient
#         values are floats.
#
#
#     Returns
#     -------
#     tuple of sympy expression and int
#         Symbolic expression for the mass action term of the irreversible
#         reaction and an integer indicating the strategy used.
#
#     See Also
#     --------
#     irr_ma_from_coeffs
#     irr_ma_from_expression
#     """
#     # strategy 1
#     strategy = 1
#     substrate_term = irr_ma_from_coeffs(substrates, stoichiometry)
#     valid = validate_irr_ma(expression, substrate_term)
#     if not valid:
#         # fallback strategy
#         strategy = 2
#         final_fallback = substrate_term
#         substrate_term = irr_ma_from_expression(expression, parameters)
#         # complete failure
#         if not substrate_term:
#             strategy = 3
#             substrate_term = final_fallback
#
#     return substrate_term, strategy
#
#
# def irr_ma_from_coeffs(substrates, stoichiometry):
#     """
#     Returns a mass action expression for an irreversible reaction (which
#     simply consists of substrates).
#
#     In this strategy the stoichiometric coefficients are used to
#     construct the substrate terms. Here an invalid substrate term  can be
#     produced when the rate equation does not follow  the stoichiometry
#     as defined in the model and the answer has to be validated using
#     `validate_irr_ma`.
#
#     Parameters
#     ----------
#     substrates : list of sympy symbols
#         List with symbolic representations for each substrate involved
#         in the reaction.
#     stoichiometry : dict of sympy.Symbol:float
#         Symbolic representations of the substrates and products are used
#         for the keys of this dict while the stoichiometric coefficient
#         values are floats.
#
#
#     Returns
#     -------
#     sympy expression
#         A symbolic expression of the substrate term of a mass action
#         expression for an irreversible reaction constructed using
#         stoichiometric coefficients.
#
#
#     """
#     return build_metabolite_term(substrates, stoichiometry)
#
#
# def irr_ma_from_expression(expression, parameters, failure_threshold=10):
#     """
#     Returns a mass action expression for an irreversible reaction (which
#     simply consists of substrates).
#
#     In this strategy there is no inspection of the stoichiometry as
#     provided by the model map. Here the expressions is divided or
#     multiplied by each parameter that initially appears in the
#     expression until it does not appear in the expression. If the
#     parameter is not removed after a defined number of attempts a total
#     failure occurs and this function returns `None`. This is a fallback
#     for cases where defined stoichiometry does not correspond to the
#     actual rate equation.
#
#     Parameters
#     ----------
#     expression : sympy expression
#         A sympy expression representing a rate equation of an
#         irreversible reaction.
#     parameters : list of sympy symbols
#         List with symbolic representations for each parameter involved
#         in the reaction which `expression` represents.
#     failure_threshold : int, optional (Default: 10)
#         A threshold value the defines the number of times the parameter
#         removal strategy should be tried before failure.
#
#     Returns
#     -------
#     sympy expression or None
#         A symbolic expression of the substrate term of a mass action
#         expression for an irreversible reaction constructed the rate
#         equation and parameters. None is returned in case of failure
#     """
#     expression_num = fraction(expression.expand())[0]
#     reset_point = expression_num
#     fail = False
#     for parameter in parameters:
#         tries = 0
#         switch_strat = False
#         while parameter in expression_num.atoms(Symbol):
#             expression_num = (expression_num / parameter).factor()
#             tries += 1
#             if tries > failure_threshold:
#                 switch_strat = True
#                 break
#
#         if switch_strat:
#             expression_num = reset_point
#             tries = 0
#             while parameter in expression_num.atoms(Symbol):
#                 expression_num = (expression_num * parameter).factor()
#                 tries += 1
#                 if tries > failure_threshold:
#                     fail = True
#                     break
#
#         if fail:
#             break
#         reset_point = expression_num
#     if fail:
#         return None
#     else:
#         return expression_num
#
#
# def validate_irr_ma(expression, substrate_term):
#     """
#     Returns `True` when the substrates in the substrates term has the same
#     number of coefficients as in the rate equation numerator.
#
#     In theory an expanded rate equation expression numerator of an
#     irreversible reaction should consist of only parameters and
#     substrates. Therefore, division of this numerator by the substrate
#     term should yield an expression without any substrates.
#
#     Parameters
#     ----------
#     expression : sympy expression
#         A sympy expression representing a rate equation of an
#         irreversible reaction
#     substrate_term : sympy expression
#         A sympy expression representing the substrate (mass action) term
#         of an irreversible reaction
#
#     Returns
#     -------
#     boolean
#         `True` for valid substrate term, otherwise `False`.
#     """
#     expression_num = fraction(expression.expand())[0]
#     remainder = expression_num / substrate_term
#     subs_atoms = substrate_term.atoms(Symbol)
#     valid = True
#     for remainder_atom in remainder.atoms(Symbol):
#         if remainder_atom in subs_atoms:
#             valid = False
#     return valid
#
# def build_metabolite_term(met_list, stoichiometry):
#     """
#     Given a list of metabolites and a dict with stoichiometry, this
#     function returns a metabolite term for a mass action expression.
#
#     Parameters
#     ----------
#     met_list : list of sympy.Symbol
#         List of symbolic representations of metabolites
#         (either products or substrates) that appear in a reaction.
#     stoichiometry : dict of sympy.Symbol:float
#         Symbolic representations of the metabolites are used as the keys
#         of this dict while the stoichiometric coefficients are floats
#
#     Returns
#     -------
#     sympy expression
#         A symbolic expression of the metabolite term of a mass action
#         expression constructed using stoichiometric coefficients.
#
#     See Also
#     --------
#     st_pt_keq_from_coeffs
#     """
#     met_term = 1
#     for met in met_list:
#         met_term *= met ** stoichiometry[met]
#
#     met_term = met_term.subs({1.0: 1})
#     return met_term
#
# def st_pt_keq_from_coeffs(expression, substrates, products, stoichiometry):
#     """
#     Takes an expression representing "substrates/products *
#     Keq_expression" and returns substrates, products and keq_expression
#     separately.
#
#     In this strategy the stoichiometric coefficients are used to
#     construct the substrate, product and Keq terms. Here an invalid Keq
#     expression can be produced when the rate equation does not follow
#     the stoichiometry as defined in the model and the answer has to be
#     validated using `validate_keq_expression`.
#
#     Parameters
#     ----------
#     expression : sympy expression
#         The expression containing "substrates/products * Keq_expression"
#     substrates : list of sympy symbols
#         List with symbolic representations for each substrate involved
#         in the reaction which `expression` represents.
#     products : list of sympy symbols
#         List with symbolic representations for each product involved in
#         the reaction which `expression` represents.
#     stoichiometry : dict of sympy.Symbol:float
#         Symbolic representations of the substrates and products are used
#         for the keys of this dict while the stoichiometric coefficients
#         are floats.
#
#     Returns
#     -------
#     tuple of sympy_expressions with length of 3
#         This tuple contains sympy expressions for the substrates,
#         products and keq_expression in that order
#
#     See Also
#     --------
#     get_st_pt_keq
#     st_pt_keq_from_expression
#     build_metabolite_term
#
#     """
#     subs_term = build_metabolite_term(substrates, stoichiometry)
#     prod_term = build_metabolite_term(products, stoichiometry)
#     keq = ((expression / subs_term) * prod_term).factor().subs({1.0: 1})
#     return subs_term, prod_term, keq
#
# def validate_keq_expression(expression, substrates, products):
#     """
#     Returns `True` when an expression does not contain any products
#     or substrates.
#
#     A valid Keq expression is either a single parameter representing the
#     Keq or it consists of parameters (maybe some variables) which
#     represents the Keq. There are no substrates or products of the
#     reaction in the Keq expression.
#
#     Parameters
#     ----------
#     expression : sympy expression
#         A symbolic expression representing the Keq. May be valid or
#         invalid.
#     substrates : list of sympy.Symbol
#         List of symbols for substrates involved in the reaction for
#         which `expression` is the Keq expression.
#     products : list of sympy.Symbol
#         List of symbols for products involved in the reaction for
#         which `expression` is the Keq expression.
#
#     Returns
#     -------
#     bool
#         True for valid Keq expression, False if invalid.
#
#     See Also
#     --------
#     st_pt_keq_from_coeffs
#     """
#     valid = True
#     expression_symbols = expression.atoms(Symbol)
#     for metabolite in substrates + products:
#         if metabolite in expression_symbols:
#             valid = False
#     return valid
