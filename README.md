# TODO Introducing a Novel Framework for Modifying Mathematical Formulas: Developing Specialized Datasets for Language Model Training
> Jonathan Drechsel, Anja Reusch, Steffen Herbold

This repository contains the official source code for the dataset generation of TODO

## Install

### Prerequisites
- Install [conda](https://docs.conda.io/en/latest/miniconda.html) or [miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Install [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Installation Steps

#### 1. Clone the repository
```bash
git clone math-mutator
cd math-mutator
```

#### 2. Create a Conda Environment:
```bash
conda create --name mamut python=3.10
conda activate mamut
conda install pip
pip install -r requirements.txt
```

#### 3. Install `jdrechsel/sympy-random-LaTeX`:
```bash
cd .. # go back to the root directory
git clone https://github.com/jdrechsel13/sympy-random-LaTeX.git
cd sympy-random-LaTeX
pip install -r requirements.txt
pip install -e . # install this sympy fork in editable mode (alternative: add the sympy-random-LaTeX path to the PYTHONPATH)
cd .. # go back to the root directory
```
#### 4. Clone `ARQMathCode`:
```bash
git clone https://github.com/ARQMath/ARQMathCode.git
```
#### 5. Add ARQMath to the `PYTHONPATH`:
##### Windows
Add the ARQMathCode directory to the system's `PYTHONPATH`: 
```bash
set PYTHONPATH=%PYTHONPATH%;C:\path\to\ARQMathCode
```
To make it permanent, edit the `Environment Variables` in the system settings.
##### Linux/maxOS
Append the path to your shell configuration file (e.g., `~/.bashrc`, `~/.bash_profile`, `~/.zshrc`):
```bash
export PYTHONPATH="$PYTHONPATH:/path/to/ARQMathCode"
source ~/.bashrc # or ~/.bash_profile, ~/.zshrc
```

#### 6. Verification [Optional]
```bash
python -c "import sympy; import post_reader_record; print('All packages are installed correctly')"
```

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
  