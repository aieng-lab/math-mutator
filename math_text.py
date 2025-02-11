import json
import os
import time
from uuid import uuid4

import pandas as pd

import sympy
from data_iterator import data_iterator
from math_formulas import DELIMITER
from sympy.generator import FormulaGenerator
from sympy.parsing.latex.text import LaTeXText
from tools import split_data, timeout, remove_suffix, Text, get_unique_count

max_fnc = max

def generate_math_text(max=100000000, debug=False, start=0, end=1000000000000, iterations=None, versions_per_formula=100, version="", return_data=False, amps=False, arqmath=False, verbose=False, append=None, questions_start=None, questions_len=False, create_split=False, delimiter=DELIMITER):
    if append is None:
        append = start > 0
    result = set()
    result_no_formulas = {}
    formula_ctr = 0
    start_time = time.time()
    output = 'data/math-text'
    file = 'data/math-text%s.csv' % version
    iteration_file = output + '/progress%s.txt' % version
    file_result_no_formulas = output + '/data_temp_%s.txt' % version
    os.makedirs(output, exist_ok=True)

    if append:
        try:
            print("try to load old data")
            result = set(pd.read_csv(file, delimiter=delimiter)['text'])
            print("Loaded %d results from previous file" % len(result))
        except Exception:
            print("Could not read old file")
            with open(file, 'w+', encoding='utf8') as f:
                f.write('uuid' + delimiter + 'id' + delimiter + 'text\n')

        try:
            result_no_formulas = json.load(open(file_result_no_formulas, 'r+', encoding='utf8'))
        except Exception:
            pass

        try:
            with open(iteration_file, 'r+', encoding='utf8') as f:
                questions_start = int(remove_suffix(f.readline().strip(), '\n').strip()) + 1
                if questions_len is not False:
                    questions_len = max_fnc(0, questions_len - questions_start)
                print("Set start to %d, question_len to %d" % (questions_start, questions_len))
        except Exception as e:
            print("Could not read progress file %s: %s" % (iteration_file, e))

    mode = 'a' if append else 'w+'
    if not append:
        # clear old file
        with open(file, mode, encoding='utf8') as f:
            f.write('uuid' + delimiter + 'id' + delimiter + 'id2' + delimiter + 'text\n')

    def add_formula(formula, uuid, id, question_index, f):
        formula_ = formula.replace('\n', '\\n')
        if formula_ not in result and delimiter not in formula_ and r'\text{None}' not in formula_:
            result.add(formula_)
            f.write(uuid + delimiter + str(id) + delimiter + str(question_index) + delimiter + formula_ + '\n')
            return True
        return False

    def check_similarity(formula):
        # check if the first sentence (usually question) is the same without the formulas
        # this filters out questions that has been already processed with different numbers
        formula_ = " ".join(formula.split('\n')[0].split('$')[0::2])
        if formula_ in result_no_formulas:
            return False, result_no_formulas[formula_]
        else:
            uuid = str(uuid4())
            result_no_formulas[formula_] = uuid
            return True, uuid

    mode = 'a'
    cache = set()
    progress_offset = questions_start or 0
    for i, (data, id, question_index) in enumerate(data_iterator(start=start, end=end, questions_start=questions_start, questions_len=questions_len, latex_text=True, single_question=True, amps=amps, arqmath=arqmath, include_questions=False, return_id=True, verbose=verbose, return_question_index=True)):
        if iterations is not None and i >= iterations:
            print("Reached end %d" % iterations)
            break

        if i >= max:
            break

        if i % 10 == 0:
            duration_s = time.time() - start_time
            print('Iteration %d: Generated %d formulas in %ss' % (i, len(result) + len(cache), duration_s))

        if i % 10 == 0:
            print("Write Cache with %d entries  %s" % (len(cache), file))
            try:
                with open(file, mode, encoding='utf8') as f:
                    while len(cache) > 0:
                        formula, uuid, id, question_idx = cache.pop()
                        add_formula(formula, uuid, id, question_idx, f)

                with open(iteration_file, 'w+', encoding='utf8') as f:
                    f.write(str(progress_offset + question_index))
            except Exception as e:
                print("Could not write cache: %s" % e)

            json.dump(result_no_formulas, open(file_result_no_formulas, 'w+', encoding='utf8'))

        if isinstance(data, (LaTeXText, Text)):
            if not data.has_formula_count(5):
                continue

        max_time = 30000 if debug else 100

        try:
            text = data.getText()
            c1 = time.time()
            similar, uuid = check_similarity(data.getText())
            if text not in result and delimiter not in text:
                cache.add((text, uuid, id, question_index))
                def generate():
                    formula_template = FormulaGenerator(data)

                    if verbose:
                        print(data.getText())
                    max_ = 10 if similar else versions_per_formula

                    if hasattr(formula_template.current_tex, 'substitutable') and not formula_template.current_tex.substitutable:
                        max_ = 2

                    for version in formula_template.generate_versions_iterator(max=max_, max_none=25, only_true_version=True, initial_is_candidate=False):
                        cache.add((version[0], uuid, id, question_index))
                        d = (time.time() - c1)

                        if d > max_time:
                            return
                r = timeout(max_time)(generate)()
                if isinstance(r, Exception):
                    raise r

        except sympy.NotAllowedSymbolException:
            try:
                cache.add((data.raw, str(uuid4()), id, question_index))
            except Exception as e:
                pass
        except Exception as e:
            pass

            # add the unmodified text to the cache
            cache.add((data.raw, str(uuid4()), id, question_index))


    with open(file, mode, encoding='utf8') as f:
        for formula, uuid, id, question_index in cache:
            add_formula(formula, uuid, id, question_index, f)
        cache.clear()
    print("Generated %d formulas from %d base formulas in %fs" % (len(result), formula_ctr, (time.time() - start_time)))

    if create_split:
        d = split_data(file, delimiter=delimiter)

        print("Base formulas: %d" % get_unique_count(d, 'id'))

        if return_data:
            return d



if __name__ == '__main__':
    generate_math_text(start=0, end=20000, append=True, amps=False, arqmath=True)
