import json
import os
import re
import time
from datetime import timedelta

import humanize

from tools import remove_suffix, remove_prefix

excluded = [
    'integration-by-u-substitution',
    'totient',
    '138',
    '229', # broken files?
    '241', # files contain currency $ in latex formulas without escaping the latex formulas
    'absolute_value_of_complex_numbers',
    'adding_and_subtracting_decimals_word_problems',
    'adding_and_subtracting_rational_expressions_3',
    'adding_and_subtracting_rational_expressions_5',
    'adding_decimals_2',
    'adding_fractions',
    'adding-and-subtracting-in-scientific-notation',
    'adding-decimals-without-the-standard-algorithm-2',
    'adding-decimals-without-the-standard-algorithm-3',
    'adding-decimals-without-the-standard-algorithm-4',
    'adding-decimals-without-the-standard-algorithm-5',
    'addition_1',
    'addition_2',
    'addition_4',
    'addition-and-subtraction-word-problems-within',
    'add-within-100--level-2',
    'calculating-binomial-probability',
    'combined-vector-operations',
    'comparing-growth-rates-of-exponentials-and-polynomials',
    'construct-exponential-models-according-to-rate-of-change',
    'converting_decimals_to_fractions_1',
    'creating-power-series-from-geometric-series-using-algebra',
    'differentiate-rational-functions',
    'divide-whole-numbers-by-fractions',
    'dividing_decimals',
    'dividing_decimals_0.5',
    'dividing_decimals_3',
    'dividing_fractions',
    'dividing-by-2',
    'dividing-by-3',
    'dividing-by-4',
    'dividing-by-5',
    'dividing-by-6',
    'dividing-by-7',
    'dividing-by-8',
    'dividing-by-9',
    'dividing-by-10',
    'division_0.5',
    'division_1',
    'division_4',
    'evaluating-numerical-expressions-with-exponents',
    'explicit-formulas-for-arithmetic-sequences',
    'integration-and-differentiation-of-power-series',
    'integration-by-u-substitution',
    'integration-of-rational-functions-by-division-and-partial-fractions',
    'interpreting-quadratic-models',
    'linear_equations_2',
    'linear_equations_3',
    'linear_inequalities',
    'logarithmic-differentiation',
    'making-ten-2',
    'manipulating-formulas',
    'matrix_inverse_2x2',
    'more-square-and-cube-root-problems',
    'motion-along-a-curve-differential-calc',
    'multi-digit-addition',
    'multi-digit-subtraction',
    'multiplication_0.5',
    'multiplication_4',
    'multiply-binomials-coefficient',
    'multiply-by-2-and-4',
    'multiply-by-5-and-10',
    'multiplying_decimals',
    'multiplying_decimals_0.5',
    'multiplying_decimals_1',
    'multiplying_polynomials',
    'multiplying_radicals',
    'multiplying-by-0-or-1',
    'multiplying-unit-fractions-and-whole-numbers',
    'multistep_equations_with_distribution',
    'multi-step-equations-rational',
    'multi-step-word-problems-with-whole-numbers',
    'net-change-algebraic',
    'one_step_equations',
    'one_step_inequalities',
    'one-step-add-sub-equations-2',
    'one-step-mult-div-equations-2',
    'order_of_operations_2',
    'parametric-curve-arc-length',
    'particle-motion',
    'perform-elementary-matrix-row-operations',
    'poly-by-x-no-remainders',
    'probability-normal-density-curves',
    'rate-conversion',
    'rational-exp-prop-challenge',
    'second-derivatives-parametric-functions',
    'simplify-radicals-and-exponentials',
    'solve-exponential-equations-using-properties-of-exponents-advanced',
    'solve-matrix-equations-add-sub',
    'solve-exponential-equations-using-properties-of-exponents--basic-',
    'solve-matrix-equations-scalar-multiplication',
    'solving_for_a_variable',
    'standard_deviation',
    'standard_deviation_of_a_population',
    'subtracting_decimals_2',
    'subtracting_fractions',
    'subtracting-decimals-without-the-standard-algorithm-2',
    'subtracting-decimals-without-the-standard-algorithm-3',
    'subtracting-decimals-without-the-standard-algorithm-6',
    'subtracting-decimals-without-the-standard-algorithm-8',
    'subtraction_1',
    'subtraction_2',
    'subtraction_4',
    'tangents-to-polar-curves',
    'two-step-equations-with-decimals-and-fractions',
    'understanding-logs-as-inverse-exponentials',
    'understanding-series',
    'understand-matrix-coordinates',
    'unit-vector',
    'u-substitution--definite-integrals',
    'Variance',
    'write-common-fractions-as-decimals',
    'writing-equations-for-parallel-or-perpendicular-lines',
    'writing-systems-of-equations-as-matrix-equations',
    'zero-product-property',
    'adding-1s-or-10s-to-two-digit-numbers'
    ]

new_line_join = [
    'adding_and_subtracting_complex_numbers',
    'adding_and_subtracting_rational_expressions',
    'adding_and_subtracting_rational_expressions_2',
    'adding_vectors',
    'adding-and-subtracting-fractions-with-unlike-denominators-word-problems',
    'adding-three-numbers',
    'divide-fractions-by-whole-numbers',
    'dividing_fractions_1.5',
    'evaluating-sequences-in-recursive-form',
    'factor-quadratics-common-factor',
    'finding-missing-factors--1-digit-multiplication-',
    'find-the-missing-number--addition-and-subtraction-within-1000-',
    'functions_2',
    'functions_matching_inputs_outputs',
    'greatest-common-factor-of-monomials',
    'higher-order-partial-derivatives',
    'integer_sums',
    'least_common_multiple',
    'linear_equations_1',
    'logarithms_1',
    'logarithms_1.5',
    'missing-number-within-20--add-and-subtract-_modal=2',
    'proportions_1',
    'put-together',
    'real-and-imaginary-parts-of-complex-numbers',
    'recursive-formulas-for-geometric-sequences',
    'relate-addition-and-subtraction',
    'adding_and_subtracting_rational_numbers'
]

def custom_join1(arr):
    # todo if endswith $ and starts with $ merge those
    result = ""
    for i, s in enumerate(arr):
        result += s
        if i < len(arr) - 1 and not s.strip().endswith("."):
            result += " "
        else:
            result += "\n"

    if "Choose 1 answer: Choose 1 answer:" in result:
        result = result.replace("Choose 1 answer: Choose 1 answer:", "Choose 1 answer:")

    return result


def has_consecutive_numbers(input_string):
    pattern = r'\d{3}'  # Regular expression to match three consecutive digits

    if re.search(pattern, input_string):
        return True
    else:
        return False

def remove_pattern(input_string):
    pattern = r'\[.*?\?]'
    cleaned_string = re.sub(pattern, '', input_string)
    return cleaned_string

def ends_with_pattern(input_string):
    pattern = r'.*\\end\{.*\}\$\$?$'
    return re.match(pattern, input_string) is not None

def extract_last_formula(input_string):
    pattern = r'\$([^$]+)\$'
    matches = re.findall(pattern, input_string)
    if matches:
        return matches[-1]
    else:
        return None

def custom_join2(question: str, hints: list):
    question = question.strip()
    s = ['=$', '={?}$', '=?$', '$', '=$', '={?}$']
    question_ends_with_equation = any(question.replace(' ', '').endswith(c) for c in s)
    hints_start_with_equals = hints[0].replace(' ', '').startswith('$=')

    if 'Choose 1 answer' in question:
        question = question.split('Choose 1 answer')[0]

    if question_ends_with_equation and hints_start_with_equals:
        question = question.replace('{?}', '').replace('=$', '$').replace('= $', '$')
        hints.insert(0, question)
    elif hints_start_with_equals and question.endswith('$ ?') or question.endswith('$?'):
        last_formula = extract_last_formula(question)
        if last_formula:
            hints[0] = last_formula + remove_prefix(hints[0], '$')
    elif question_ends_with_equation and '=' in question and not question.strip().endswith('?'):
        question += '?'

    answer = hints[0].strip()
    for hint in hints[1:]:
        hint = remove_pattern(hint).strip()

        if answer.endswith('$') and hint.replace(' ', '').startswith('$='):
            # connect the two lines by =
            answer = remove_suffix(answer, '$') + " " + remove_prefix(hint, '$')
        elif hint[0].isupper() and answer[-1] != '.' and not ends_with_pattern(answer):
            # add a point to indicate the sentence ended
            answer = answer + '. ' + hint
        else:
            last_formula = extract_last_formula(answer)
            if last_formula:
                start = remove_suffix(last_formula, '$').strip()
                first_term = start.split('=')[0].strip()
                if answer.endswith("$%s$" % last_formula) and hint.startswith("$" + start):
                    answer = remove_suffix(answer, "$%s$" % last_formula) + remove_prefix(hint, start)
                elif answer.endswith("$%s$" % last_formula) and remove_prefix(hint, '$').strip().startswith(first_term):
                    answer = remove_suffix(answer, "$") + remove_prefix(remove_prefix(hint, '$').strip(), first_term)
                else:
                    answer += " " + hint.strip()
            else:
                answer += " " + hint.strip()

    if question_ends_with_equation and hints_start_with_equals:
        line = answer
    else:
        line = question + '\n' + answer

    if not line.endswith('.') and not line.endswith('}S'):
        line += '.'

    return answer, line


def amps_iterator(return_text=False, raw=False, latex_text=False, start=0, verbose=True, return_id=False, return_question_index=False):
    dir = 'data/amps/khan'

    ctr = 0
    start_time = time.time()
    for subdir, dirs, files in list(os.walk(dir)):
        for file in files:
            path = os.path.join(subdir, file)
            if any(e in path for e in excluded):
                continue

            if path.endswith('.json'):
                ctr += 1
                try:
                    if start is not None and ctr < start:
                        continue

                    question, answer, line = process_data(path)
                    if question is None:
                        continue

                    if return_text:
                        try:
                            if latex_text:
                                from sympy.parsing.latex.text import LaTeXText
                                t = LaTeXText(line)
                            else:
                                from tools import Text
                                t = Text(line, raw=raw)
                            if return_id:
                                id = hash(path)
                                if return_question_index:
                                    yield t, id, -1
                                else:
                                    yield t, id
                            else:
                                if return_question_index:
                                    yield t, -1
                                else:
                                    yield t
                        except Exception:
                            pass
                    else:
                        yield {'question': question, 'answer': answer}

                    if verbose and ctr % 1 == 0:
                        duration_seconds = time.time() - start_time
                        print("Processed %d amps files in %s (%ss) (current file: %s)" % (ctr, humanize.naturaldelta(timedelta(seconds=duration_seconds)), duration_seconds, path))
                except Exception as e:
                    print("An error occurred during processing an amps file: %s, %s" % (path, e))
            else:
                print(path)
    duration_seconds = time.time() - start_time
    print("Finished %d amps files in %s (%ss)" % (ctr, humanize.naturaldelta(timedelta(seconds=duration_seconds)), duration_seconds))

def process_data(path):
    data = json.load(open(path, 'r+'))

    question = data['problem']
    hints = data['hints']

    if any(x in " ".join(hints) + question for x in [r'\llap', '~~~', 'SOH CAH TOA']):
        # files containing these symbols indicate unusual math formatting and math symbols
        return None, None, None

    if has_consecutive_numbers(path):
        # file like .../123/...
        answer, line = custom_join2(question, hints)
        #line = question + '\n' + answer
    elif any(f in path for f in new_line_join):
        answer = '\n'.join(hints)
        line = question + '\n' + answer
    else:
        answer, line = custom_join2(question, hints)
    return question, answer, line

if __name__ == '__main__':
    p = process_data(r"data/amps/khan/504/1607900679.json")
    for pp in p:
        print(pp)