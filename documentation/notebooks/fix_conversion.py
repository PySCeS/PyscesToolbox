
# coding: utf-8

# In[22]:

import codecs
from os import listdir, path
import pypandoc
import sys


# In[12]:

def get_rst_file_names():
    def ends_with_rst(line):
        if line.endswith('.rst'):
            return True
        else:
            return False
    return filter(ends_with_rst,listdir(path.curdir))



# In[13]:

def get_lines(file_name):
    with codecs.open(file_name,'r', 'utf-8') as f:
        lines = f.readlines()
    return lines



# In[14]:

def save_lines(lines,file_name):
    with codecs.open(file_name,"w", "utf-8") as f:
        f.writelines(lines)


# In[15]:

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


# In[16]:

def remove_endswith(lines, exclude_string = '#ex\n'):
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

def remove_empty_block(lines,block_string):
    new_lines = []
    for i, line in enumerate(lines):
        if line.startswith(block_string) and lines[i+2] == '\n':
            pass
        else:
            new_lines.append(line)
    return new_lines


# In[56]:

def replace_in_string(line,to_replace,replacement):
    new_string = line
    while True:
        try:
            new_string = line[:line.index(to_replace)] + replacement +             line[line.index(to_replace) +  len(to_replace):]
            line = new_string
        except:
            break
    return new_string


# In[68]:

def replace_in_all(lines, to_replace, replacement):
    new_lines = []
    for line in lines:
        new_lines.append(replace_in_string(line,to_replace,replacement))
    return new_lines


# In[1]:

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



# In[82]:

def convert_html_tables(lines):
    new_lines = []
    replace_next = False
    for line in lines:
        if line.startswith('.. raw:: html'):
            replace_next = True
        elif replace_next and line != '\n':
            table = line.strip()
            new_line = pypandoc.convert(table,to='rst',format='html')
            new_lines.append(new_line)
            replace_next = False
        else:
            new_lines.append(line)
    new_lines = [line + '\n' for line in ''.join(new_lines).splitlines()]
    return new_lines



# In[83]:

if __name__ == "__main__":
    to_remove_block_strings = ['.. code::','.. parsed-literal::']
    ends_with_to_remove = ['#ex\n']
    starts_with_to_remove = ['    %matplotlib inline']
    replacements = [('*#','`'),
                   ('#*','`_')]

    if len(sys.argv) == 1:
        file_names = get_rst_file_names()
    else:
        file_names = sys.argv[1:]
    for file_name in file_names:
        print "Applying fixes for: ", file_name
        lines = get_lines(file_name)
        fix_note_indentation(lines)

        for to_remove in ends_with_to_remove:
            lines = remove_endswith(lines,to_remove)

        for to_remove in starts_with_to_remove:
            lines = remove_startsswith(lines,to_remove)

        for to_replace, replacement in replacements:
            lines = replace_in_all(lines, to_replace, replacement)

        lines = remove_specified_images(lines)
        lines = convert_html_tables(lines)

        for block_to_remove in to_remove_block_strings:
            lines = remove_empty_block(lines, block_to_remove)


        save_lines(lines, file_name)



# In[ ]:



