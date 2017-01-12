
# coding: utf-8

# In[21]:

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
    return filter(ends_with_rst, listdir(path.curdir))


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
        if line.startswith(block_string) and lines[i + 2] == '    \n':
            pass
        elif line.startswith(block_string) and lines[i + 2] == '\n':
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


# In[ ]:

if __name__ == "__main__":
    to_remove_block_strings = ['.. code::', '.. parsed-literal::']
    ends_with_to_remove = ['#ex\n']
    starts_with_to_remove = ['    %matplotlib inline']
    replacements = [('*#', '`'),
                    ('#*', '`_'),
                    ('.ipynb#', '.html#')]

    if len(sys.argv) == 1:
        file_names = get_rst_file_names()
    else:
        file_names = sys.argv[1:]
    for file_name in file_names:
        print "Applying fixes for: ", file_name
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
        lines = convert_html_tables(lines)

        for block_to_remove in to_remove_block_strings:
            lines = remove_empty_block(lines, block_to_remove)

        lines = add_in_out(lines)

        save_lines(lines, file_name)
