from SymcaToolBox import SymcaToolBox

class LatexOut(object):
    def __init__(self, symca):
        self.symca = symca
        self.path = self.symca.path_to('latex_out')
        


        self.header = r"""
\documentclass[a4paper,10pt]{article}
\usepackage[utf8]{inputenc}

%opening
\title{}
\author{}

\begin{document}

\maketitle
        """

    def make_main(self):
        main_file = self.path + 'main.tex'
        with open(main_file,'w') as f:
            f.write(self.header)
            
    def make_cp_table(self,cc):
        lines = ['\\begin{center}',
                 '\\begin{tabularx}{}[]{llrr}',
                 'Control pattern & Expression & Value & Percentage of total\\\\']
        for cp in cc.control_patterns:
            latexnum = SymcaToolBox.expression_to_latex(cp.numerator)
            elements = (cp.name, latexnum, cp.value, cp.percentage)
            line = '%s & $%s$ & %.2f & %.2f \\%% \\\\' % elements
            lines.append(line)

        lines.append('\\end{tabularx}')
        lines.append('\\end{center}')

        for line in lines:
            print line




    