import json
import multiprocessing
import os
import random
import time
from collections import Counter
from datetime import timedelta

import humanize
import pandas as pd
import sklearn
from datasets import DatasetDict, Dataset

from sympy.generator import FormulaGenerator
from tools import make_dict_serializable


class FormulaTemplate:

    def __init__(self, data, additional_names, id, factor_false=1):
        self.templates = [FormulaGenerator(d, additional_names, id, factor_false=factor_false) for d in data]
        self.id = id

    def amounts(self, true_positives: bool=None, sum_values=True):
        s = [t.amounts(true_positives) for t in self.templates]
        if sum_values:
            return sum(s)
        return s

    def generate_versions(self, max=100, iterator=False, return_stats=False, strategies=None):
        for i in range(max):
            t = random.choice(self.templates)
            if iterator is not None:
                for v in t.generate_versions_iterator(1, return_stats=return_stats, strategies=strategies):
                    name = t.random_name()
                    if return_stats:
                        version = (name, *v[0], v[1])
                    else:
                        version = (name, *v)
                    yield version
            else:
                t.generate_versions(1, return_stats=return_stats, strategies=strategies)

    def get_random_version(self, return_stats=False, only_true_version=False):
        index = random.choices(list(range(len(self.templates))), weights=self.amounts(sum_values=False), k=1)[0]
        return self.templates[index].get_random_version(return_stats=return_stats, only_true_version=only_true_version)


    def update_similar_formulas(self, similar_formulas):
        for t in self.templates:
            #reduced_similar_formulas = {k: v for k, v in similar_formulas.items() if  != k}
            t.update_similar_formulas(similar_formulas)

    def update_random_formula(self, random_formula):
        for t in self.templates:
            t.update_random_formula(random_formula)

    def update_no_versions(self, no_versions):
        for t in self.templates:
            t.update_no_versions(no_versions)

    def analyze(self):
        tp = sum([f.amounts(True) for f in self.templates])
        fp = sum([f.amounts(False) for f in self.templates])
        print("%s: generated %d versions (%d TP, %d FP)" % (self.id, tp + fp, tp, fp))

    def set_not_allowed_names(self, names):
        for t in self.templates:
            t.set_not_allowed_names(names)


class Formula:

    def __init__(self, data, factor_false=1, similar_formulas=None, random_formula=None):
        if similar_formulas is None:
            similar_formulas = {}
        self.id = data['id']
        self.names = data['names']
        self.tag = data['tag']
        if 'text_substitution' in data:
            versions = data['versions'].copy()
            for v in data['versions']:
                v['text_substitution'] = data['text_substitution']
            del data['text_substitution']
        else:
            versions = data['versions']

        self.template = FormulaTemplate(versions, self.names, self.id, factor_false=factor_false)
        self.returned_versions = []
        self.template.update_similar_formulas(similar_formulas)
        self.template.update_random_formula(random_formula)
        if 'no-versions' in data:
            self.no_versions = data['no-versions']
        else:
            print("No no_versions given for <%s>" % self.id)
            self.no_versions = []
        print("Created Formula Template <%s>" % self.id)

    def amounts(self, positive_versions: bool=None):
        return self.template.amounts(positive_versions)

    def generate_versions(self, max=100, iterator=False, return_stats=False, strategies=None):
        if iterator:
            for v in self.template.generate_versions(max=max, iterator=iterator, return_stats=return_stats, strategies=strategies):
                if v not in self.returned_versions:
                    self.returned_versions.append(v)
                    yield v
        else:
            self.template.generate_versions(max, return_stats=return_stats, strategies=strategies)


    def get_random_version(self, max_tries=100, return_stats=False, only_true_version=False):
        for i in range(max_tries):
            if return_stats:
                name, formula, stats = self.template.get_random_version(return_stats=True, only_true_version=only_true_version)
                version = (name, *formula)
                if version not in self.returned_versions:
                    self.returned_versions.append(version)
                    return version, stats
            else:
                name, formula = self.template.get_random_version(return_stats=False, only_true_version=only_true_version)
                version = (name, *formula)
                if return_stats:
                    version_no_stats = version[:3]
                else:
                    version_no_stats = version

                if version_no_stats not in self.returned_versions:
                    self.returned_versions.append(version_no_stats)
                    return version

        if return_stats:
            return None, None
        return None

    def __str__(self):
        return "Formula %s" % self.template.templates

    def __name__(self):
        return str(self)

    def get_all_template_entries(self):
        return self.template.templates

    def update_no_versions(self, mapping):
        no_versions = []
        for nv in self.no_versions:
            if isinstance(nv, str):
                if nv in mapping:
                    no_versions += mapping[nv]
                else:
                    print('Unknown nv %s' % nv)
            elif isinstance(nv, dict):
                if 'text_substitution' in nv:
                    # text_substitutions in no_versions means, any single entry makes the formula wrong
                    for template in self.template.templates:
                        formula = template.formula
                        for key, value in nv['text_substitution'].items():
                            if isinstance(value, str):
                                value = [value]
                            for v in value:
                                if key in formula:
                                    new_formula = formula.replace(key, v)
                                    new_data = template.data
                                    new_data['formula'] = new_formula
                                    template_entry = FormulaGenerator(new_data, template.names, id=template.id)
                                    no_versions.append(template_entry)

                else:
                    template_entry = FormulaGenerator(nv)
                    no_versions.append(template_entry)
            else:
                print("Unknown nv type %s" % nv)
        self.template.update_no_versions(no_versions)

    def analyze(self):
        self.template.analyze()

    def set_not_allowed_names(self, names):
        self.template.set_not_allowed_names(names)


class create_formula_:

    def __init__(self, formulas):
        self.formulas = formulas
    def __call__(self, data):
        return Formula(data, factor_false=self.formulas.factor_false, random_formula=self.formulas.get_random_version)

class update_formula_no_versions_:
    def __init__(self, mapping):
        self.mapping = mapping.copy()

    def __call__(self, formula):
        print("Generate no-versions for %s" % formula.id)
        formula.update_no_versions(self.mapping)


class update_formula:
    def __init__(self, max, return_stats, strategies):
        self.max = max
        self.return_stats = return_stats
        self.strategies = strategies

    def __call__(self, formula):
        return list(formula.generate_versions(max=self.max, iterator=True, return_stats=self.return_stats, strategies=self.strategies))

def create_formulas(cls, state):
    return Formulas(path=None, **state)

class Formulas:

    def __init__(self, path='data/data.json', data=None, min=0, max=None, pool=False, factor_false=1, **kwargs):
        if path is None:
            for name, value in kwargs.items():
                setattr(self, name, value)
            for formula in self.formulas:
                formula.template.update_random_formula(self.get_random_version)
            return
        self.factor_false = factor_false
        start = time.time()
        if data is None:
            data = json.load(open(path, 'r+', encoding='utf8'))
        if max is not None:
            data = data[min:max]
        else:
            data = data[min:]

        from sympy.parsing.latex.logic import set_check_variables
        set_check_variables(False)

        from sympy.parsing.latex._parse_latex_antlr import set_check
        set_check(False)

        self.weights = []
        print("Read %s with %s raw formulas" % (path, len(data)))
        formulas = []
        mapping = {} # maps formula ids to all its templateEntries
        if pool:
            import multiprocessing
            num_cpu = multiprocessing.cpu_count()
            from multiprocessing import Pool
            with Pool(processes=num_cpu) as pool:
                results = pool.map(create_formula_(self), data)
        else:
            results = []
            creator = create_formula_(self)
            for f in data:
                results.append(creator(f))

        for i, (formula, d) in enumerate(zip(results, data)):
            formulas.append(formula)
            mapping[d['id']] = formula.get_all_template_entries()

        # determine not allowed names
        all_names = [n for d in data for n in d['names']]
        element_counts = Counter(all_names)
        elements_at_least_twice = [element for element, count in element_counts.items() if count >= 2]

        print("Create no-versions mapping")
        #with Pool(processes=num_cpu) as pool:
         #   pool.map(update_formula_no_versions_(mapping), formulas)
        for formula in formulas:
            update_formula_no_versions_(mapping)(formula)
            formula.set_not_allowed_names(elements_at_least_twice)
        print("Created no-versions mapping")

        self.formulas = formulas
        self.weights = [f.amounts() for f in self.formulas] # update weights, so random formulas can be already used

        print("Intialized Formulas Object in %ss" % (time.time() - start))


    def __reduce__(self):
        # Get all attributes except the non-pickable_attribute
        state = {key: value for key, value in vars(self).items()}

        # Here, we specify the custom function 'recreate_complex_pickable_class' to reconstruct the object.
        # The custom function takes two arguments: the class and the object's state.
        # The state contains all pickable attributes except the non-pickable_attribute.
        return (create_formulas, (self.__class__, state))


    def get_total_amount(self):
        return sum([f.amounts() for f in self.formulas])

    def generate_versions(self, max_per_template=100, pool=False, batch=10, iterator=False, return_stats=False, strategies=None, timeout_per_version=5):
        print("Start generations of versions")
        iterations = int(max_per_template / batch)
        start_time = time.time()

        def analyze():
            tp = sum([f.amounts(True) for f in self.formulas])
            fp = sum([f.amounts(False) for f in self.formulas])
            print("Generated %d versions (%d TP, %d FP)" % (sum(self.weights), tp, fp))
            for f in self.formulas:
                f.analyze()

        total_timeout = timeout_per_version * len(self.formulas) * batch
        for i in range(iterations):
            if i > 0 and (i % 10 == 0 or batch > 1):
                total = self.get_total_amount()
                duration_seconds = time.time() - start_time
                print("Generated %d formulas in %d/%d iterations in %s (%ss)" % (total, i * batch, max_per_template, humanize.naturaldelta(timedelta(seconds=duration_seconds)), duration_seconds))

            if pool and iterator:
                num_cpu = int(multiprocessing.cpu_count() / 2)
                u = update_formula(max=batch, return_stats=return_stats, strategies=strategies)
                results = []
                with multiprocessing.Pool(processes=num_cpu) as pool:
                    futures = [pool.apply_async(u, args=(v,)) for v in self.formulas]
                    time_to_wait = total_timeout  # initial time to wait
                    start_time = time.time()
                    for i, result in enumerate(futures):
                        print(i)
                        try:
                            return_value = result.get(time_to_wait)  # wait for up to time_to_wait seconds
                        except multiprocessing.TimeoutError:
                            print('Timeout for formula = ', i)
                        else:
                            results.append(return_value)
                        # how much time has exprired since we began waiting?
                        t = time.time() - start_time
                        time_to_wait = total_timeout - t
                        if time_to_wait < 0:
                            time_to_wait = 0


                for result in results:
                    for r in result:
                        yield r
            else:
                for formula in self.formulas:
                    if iterator:
                        for v in formula.generate_versions(max=batch, iterator=iterator, return_stats=return_stats, strategies=strategies):
                            yield v
                    else:
                        formula.generate_versions(max=batch, iterator=iterator, return_stats=return_stats, strategies=strategies)
            self.weights = [f.amounts() for f in self.formulas] # update weights, so random formulas can be already used


            if i % 1000 == 0:
                analyze()
        analyze()


    def get_random_version(self, return_stats=False, only_true_version=False):
        if sum(self.weights) == 0:
            if return_stats:
                return None, None
            return None

        formula = random.choices(self.formulas, weights=self.weights)[0]
        return formula.get_random_version(return_stats=return_stats, only_true_version=only_true_version)

    def get_all_random_versions(self):
        none_ctr = 0
        while True:
            formula = self.get_random_version()
            if formula is None:
                none_ctr += 1
            else:
                none_ctr = 0
                yield formula

            if none_ctr >= 10000:
                print("None Counter reached its limit")
                return



def generate_named_math_formulas(max=None, max_per_template=400000, return_data=False, version='', checkpoint=None, max_formulas=None, factor_false=1):
    random.seed(42)

    strategies = ['strategy_equality', 'strategy_inequality', 'strategy_swap', 'strategy_variables', 'strategy_random_formula', 'strategy_constants', 'strategy_distribute']

    checkpoint_file = 'data/nmf%s.csv' % version
    os.makedirs('data', exist_ok=True)

    print('Generate Formulas')
    f = Formulas(max=max_formulas, factor_false=factor_false)

    pairs = {
        'name': [],
        'formula': [],
        'label': [],
        'formula_name_id': [],
        'stats': [],
        'id': [],
        'is_text': [],
        'original_id': [],
        **{s: [] for s in strategies},
    }

    for s in strategies:
        pairs[s] = []

    if checkpoint:
        # try to fill the pairs and update formulas
        try:
            ds = pd.read_csv(checkpoint_file)
            pairs = {column: ds[column].tolist() for column in ds.columns if 'Unnamed' not in column}
            for formula in f.formulas:
                id = formula.id
                filtered = ds[ds['formula_name_id'] == id]
                formula.returned_versions = list(filtered.apply(lambda example: (example['name'], example['formula'], example['label'])))

            print("Start from checkpoint %s with %d" % (checkpoint, len(pairs['id'])))
        except Exception as e:
            print("Restart since checkpoint not found <%s>" % e)

    def add_pair(name, formula, label, stats):
        pairs['name'].append(name)
        pairs['formula'].append(formula)
        pairs['label'].append(label)
        pairs['id'].append(stats['id'])
        pairs['formula_name_id'].append(stats['formula_name_id'])
        pairs['is_text'].append(stats['is_text'])
        pairs['original_id'].append(stats['original_id'])

        del stats['id']
        del stats['original_id']
        del stats['is_text']
        del stats['formula_name_id']
        for s in strategies:
            pairs[s].append(len(stats[s]) > 0)
        pairs['stats'].append(dict(stats))

    def save_checkpoint():
        if checkpoint:
            try:
                print("Save checkpoint with %d formulas" % len(pairs['id']))
                pairs_ = make_dict_serializable(pairs)
                df = pd.DataFrame(pairs_)
                df.to_csv(checkpoint_file)
            except Exception:
                print("Couldn't save checkpoint")

    def create_dataset(version=version):
        if version:
            output = 'data/nmf'
        else:
            output = f'data/nmf-data/{version}'

        for i, entry in enumerate(f.generate_versions(max_per_template=max_per_template, iterator=True, return_stats=True)):
            if entry is not None:
                add_pair(*entry)

            if i % 10000 == 0:
                save_checkpoint()

            if max and i >= max:
                save_checkpoint()
                break
        print("Generated %d entries" % len(pairs['name']))
        save_checkpoint()

        pairs_ = make_dict_serializable(pairs.copy())

        df = pd.DataFrame(pairs_)
        df = df.sample(frac=1).reset_index(drop=True)
        df.to_csv(checkpoint_file)
        del df['stats']
        ds = Dataset.from_pandas(df)
        ds.save_to_disk(output)
        return ds

    if return_data:
        return create_dataset()
    else:
        create_dataset()

if __name__ == '__main__':
    generate_named_math_formulas()