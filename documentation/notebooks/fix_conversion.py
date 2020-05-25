# This script should really be documented

import codecs
from os import listdir, path
import pypandoc
import sys
from re import sub
import re


# In[ ]:

def get_rst_file_names():
    def ends_with_rst(line):
        if line.endswith('.rst'):
            return True
        else:
            return False
    return list(filter(ends_with_rst, listdir(path.curdir)))


# In[ ]:

def get_lines(file_name):
    with codecs.open(file_name, 'r', 'utf-8') as f:
        lines = f.readlines()
    return lines


# In[ ]:

def save_lines(lines, file_name):
    with codecs.open(file_name, "w", "utf-8") as f:
        f.writelines(lines)


# In[ ]:

def fix_note_indentation(lines):
    for i, line in enumerate(lines):
        if line.startswith('.. note::'):
            counter = i
            while True:
                counter += 1
                try:
                    if lines[counter] == '\n':
                        break
                    else:
                        lines[counter] = '          ' + lines[counter]
                except:
                    break


# In[ ]:

def remove_endswith(lines, exclude_string='#ex\n'):
    new_lines = []
    for line in lines:
        if not line.endswith(exclude_string):
            new_lines.append(line)
    return new_lines


# In[ ]:

def remove_startsswith(lines, exclude_string):
    new_lines = []
    for line in lines:
        if not line.startswith(exclude_string):
            new_lines.append(line)
    return new_lines


# In[ ]:

def remove_empty_block(lines, block_string):
    new_lines = []
    for i, line in enumerate(lines):
        #if line.startswith(block_string) and lines[i + 2] == '    \n':
            #pass
        if line.startswith(block_string) and lines[i + 2] == '\n':
            pass
        else:
            new_lines.append(line)
    return new_lines

def remove_block_contains(lines, block_string, match_string):
    new_lines = []
    flag = False
    for i, line in enumerate(lines):
        if line.startswith(block_string) and \
                lines[i + 2].startswith(match_string):
            flag = True
        elif line == '\n' and i < len(lines)-2 and \
                lines[i + 1] != '\n' and lines[i + 1][:2] != '  ':
            flag = False
        if flag:
            pass
        else:
            new_lines.append(line)
    return new_lines

# In[ ]:

def replace_in_string(line, to_replace, replacement):
    new_string = line
    while True:
        try:
            new_string = line[:line.index(
                to_replace)] + replacement + line[line.index(to_replace) + len(to_replace):]
            line = new_string
        except:
            break
    return new_string


# In[ ]:

def replace_in_all(lines, to_replace, replacement):
    new_lines = []
    for line in lines:
        new_lines.append(replace_in_string(line, to_replace, replacement))
    return new_lines


# In[ ]:

def remove_specified_images(lines):
    new_lines = []
    remove_next = False
    for line in lines:
        if line.endswith('#remove_next\n'):
            remove_next = True
        elif remove_next and line.startswith('.. image'):
            remove_next = False
        else:
            new_lines.append(line)
    return new_lines


# In[103]:

def clear_extra_slashes(line):
    return line.replace('\\\\', '@@@@').replace('\\', '').replace('@@@@', '\\')


# In[ ]:

def table_math(new_line):
    slash_matches = re.findall(r':math:\\`(.*?)`', new_line)
    for s_m in slash_matches:
        s, d = count_slashes(s_m)
        s_m_clean = clear_extra_slashes(s_m)
        new_line = new_line.replace(':math:\\`%s`' % s_m,
                                    ':math:`%s` %s%s' % (s_m_clean, s * ' ', d * ' '))
    return new_line


# In[ ]:

def convert_html_tables(lines):
    new_lines = []
    replace_next = False
    for line in lines:
        if line.startswith('.. raw:: html'):
            replace_next = True
        elif replace_next and line != '\n':
            table = line.strip()
            new_line = pypandoc.convert(table, to='rst', format='html')
            new_line = table_math(new_line)
            new_lines.append(new_line)
            replace_next = False
        else:
            new_lines.append(line)
    new_lines = [line + '\n' for line in ''.join(new_lines).splitlines()]
    return new_lines


# In[100]:

def count_slashes(a_string):
    doubles = a_string.count('\\\\')
    singles = a_string.count('\\') - 2 * doubles
    return singles, doubles


# In[1]:

def add_in_out(lines):
    counter = 0
    new_lines = []
    for line in lines:
        if line.startswith('.. code::'):
            counter += 1
            line = '``In [%s]:``\n\n%s' % (counter, line)
        if line.startswith('.. parsed-literal::'):
            line = '``Out[%s]:``\n\n%s' % (counter, line)
        new_lines.append(line)
    return new_lines


# In[96]:

def sub_math(lines):
    new_lines = []
    for line in lines:
        matches = re.findall(r'\$(.*?)\$', line)
        for match in matches:
            line = line.replace('$%s$' % match,
                                ':math:`%s`' % (match))
        new_lines.append(line)
    return new_lines


def find_tables(lines):
    """
    For a list of lines, splits lines into blocks (stored in lists
    of lines within two lists) representing tables or non tables. Also
    return if a file starts with a table or a non-table (mostly
    non-tables, but functionality is included for robustness).
    """
    in_table = False
    tables = []
    non_tables = []
    current_table = []
    current_non_table = []
    text_first = None
    for i, line in enumerate(lines):
        if line.startswith('+') and line.strip().endswith('+') and not in_table:
            in_table = True
            if len(current_non_table) != 0:
                non_tables.append(current_non_table)
                current_non_table = []
            current_table.append(line)
            if text_first is None:
                text_first = False
        elif in_table and (line.startswith('+') or line.startswith('|')):
            current_table.append(line)
        elif in_table:
            in_table = False
            tables.append(current_table)
            current_table = []
            current_non_table.append(line)
        else:
            if text_first is None:
                text_first = True
            current_non_table.append(line)
    if len(current_non_table) != 0:
        non_tables.append(current_non_table)
    if len(current_table) != 0:
        tables.append(current_table)
    return tables, non_tables, text_first


def weave_lists(tables, non_tables, text_first):
    """
    Takes a list of tables, non-tables and a boolean indicating which
    should come first and returns a single list of lines.
    """
    new_list = []
    total_blocks = len(tables) + len(non_tables)
    for i in range(total_blocks):
        if text_first:
            new_list.extend(non_tables.pop(0))
            text_first = False
        else:
            new_list.extend(tables.pop(0))
            text_first = True
    return new_list


def fix_all_table_split(lines):
    """
    Uses find_tables, fix_table_splits and weave_lists to construct
    a new list of all lines with tables with the correct formatting.
    """
    tables, non_tables, text_first = find_tables(lines)
    new_tables = []
    for table in tables:
        new_tables.append(fix_table_splits(table))
    return weave_lists(new_tables, non_tables, text_first)


def fix_table_splits(table_lines):
    """
    Adds an escape "\" to lines where text has been split incorrectly
    (prematurely).
    """
    new_table = []
    for line in table_lines:
        if line.startswith('+'):
            new_line = ''
            line_type = line[1]
            for i, char in enumerate(line):
                if char == '+' and line[i + 1] == line_type:
                    char = '+' + line_type
                new_line = new_line + char
            new_table.append(new_line)
        else:
            new_line = ''
            for i, char in enumerate(line):
                if char == ' ' and line[i + 1] == '|':
                    if line[i - 1] != ' ':
                        char = '\ '
                    else:
                        char = '  '
                new_line = new_line + char
            new_table.append(new_line)
    return new_table


if __name__ == "__main__":
    to_remove_block_strings = ['.. code::', '.. parsed-literal::']
    ends_with_to_remove = ['#ex\n']
    starts_with_to_remove = ['    %matplotlib inline']
    replacements = [('*#', '`'),
                    ('#*', '`_'),
                    ('.ipynb#', '.html#'),
                    ('code:: ipython3', 'code:: python')]

    if len(sys.argv) == 1:
        file_names = get_rst_file_names()
    else:
        file_names = sys.argv[1:]
    for file_name in file_names:
        print("Applying fixes for: ", file_name)
        lines = get_lines(file_name)
        fix_note_indentation(lines)

        for to_remove in ends_with_to_remove:
            lines = remove_endswith(lines, to_remove)

        for to_remove in starts_with_to_remove:
            lines = remove_startsswith(lines, to_remove)

        for to_replace, replacement in replacements:
            lines = replace_in_all(lines, to_replace, replacement)

        lines = remove_specified_images(lines)
        lines = sub_math(lines)
        lines = fix_all_table_split(lines)
        lines = convert_html_tables(lines)

        for block_to_remove in to_remove_block_strings:
            lines = remove_empty_block(lines, block_to_remove)
        
        lines = remove_block_contains(lines, '.. parsed-literal::', 
                                      '    Widget Javascript not detected.')

        lines = add_in_out(lines)

        save_lines(lines, file_name)
