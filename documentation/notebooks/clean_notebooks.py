#!/usr/bin/env  python
import nbformat
from sys import argv
from os import path


def notebook_without_cells(notebooknode):
    """
    Converts a NotebookNode object to a dict and removes the 'cells'
    key/attribute.
    """
    nb_sans_cells = {k: v for k, v in notebooknode.items()
                     if k != 'cells'}
    return nb_sans_cells


def remove_ex_comment(line):
    """
    If a line ends with '#ex' and is only a comment, returns an empty
    string, otherwise return the string.
    """
    if line.startswith('#') and '#ex' in line:
        return ''
    else:
        return line


def remove_line_with(line, pattern):
    """
    Returns an empty string if the provided string contains the provided
    pattern.
    """
    if pattern in line:
        return ''
    else:
        return line


def remove_ex(line):
    """
    Replaces '#ex in any string with an empty string.'
    """
    return line.replace('#ex', '')


def remove_cell_with(cell, pattern):
    """
    If a string string contains the specified pattern, None is returned.
    """
    if pattern in cell:
        return None
    else:
        return cell

def remove_stderr_from_cell(cell):
    """
    Removes any stderr from cell outputs list.
    """
    if 'outputs' in cell:
        outputs = cell['outputs']
        good_outputs = [d for d in outputs if not \
                        ('name' in d and d['name']=='stderr')]
        cell['outputs'] = good_outputs
    return cell

def iterlines(text):
    """
    Splits lines in string at '\n' while preserving line endings.
    """
    lines = text.split('\n')
    if text[-1] == '\n':
        lines = [line + '\n' for line in lines[:-1]]
        return lines
    else:
        lines = [line + '\n' for line in lines[:-1]] + [lines[-1]]
        return lines


def combine_lines(lines):
    """
    Combines the stings contained in a list into a single string.
    """
    new = ''
    for each in lines:
        new = new + each
    return new


if __name__ == "__main__":
    file_path = argv[1]

    original_nb = nbformat.read(file_path, nbformat.NO_CONVERT)

    nb_sans_cells = notebook_without_cells(original_nb)
    nb_sans_cells['cells'] = []

    for cell in original_nb.cells:
        # only include cells that do not contain the following pattern
        if remove_cell_with(cell['source'], '# To avoid duplication'):
            # a list for all the cells that should be preserved
            new_lines = []
            # go through the cell source and remove all unneeded lines and text
            for line in iterlines(cell['source']):
                new_line = remove_ex_comment(line)
                new_line = remove_ex(new_line)
                new_line = remove_line_with(new_line, '#remove_next')
                new_lines.append(new_line)
            # combine preserved lines into single string
            new_source = combine_lines(new_lines)
            # construct a new cell
            new_cell = {k: v for k, v in cell.items() if k != 'source'}
            # add the cell source
            new_cell['source'] = new_source
            # convert cell to NotebookNode
            new_cell = nbformat.NotebookNode(new_cell)
            # remove any stderr from cell
            new_cell = remove_stderr_from_cell(new_cell)
            # add cell to the new notebook
            nb_sans_cells['cells'].append(new_cell)
    new_nb = nbformat.NotebookNode(nb_sans_cells)
    new_path = path.splitext(file_path)
    new_path = new_path[0] + '_clean' + new_path[1]
    nbformat.write(new_nb, new_path)
