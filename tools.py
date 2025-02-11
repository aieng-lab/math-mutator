import random
from collections import Counter
from copy import deepcopy

import pandas as pd
from bs4 import BeautifulSoup
import re
from threading import Thread
from TexSoup import TexSoup
import functools

from datasets import DatasetDict, Dataset

import sympy
from sympy import latex, SympifyError
from sympy.parsing.latex._parse_latex_antlr import parse_latex
from sympy.parsing.latex.logic import StringFormula
from sympy.parsing.latex.text import LaTeXText


def timeout(timeout):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout))]
            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e
            t = Thread(target=newFunc)
            t.daemon = True
            try:
                t.start()
                t.join(timeout)
            except Exception as je:
                print ('error starting thread')
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                return ret
            return ret
        return wrapper
    return deco

def make_dict_serializable(data):
    if isinstance(data, dict):
        # Create a new dictionary to store the serializable values
        serializable_dict = {}

        for key, value in data.items():
            # Convert non-serializable values to strings
            if not isinstance(value, (str, int, float, bool, list, dict)):
                try:
                    value = str(value)
                except Exception as e:
                    value = "EXCEPTION: %s" % e

            # Recursively process nested dictionaries or lists
            elif isinstance(value, dict):
                value = make_dict_serializable(value)
            elif isinstance(value, list):
                value = make_list_serializable(value)

            if isinstance(key, (bool, int, float)):
                try:
                    key = str(key)
                except Exception as e:
                    key = "EXCEPTION: %s" % e
            serializable_dict[key] = value

        return serializable_dict

    return data


def make_list_serializable(data):
    # Create a new list to store the serializable values
    serializable_list = []

    for item in data:
        # Convert non-serializable values to strings
        if not isinstance(item, (str, int, float, bool, list, dict)):
            try:
                item = str(item)
            except Exception as e:
                item = "EXCEPTION: %s" % e

        # Recursively process nested dictionaries or lists
        elif isinstance(item, dict):
            item = make_dict_serializable(item)
        elif isinstance(item, list):
            item = make_list_serializable(item)

        serializable_list.append(item)

    return serializable_list

def get_unique_count(dataset_dict, column_name):
    unique_uuids = set()
    for dataset_name, dataset in dataset_dict.items():
        if column_name in dataset.column_names:
            unique_uuids.update(set(dataset[column_name]))
    return len(unique_uuids)



def split_data(txt_file, proportions=(0.8, 0.2), delimiter=','):
    dataset = pd.read_csv(txt_file, delimiter=delimiter)
    columns = ['id', 'text']
    train = {c: [] for c in columns}
    test = {c: [] for c in columns}
    first_column = columns[0]
    for uuid, group in dataset.groupby('id'):
        l_train = len(train[first_column])
        l_test = len(test[first_column])
        proportion = l_train / (l_test + l_train) if l_test > 0 else 1
        if proportion < proportions[0]:
            # train
            for text in group['text'].str.replace('\\n', '\n'):
                train['text'].append(text)
                train['id'].append(uuid)
        else:
            for text in group['text'].str.replace('\\n', '\n'):
                test['text'].append(text)
                test['id'].append(uuid)


    splitted = DatasetDict()
    splitted['train'] = Dataset.from_dict(train).shuffle()
    splitted['test'] = Dataset.from_dict(test).shuffle()

    sp = txt_file.split('/')
    directory = '/'.join(sp[:-1])
    name = remove_suffix(remove_suffix(sp[-1], '.txt'), '.csv')

    path = directory + '/' + name
    print(splitted)
    splitted.save_to_disk(path)
    return splitted


def get_duplicates(lst):
    counter = Counter(lst)
    duplicates = [item for item, count in counter.items() if count > 1]
    return duplicates

class Text:

    def __init__(self, data: str, remove_html=False, raw=False, precalculate=False):
        self.raw = data
        self.formulas = None
        self.id = None
        self.formulas_string = None
        self.raw_formulas = []
        self.functions_ = None

        self.remove_html = remove_html
        self.raw_ = raw
        self.text = None
        self.initialized = False

        self.precalculate = precalculate
        if precalculate:
            self.check_init()


    def check_init(self):
        if not self.initialized:
            self.init()
            self.initialized = True


    def init(self):
        if self.remove_html:
            # convert html text to readable text
            soup = BeautifulSoup(self.raw, 'html.parser')
            span_taqs = soup.find_all('span', {'class': 'math-container'})
            for span_tag in span_taqs:
                if span_tag.string and not (span_tag.string.startswith('$') and span_tag.string.endswith('$')):
                    span_tag.string = "$%s$" % span_tag.string

            self.text = soup.get_text()
        else:
            self.text = self.raw

        if not self.raw_:
            # commands that are ignored, but whose (1st) argument is kept
            ignored_command = {'mbox', 'Big', 'llap', 'vec', 'overrightarrow', 'small', 'underset', 'displaystyle', 'Bbb',}
            # unary commands that are deleted with it's content
            ignored_content = {'color', 'gray', 'leadingColor', 'large'}
            # commands without arguments that are deleted with it's content
            replaced_content = {'thinspace', 'enspace', 'scriptsize', 'rm', 'bf',
                               'space', 'Big', 'small', 'Space'}
            try:
                pattern = r'\$(?!\$)'
                text = re.sub(pattern, ' $', self.text)
                tex = TexSoup(text)

                for command in ignored_command:
                    for r in tex.find_all(command):
                        if len(r.args) > 0:
                            a = r.args[0].all
                            if len(a) == 1:
                                r.replace_with(a[0])

                for command in ignored_content.union(replaced_content):
                    # data = re.sub(r'\\%s{[^}]+}' % c, '', data)
                    for r in tex.find_all(command):
                        r.delete()

                self.text = str(tex)
            except Exception as e:
                pass

            for c in ignored_command:
                pattern = r'\\%s{([^}]*)}' % c
                self.text = re.sub(pattern, r'\1', self.text)

            for r in replaced_content:
                self.text = self.text.replace("\\" + r, '')

            for command in ignored_content:
                self.text = re.sub(r'\\%s{[^}]+}' % command, '', self.text)

        if self.precalculate:
            self.get_formulas()
            self.get_formulas(as_string=True)
            r = timeout(2)(lambda :self.functions())()
            if isinstance(r, Exception):
                raise r

    @property
    def args(self):
        return tuple(self.get_formulas(remove_None=True))

    @property
    def free_symbols(self):
        symbols = []
        for formula in self.get_formulas(as_string=False):
            if formula is not None:
                symbols += list(formula.free_symbols)
        symbols = get_duplicates(symbols)
        symbols = set(s for s in symbols if str(s) not in self.functions(as_string=True))
        return symbols

    def functions(self, as_string=False):
        if self.functions_ is None:
            result = set()
            for f in self.get_raw_formulas():
                try:
                    functions = parse_latex(f).atoms(sympy.Function)
                    result.update(s.func for s in functions)
                except Exception:
                    pass
            self.functions_ = result

        if as_string:
            r = set()
            for f in self.functions_:
                try:
                    r.add(f.name)
                except Exception:
                    pass
            return r

        return self.functions_

    def has_formula_count(self, n):
        return self.formula_count() >= n

    def formula_count(self):
        return self.raw.count('math-container')

    def get_raw_formulas(self):
        self.check_init()
        pattern = r'\$(.*?)\$'
        formulas = re.findall(pattern, self.text)
        return set(formulas)

    def _convert_aligned_equation(self, latex_equation):
        env = None
        if 'aligned' in latex_equation:
            env = 'aligned'
        elif 'align*' in latex_equation:
            env = 'align*'
        elif 'align' in latex_equation:
            env = 'align'

        if env is not None:
            # Remove leading and trailing whitespaces
            latex_equation = latex_equation.strip()

            # Remove the '\begin{aligned}' and '\end{aligned}' tags
            latex_equation = re.sub(r'\\begin{%s}' % env, '', latex_equation)
            latex_equation = re.sub(r'\\end{%s}' % env, '', latex_equation)

            latex_equation = re.sub(r'&', '', latex_equation)

            # Replace '\\\\' with ' && '
            lines = []
            for line in latex_equation.split('\\\\'):
                if len(line.strip()) > 0:
                    if line.strip().startswith('=') and len(lines) > 0:
                        lines[-1] += line
                    else:
                        equ = line.split('=')
                        if len(equ) == 2:
                            lhs = equ[0].strip()
                            if len(lines) > 0 and lhs == lines[-1].split('=')[0].strip():
                                lines[-1] += ' = ' + equ[1]
                            else:
                                lines.append(line)
                        else:
                            lines.append(line)

            result = [] #[r"%s \Rightarrow %s" % (x, y) for x, y in zip(lines, lines[1:])] #+ [r"%s \Rightarrow %s \Rightarrow %s" % (x, y, z) for x, y, z in zip(lines, lines[1:], lines[2:])]
            for l in lines:
                if len(l.split('=')) > 2:
                    result.append(l)
                elif bool(random.getrandbits(1)):
                    result.append(l)

            return result
        return latex_equation

    def flatten_list(self, lst):
        return [item for sublist in lst for item in (self.flatten_list(sublist) if isinstance(sublist, list) else [sublist])]

    def get_formulas(self, as_string=True, remove_None=False):
        if as_string and self.formulas_string:
            if remove_None:
                return [f for f in self.formulas_string if f is not None]
            return self.formulas_string
        elif self.formulas:
            if remove_None:
                return [f for f in self.formulas if f is not None]
            return self.formulas

        formulas = self.get_raw_formulas()
        formulas = self.flatten_list([self._convert_aligned_equation(f) for f in formulas])
        self.formulas_string = [f for f in formulas if r'\text{vertex' not in f and len(f) > 0]

        if as_string:
            return self.formulas_string

        self.formulas = []
        for f in self.formulas_string:
            try:
                self.formulas.append(parse_latex(f))
            except Exception:
                self.formulas.append(None)

        if remove_None:
            return [f for f in self.formulas if f is not None]
        return self.formulas

    def __copy__(self):
        return deepcopy(self)

    def dollars(self, s: str):
        return "$%s$" % s

    def subs(self, substitution, evaluate=False, **kwargs):
        self.check_init()
        new_ = deepcopy(self)
        for formula in self.get_raw_formulas():
            try:
                with sympy.evaluate(evaluate):
                    tex = parse_latex(formula)
                    tex = tex.subs(substitution, **kwargs)
                    l = latex(tex)
                    if l.strip() != formula.strip():
                        new_.text = new_.text.replace(self.dollars(formula), self.dollars(l))
            except Exception:
                pass


        new_.formulas_string = None
        new_.formulas = None
        new_.functions_ = None
        return new_
    def __str__(self):
        self.check_init()
        return self.text

    def getText(self):
        self.check_init()
        return self.text

    def __contains__(self, item):
        if isinstance(item, (sympy.Basic, Text, LaTeXText, StringFormula)):
            return any(item in f for f in self.get_formulas(as_string=False, remove_None=True))
        elif isinstance(item, type):
            for arg in self.get_formulas(as_string=False, remove_None=True):
                if isinstance(arg, item):
                    return True
                if hasattr(arg, 'func') and isinstance(arg.func, item):
                    return True
        elif isinstance(item, str):
            return item in self.__str__()

        try:
            for a in self.args:
                if hasattr(a, '__contains__') and a is not self:
                    try:
                        if item in a:
                            return True
                    except TypeError:
                        pass
        except SympifyError:
            pass

        return False


def remove_prefix(text, *prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):]
    return text


def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:len(text) - len(suffix)]
    return text