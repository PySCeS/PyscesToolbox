from re import sub
from os import path, mkdir

class PyscesToolBox(object):

    @staticmethod
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

    @staticmethod
    def expression_to_latex(expression):
        #At the moment this function can turn (some) expressions containing
        #elasticities and control coefficients into 
        #latex strings. One problem is that I assumed that expressions with 
        #fractions will always have the form 
        #(x1/y1+x2/y2+x3/y3)/(z1/u1+z2/u2+z3/u3). However when the numerator
        #only has one term the form is: x1/(y1*(z1/u1+z2/u2+z3/u3))
        #and in this case the function does not work correctly. 
        if type(expression) != str:
            expression = str(expression)

        #elasticities
        expr = sub(r'ec(\S*?)_(\S*?\b)',r'\\varepsilon^{\1}_{\2}',expression)
        #fluxes
        expr = sub(r'J_(\S*?\b)',r'J_{\1}',expr)
        #controls
        expr = sub(r'cc(\S*?)_(\S*?\b)',r'C^{\1}_{\2}',expr)
        #main fraction division        
        expr = sub(r'\)/\(',r'   ',expr)      
        #remove ( and )
        expr = sub(r'\)',r'',expr)
        expr = sub(r'\(',r'',expr)
        #main fraction
        expr = sub(r'(\S*[^\)])/([^\(]\S*)',r'\\frac{\1}{\2}',expr)
        #sub fractions
        expr = sub(r'(.*})\s\s\s(\\frac{.*)',r'\\frac{\1}{\2}',expr)
        #times
        expr = sub(r'\*',r'\\cdot ',expr)


        return expr