import multiprocessing
import random
import re
import time
from datetime import timedelta
from multiprocessing import Pool
from uuid import uuid4

import dill

dill.settings['recurse'] = True
import humanize
import pandas as pd
from tools import remove_prefix, split_data, get_unique_count
import sympy
from sympy.generator import FormulaGenerator
from sympy import latex, Derivative
from sympy.settings import randomize_settings
from data_iterator import formula_iterator
from pathlib import Path
from tools import timeout, remove_suffix

max_fnc = max
DELIMITER = ';;'

def get_function_symbols(expr):
    function_symbols = set()
    if isinstance(expr, sympy.core.function.UndefinedFunction):
        function_symbols.add(expr)
    elif hasattr(expr, 'func') and isinstance(expr.func, sympy.core.function.UndefinedFunction):
        function_symbols.add(expr.func)
    for arg in expr.args:
        function_symbols.update(get_function_symbols(arg))
    return function_symbols

def check_formula(expr):
    try:
        if isinstance(expr, (sympy.core.relational.Relational, sympy.Implies)):
            lhs_args = expr.args[0].free_symbols
            rhs_args = expr.args[1].free_symbols

            lhs_funcs = get_function_symbols(expr.args[0])
            rhs_funcs = get_function_symbols(expr.args[1])

            return set(lhs_args) == set(rhs_args) and lhs_funcs == rhs_funcs
    except Exception:
        pass

    return False


def check_begin_end(string):
    end_index = string.find('end')
    before_index = string.find('before')

    if end_index == -1 ^ before_index == -1:
        return False
    elif end_index == -1 and before_index == -1:
        return True
    else:
        return before_index < end_index



def process_data(data, id, versions_per_formula, over_all_results, start_time, callback=None):
    formulas = set()
    formula_ctr = len(over_all_results)
    start_time_ = time.time()

    def add_formula(formula, uuid):
        formula_ = formula.replace('\n', '\\n')
        if formula_ not in over_all_results and formula_ not in formulas and DELIMITER not in formula_:
            formulas.add((formula_, uuid, id))
            if callback is not None:
                callback(formula_, uuid, id)
            return True
        return False

    iterator = data.get_formulas if hasattr(data, 'get_formulas') else [data]
    for formula in iterator:
        if time.time() - start_time_ > 30:
            break

        raw_formula = formula
        try:
            symbols = ['=', '\\Rightarrow', '\\implies']
            if not any(s in formula for s in symbols):
                continue

            if len(formula) < 6:
                continue

            if not check_begin_end(formula):
                continue

            for sign in ['$', '=', '\\geq', '\\leq', '<', '>', '\\le', '\\ge', r'\;', r'\approx', '%', '.', ',', ':',
                         'n:', '\n']:
                formula = remove_prefix(remove_suffix(formula, sign), sign).strip()

            if formula.startswith('{') and formula.endswith('}') and len(formula.count('}')) == 1 and len(formula.count('{')) == 1:
                formula = formula[1:-1]

            if formula.startswith('(') and formula.endswith(')') and '(' not in formula[1:-1]:
                formula = formula[1:-1]

            if len(formula) < 6:
                continue

            if formula.startswith('\\ '):
                continue

            if formula.startswith('\\text{') and 'undefined' not in formula.lower():
                continue  # still keep \\text{undefined}

            if any(s in formula for s in ['?', 'text{ft}', 'tag']):
                continue

            if 'end' in formula and 'begin' not in formula:
                continue

            if formula.isnumeric():
                continue
            else:
                s = formula.split('=')
                if len(s) == 2:
                    if s[0].isnumeric() and s[1].isnumeric() and float(s[0].strip()) - (s[1].strip()) > 1e-5:
                        continue

            no_starter = {'-}', 'du', r'\pm', }
            for ns in no_starter:
                if formula.startswith(ns):
                    break
            else:
                patterns = [r'^[sgfhH]\'*\([a-zA-Z0-9\}\{\(\)]+\)\s?=\s?', r'^\s?=\s?[sfghH]\'*\([a-zA-Z0-9]\)',
                            r"^[a-z]\s?=\s?[-+]\d+", r"^[-+]\d+\s?=\s?[a-z]+", "[A-Z]_[a-z]\s+="]
                match = any(re.match(pattern, formula) for pattern in patterns)
                if match:  # ignore things like f(x) = 4
                    continue

                max_ = versions_per_formula
                if any(symbol in formula for symbol in symbols):
                    formula_template = FormulaGenerator(formula)

                    useful = check_formula(formula_template.current_tex)

                    try:
                        if useful:
                            if sympy.core.function.UndefinedFunction in formula_template.current_tex:
                                continue
                            else:
                                if any(x in formula for x in ['frac{d}{dx}', "'", '%', '...']):
                                    pass
                                else:
                                    solve_result = timeout(0.25)(lambda: sympy.solve(formula_template.current_tex))()
                                    if solve_result:
                                        if isinstance(solve_result, list):
                                            if isinstance(solve_result[0], dict):
                                                if random.random() < 0.5 or len(solve_result[0]) > 1 or len(set.union(*[set(x.keys()) for x in solve_result])) > 1:
                                                    impl = " or ".join(
                                                        [", ".join(
                                                            ["%s = %s" % (latex(aa), latex(aaa, **randomize_settings)) for
                                                             aa, aaa in a.items()]) for a in solve_result])
                                                else:
                                                    var = latex(list(solve_result[0])[0])
                                                    impl = "%s \\in \{%s\}" % (var, ', '.join(latex(list(v.values())[0]) for v in solve_result))

                                                if len(impl) > 40:
                                                    continue  # this formula is too complicated

                                                if Derivative in formula_template.current_tex:
                                                    continue

                                                formula = "%s \\Rightarrow %s" % (formula, impl)
                                            else:
                                                if Derivative in formula_template.current_tex:
                                                    continue

                                                var = list(formula_template.current_tex.free_symbols)[0]
                                                impl = " or ".join(
                                                    [latex(var) + ' = ' + latex(a, **randomize_settings) for a in
                                                     solve_result])
                                                if len(impl) > 40:
                                                    continue  # this formula is too complicated
                                                formula = "%s \\Rightarrow %s" % (formula, impl)
                                            formula_template = FormulaGenerator(formula)
                                        else:
                                            if not any(isinstance(a, (sympy.Eq)) for a in
                                                       formula_template.current_tex.args):  # longer chains of equalities are assumed to be reasonable
                                                solve_result = timeout(1)(
                                                    lambda: sympy.simplify(formula_template.current_tex))()
                                                if solve_result != True:
                                                    continue
                                    elif isinstance(solve_result, Exception):
                                        continue
                                    else:
                                        if not any(isinstance(a, (sympy.Eq)) for a in
                                                   formula_template.current_tex.args):
                                            solve_result = timeout(1)(
                                                lambda: sympy.simplify(formula_template.current_tex))()
                                            if solve_result != True:
                                                continue
                                        else:
                                            # this is a longer chain of equalities
                                            equalities = formula_template.current_tex.find(sympy.Eq)
                                            equalities = [eq for eq in formula_template.current_tex.find(sympy.Eq) if len(eq.find(sympy.Eq)) == 1]

                                            if len(equalities) > 0:
                                                # just check a single equation and hope this is representative for all
                                                equality = random.choice(equalities)
                                                solve_result = timeout(0.25)(lambda: sympy.simplify(equality))()
                                                if solve_result != True:
                                                    continue
                                            else:
                                                continue

                        elif random.random() > 0.5 \
                                and isinstance(formula_template.current_tex, sympy.Eq) \
                                and len(formula_template.current_tex.free_symbols) == 1 \
                                and not "text" in formula \
                                and not sympy.core.function.UndefinedFunction in formula_template.current_tex \
                                and any(s in formula_template.current_tex for s in [sympy.Add, sympy.Mul]):
                            max_ = int(max_ / 2)
                            # try to solve this equation
                            solve_result = timeout(0.5)(lambda: sympy.solve(formula_template.current_tex))()
                            if solve_result:
                                if isinstance(solve_result, list):
                                    var = list(formula_template.current_tex.free_symbols)[0]
                                    args = formula_template.current_tex.args

                                    if len(solve_result) == 1 and len(args) == 2 and (
                                            len(args[0].free_symbols) == 1 and len(args[1].free_symbols) == 0) and \
                                            list(args[0].free_symbols)[0] == args[0]:
                                        if args[1] == solve_result[0]:
                                            continue  # trivial equation

                                        l = latex(solve_result[0])
                                        formula = latex(args[1])
                                        if formula.strip() == l.strip():
                                            continue

                                        # equation of type x = 2+3 -> compute result and add it -> x = 2+3 = 5
                                        if '.' in l and len(l.split('.')[1]) > 2:
                                            rounded = l.split('.')[0] + '.' + l.split('.')[1][:2]
                                            formula += " \\approx " + rounded
                                            max_ = 2
                                        else:
                                            formula += " = " + l
                                    else:
                                        impl = " or ".join(
                                            [latex(var) + ' = ' + latex(a, **randomize_settings) for a in
                                             solve_result])
                                        if len(impl) > 30:
                                            continue  # this formula is too complicated

                                        if Derivative in formula_template.current_tex:
                                            continue

                                        formula = "%s \\Rightarrow %s" % (formula, impl)
                                    formula_template = FormulaGenerator(formula)
                                else:
                                    continue
                            elif isinstance(solve_result, list) and len(solve_result) == 0:
                                # this means the equation is valid in general or has no solutions at all
                                continue
                            else:
                                continue
                        else:
                            continue


                    except Exception as e:
                        continue

                    print("%d: %s" % (max_, formula))
                    if len(formula) > 75:
                        max_ = min(max_, 5)
                        print("pretty long formula: <%s>" % formula)
                    elif len(formula) > 100:
                        print("Skip too long formula <%s>" % formula)
                        continue
                    max_ = min(max_, versions_per_formula)

                    uuid = str(uuid4())
                    if add_formula(formula, uuid):
                        formula_ctr += 1
                    else:
                        max_ = min(max_, 4)
                    for version in formula_template.generate_versions_iterator(max=max_, only_true_version=True,
                                                                               initial_is_candidate=False, max_none=10):
                        add_formula(version[0], uuid)

                    if formula_ctr % 100 == 0:
                        diff = time.time() - start_time
                        print("Generated %d formulas from %d base formulas in %s (%fs)" % (
                        len(over_all_results) + len(formulas), formula_ctr, humanize.naturaldelta(timedelta(seconds=diff)), diff))

        except Exception as e:
            pass # exceptions might occur due to a lot of reasons, most likely due to a NotSupportedSymbolException

    return formulas


def process_data__(data_batch, versions_per_formula, result, start_time):
    formulas = set()
    for data, id in data_batch:
        formulas.update(process_data(data, id, versions_per_formula, result, start_time))
    return formulas


def generate_math_formulas(max=100000000, start=0, file=None, file_tens=None, iterations=None, pool=False, versions_per_formula=100, version="", return_data=False, amps=False, arqmath=False, append=None, batch_size=200, num_cpu=multiprocessing.cpu_count(), create_split=False):
    if append is None:
        append = start > 0
    result = set()
    start_time = time.time()
    file_ = file
    output = 'data/math-formulas'
    iteration_file = output + '/progress%s.txt' % version
    Path(output).mkdir(parents=True, exist_ok=True)
    file = 'data/math-formulas%s.csv' % version
    if append:
        try:
            result = set(pd.read_csv(file, delimiter=DELIMITER)['text'])
            print("Loaded %d results from previous file" % len(result))
        except Exception as e:
            print("could not load previous data! %s" % e)
            with open(file, 'w+', encoding='utf8') as f:
                f.write('uuid' + DELIMITER + 'id' + DELIMITER + 'text\n')
            pass

        try:
            with open(iteration_file, 'r+', encoding='utf8') as f:
                start = int(remove_suffix(f.readline().strip(), '\n').strip()) + 500
                print("Set start to %d" % start)
        except Exception as e:
            print("Could not read progress file %s: %s" % (iteration_file, e))

    mode = 'a' if append else 'w+'
    if not append:
        with open(file, mode, encoding='utf8') as f:
            f.write('uuid' + DELIMITER + 'id' + DELIMITER + 'text\n')

    def add_formula(formula, uuid, id, f):
        formula_ = formula.replace('\n', '\\n')
        if formula_ not in result and DELIMITER not in formula_:
            result.add(formula_)
            f.write(uuid + DELIMITER + str(id) + DELIMITER + formula_ + '\n')
            return True
        return False

    mode = 'a'
    cache = set()

    if pool:
        print("Number of processors: %d" % num_cpu)

    last_cache = time.time()
    for i, (data, index) in enumerate(formula_iterator(start=start, amps=amps, arqmath=arqmath, file=file_, file_tens=file_tens, return_index=True)):
        if iterations is not None and i >= iterations:
            print("Reached end %d" % iterations)
            break

        if i % 100 == 0 and i > 0:
            time_diff = time.time() - last_cache
            last_cache = time.time()
            print("Write Cache with %d entries (%d formulas per s)" % (len(cache), len(cache) / time_diff))
            with open(file, mode, encoding='utf8') as f:
                for formula, uuid, id in cache:
                    add_formula(formula, uuid, id, f)
                cache.clear()

            with open(iteration_file, 'w+', encoding='utf8') as f:
                f.write(str(index))

            print('Iteration %d: Generated %d formulas in %fs' % (i, len(result), (time.time() - start_time)))

        if i >= max:
            break
        try:
            id = data['post_id']
            r = timeout(40)(lambda: process_data(str(data['formula']), id, versions_per_formula, result, start_time, callback=lambda f, u, d: cache.add((f, u, d))))()
        except (ValueError, TypeError, Exception) as e:
            r = e

        if isinstance(r, Exception):
            print("Exception <%s> for formula <%s>" % (r, data['formula']))

    print("Generated %d formulas in %fs" % (len(result), (time.time() - start_time)))

    if create_split:
        d = split_data(file, delimiter=DELIMITER)
        print("Base formulas: %d" % get_unique_count(d, 'id'))
        if return_data:
            return d



if __name__ == '__main__':
    generate_math_formulas(start=0, version='', append=True, amps=True, arqmath=True)