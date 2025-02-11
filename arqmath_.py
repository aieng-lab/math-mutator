import os
import pickle
import time
from datetime import timedelta
import humanize
from post_reader_record import DataReaderRecord
from Entities.Post import Answer, Question

class MamutDataReaderRecord(DataReaderRecord):

    def __init__(self, root_file_path, version=""):
        super().__init__(root_file_path, version)

    def question_iterator(self, include_answers=False, filter=None):
        for question in self.post_parser.map_questions.values():
            if filter and filter(question):
                continue

            if include_answers:
                answers = self.get_answers_for_question(question_id=question.post_id)
                yield question, answers
            else:
                yield question

    def question_answer_iterator(self, filter_question=None, filter_answer=None, start=0, end=None, verbose=True, questions_start=None, questions_len=None):
        values = list(self.post_parser.map_questions.values())
        start_time = time.time()

        if questions_start:
            values = values[questions_start:]

        if questions_len is not None:
            if questions_len == 0:
                print("question_len=0 given")
                return
            values = values[:questions_len]
        l = len(values)

        i = 0
        for j, question in enumerate(iter(values)):

            if verbose and i % 10 == 0:
                duration_seconds = time.time() - start_time
                print("Processed %d/%d question answer pairs in %s, yielded %d" % (i, l, humanize.naturaldelta(timedelta(seconds=duration_seconds)), j))

            if filter_question and filter_question(question):
                continue

            answers = question.answers
            if answers:
                for answer in answers:
                    if answer.votes is not None and (not filter_answer or not filter_answer(question, answer)):
                        i += 1
                        if i < start:
                            continue
                        else:
                            yield question, answer

                        if end and i >= end:
                            return

    def question_answers_iterator(self, filter_question=None, filter_answer=None, start=0, end=None, verbose=True, questions_start=None, questions_len=None, return_question_index=False):
        values = list(self.post_parser.map_questions.values())
        start_time = time.time()

        if questions_start:
            values = values[questions_start:]

        if questions_len is not None:
            if questions_len == 0:
                print("question_len=0 given")
                return
            values = values[:questions_len]
        l = len(values)

        i = 0
        for j, question in enumerate(iter(values)):

            if verbose and j % 10 == 0:
                duration_seconds = time.time() - start_time
                print("Processed %d/%d question answer pairs in %s" % (j, l, humanize.naturaldelta(timedelta(seconds=duration_seconds))))

            if filter_question and filter_question(question):
                continue

            answers = question.answers
            if answers:
                answers_ = []
                for answer in answers:

                    if answer.votes is not None and (not filter_answer or not filter_answer(question, answer)):
                        i += 1
                        if i < start:
                            continue
                        answers_.append(answer)

                if len(answers_) > 0:
                    if return_question_index:
                        yield question, answers_, j
                    else:
                        yield question, answers_

            if end and i >= end:
                return

    def text_iterator(self, start=0, end=None, questions_start=None, questions_len=None, verbose=True, filter_question=None, filter_answer=None, return_question_index=False):
        values = list(self.post_parser.map_questions.values())
        start_time = time.time()
        i = 0

        if questions_start:
            values = values[questions_start:]

        if questions_len is not None and questions_len is not False:
            if questions_len == 0:
                print("question_len=0 given")
                return
            values = values[:questions_len]
        l = len(values)

        for j, question in enumerate(iter(values)):

            if verbose and i % 100 == 0:
                duration_seconds = time.time() - start_time
                print("Processed %d/%d question/answers in %s, yielded %d" % (j, l, humanize.naturaldelta(timedelta(seconds=duration_seconds)), i))

            if filter_question and filter_question(question):
                continue

            if i < start:
                pass
            else:
                if return_question_index:
                    yield question, j
                else:
                    yield question
            i += 1

            answers = question.answers
            if answers:
                for answer in answers:
                    if answer.votes is not None and len(answer.votes) >= 5 and (not filter_answer or not filter_answer(question, answer)):
                        i += 1
                        if i < start:
                            continue
                        else:
                            if return_question_index:
                                yield answer, j
                            else:
                                yield answer

                        if end and i >= end:
                            return

    def count_questions(self, filter=None):
        return len(list(self.question_iterator(filter=filter)))

    def count_question_answer_pairs(self, filter_question=None, filter_answer=None):
        return len(list(self.question_answer_iterator(filter_question=filter_question, filter_answer=filter_answer)))

    def get_question_of_tag(self, tag):
        """
        Return a list of questions with a specific tag
        :param tag: tag to find questions having it
        :return: list of questions with the input tag
        """
        lst_of_questions = []
        for question_id in self.post_parser.map_questions:
            question = self.post_parser.map_questions[question_id]
            lst_tags = question.tags
            if tag in lst_tags:
                lst_of_questions.append(question)
        return lst_of_questions

def write(dir='data/arqmath', pickle_path='data/bin/arqmath.pickle'):
    dr = MamutDataReaderRecord(dir, version='.V1.3')
    print('Successfully generated DataReaderRecord')
    os.makedirs(os.path.dirname(pickle_path), exist_ok=True)
    pickle.dump(dr, open(pickle_path, 'wb'))
    return dr

def read(force=False):
    pickle_path = 'data/bin/ARQMath.pickle'
    try:
        if force:
            raise FileNotFoundError
        print('Read arqmath data...')
        return pickle.load(open(pickle_path, 'rb'))
    except FileNotFoundError:
        print("Could not read pickle. Try to generate it...")
        return write(pickle_path=pickle_path)



def get_text_answer(self, raw=False, remove_html=True, precalculate=False):
    from tools import Text
    return Text(self.body, remove_html=remove_html, raw=raw, precalculate=precalculate)

def get_text_question(self, raw=False, remove_html=True, precalculate=False):
    from tools import Text
    return Text(self.title + '\n' + self.body, remove_html=remove_html, raw=raw, precalculate=precalculate)

Answer.get_text = get_text_answer
Question.get_text = get_text_question