import os

import pandas as pd

from amps import amps_iterator
from tools import timeout, Text


def formula_iterator(start=0, amps=True, arqmath=True, file=None, return_index=False, file_tens=None):

    if arqmath:
        dir = 'data/arqmath/latex_representation_v3'

        symbols = ['=', '\\Rightarrow', '\\implies']
        for subdir, dirs, files in os.walk(dir):
            if file is not None:
                files = [files[file]]

            for i, file in enumerate(files):
                print(file)
                tsv = pd.read_csv(dir + '/' + file, sep='\t', header=0)

                if file_tens is not None:
                    l = len(tsv)
                    lower = int(l / 10) * (file_tens - 1)
                    upper = int(l / 10) * file_tens
                    tsv = tsv[lower:upper]

                for j, formula in tsv.iterrows():
                    if start and j < start:
                        continue
                    try:
                        f = str(formula['formula'])
                        if not any(s in f for s in symbols):
                            continue

                        if len(f) < 6:
                            continue
                        if return_index:
                            yield formula, j
                        else:
                            yield formula
                    except Exception:
                        pass

    if amps:
        for t, id in amps_iterator(return_text=True, start=start, return_id=True):
            for f in t.get_formulas():
                if return_index:
                    yield {'formula': f, 'post_id': id}, id
                else:
                    yield {'formula': f, 'post_id': id}

def data_iterator(start=0, end=None, amps=True, arqmath=True, raw=False, latex_text=False, single_question=False, include_questions=True, return_id=False, precalculate=False, questions_start=None, questions_len=None, verbose=True, pairs=False, return_question_index=False):
    ctr = 0
    if arqmath:
        from arqmath_ import read
        if not isinstance(arqmath, bool):
            arqmath_data = arqmath
        else:
            arqmath_data = read()
        if single_question:
            for text, question_index in arqmath_data.text_iterator(start=start, end=end, questions_start=questions_start, questions_len=questions_len, return_question_index=True):
                try:
                    print(text)
                    r = text.get_text(raw=raw, remove_html=True, precalculate=precalculate)

                    result = [r]

                    if return_id:
                        result.append(text.post_id)

                    if return_question_index:
                        result.append(question_index)
                    yield tuple(result)

                except Exception as e:
                    pass
                ctr += 1
        elif pairs:
            from sympy.parsing.latex.text import LaTeXText
            for question, answers, question_index in arqmath_data.question_answers_iterator(questions_start=questions_start, questions_len=questions_len, return_question_index=True):
                id = question.post_id
                try:
                    def generate():
                        l = LaTeXText(str(question.get_text(raw=raw)))
                        l.check_init()
                        return l
                    question = timeout(20)(generate)()
                    if isinstance(question, Exception):
                        raise question
                except Exception as e:
                    print(e)
                    continue
                answers_ = []
                for answer in answers:
                    try:
                        def generate():
                            l = LaTeXText(str(answer.get_text(raw=raw)))
                            l.check_init()
                            return l
                        answer_ = timeout(10)(generate)()
                        if isinstance(answer_, Exception):
                            raise answer_
                        answers_.append((answer_, answer.post_id))
                    except Exception:
                        pass
                if len(answers_) > 0:
                    if return_id:
                        yield question, answers_, question_index, id
                    else:
                        yield question, answers_, question_index

        else:
            for i, (question, answer) in enumerate(arqmath_data.question_answer_iterator(start=start, end=end, questions_start=questions_start, questions_len=questions_len, verbose=verbose)):
                def return_data(data):
                    if return_id:
                        return data, question.post_id
                    else:
                        return data

                ctr += 1
                try:
                    if latex_text:
                        from sympy.parsing.latex.text import LaTeXText
                        if include_questions:
                            d = LaTeXText(str(question.get_text(raw=raw)) + '\n' + str(answer.get_text(raw=raw)))
                        else:
                            d = LaTeXText(str(answer.get_text(raw=raw)))
                    else:
                        if include_questions:
                            d = Text(str(question.get_text(raw=True, remove_html=False)) + '\n' + str(answer.get_text(raw=True, remove_html=False)), remove_html=True, raw=raw, precalculate=precalculate)
                        else:
                            d = Text(str(answer.get_text(raw=True, remove_html=False)), remove_html=True, raw=raw, precalculate=precalculate)

                    yield return_data(d)
                except Exception:
                    pass

                if end and ctr >= end:
                    return
        arqmath_data = None

    if amps:
        start = max(0, start - ctr)
        yield from amps_iterator(return_text=True, raw=raw, latex_text=latex_text, start=start, return_id=return_id, return_question_index=return_question_index)

