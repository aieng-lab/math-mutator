# TODO Introducing a Novel Framework for Modifying Mathematical Formulas: Developing Specialized Datasets for Language Model Training
> Jonathan Drechsel, Anja Reusch, Steffen Herbold

This repository contains the official source code for the dataset generation of TODO

## Install
```bash
git clone math-mutator
git clone https://github.com/jdrechsel13/sympy-random-LaTeX.git
cd math-mutator
conda create --file environment.yml # todo?
conda activate mamut
conda install pip

# add sympy-random-LaTeX to the PYTHONPATH
cd ../sympy-random-LaTeX
pip install -r requirements.txt
pip install -e .
export PYTHONPATH=$PYTHONPATH:$(pwd) # todo check
cd ../math-mutator


git clone https://github.com/ARQMath/ARQMathCode.git arqmath
./arqmath/bin/install
```

todo arqmath

add arqmath to PYTHONPATH

## Data Generation

- Download the original data (AMPS and ARQMATH): `download.py`
  - Downloads AMPS and ARQMath data into `data/amps` and `data/arqmath` respectively
- Generate Named Math Formulas (NMF): `named_math_formulas.py`
  - Generates the NMF dataset into `data/nmf` as `datasets.Dataset`
  - Intermediate results and a more detailed dataset can be found in `data/nmf.csv` (including an entry `stats` in `json` format containing the applied transformation steps)
- Generate Math Formula Retrieval (MFR): `math_formula_retrieval.py`
  - Generates the MFR dataset as `data/mfr.csv` based on `data/nmf.csv`
- Generate Math Formulas (MF): `math_formulas.py`
  - Generates the MF dataset as `data/math-formulas.csv`
- Generate Math Text (MT): `math_text.py`
  - Requires the ARQMath package to be available as `arqmath` (see Installation)
  - Generates the MT dataset as `data/math-text.csv`
  - Due to a long run time of that script (several days), specifically for ARQMath, you can use `generate_math_text_arqmath_asynch` to generate the data in parallel. You need to combine the data together afterwards.
  