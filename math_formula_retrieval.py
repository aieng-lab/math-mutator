import random
from pathlib import Path
import pandas as pd


def generate(input='data/nmf.csv', false_positives=4, output = 'data/mfr.csv'):
    df = pd.read_csv(input, encoding='utf8')
    result = {k: [] for k in ['formula1', 'formula2', 'label', 'formula1_name_id']}

    for k, (id, data) in enumerate(df.groupby('formula_name_id')):
        print(id)
        false_candidates = data[~data['label']]
        true_candidates = data[data['label']]

        true_candidates = true_candidates['formula'].tolist()
        false_candidates = false_candidates['formula'].tolist()

        for lhs in true_candidates:
            # generate single true positive
            rhs = random.choice(true_candidates)

            result['formula1'].append(lhs)
            result['formula2'].append(rhs)
            result['label'].append(True)
            result['formula1_name_id'].append(id)

            # generate false positive
            for _ in range(false_positives):
                result['formula1'].append(lhs)
                rhs = random.choice(false_candidates)
                result['formula2'].append(rhs)
                result['label'].append(False)
                result['formula1_name_id'].append(id)

    df = pd.DataFrame.from_dict(result)
    print(df)
    Path('/'.join(output.split('/')[:-1])).mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    true_df = df[df['label']]
    l = len(df)
    trues = len(true_df)
    falses = l - trues

    print("Number of trues %d, of falses %d, factor false %f" % (trues, falses, falses / trues))
    epochs = 500000 / ((2 * trues * 0.85) / 16)
    print("Number of epochs for 500k steps: %f" % epochs)


if __name__ == '__main__':
    generate(input='data/nmf.csv', output='data/mfr.csv')