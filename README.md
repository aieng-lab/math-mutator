# MAMUT: A Novel Framework for Modifying Mathematical Formulas for the Generation of Specialized Datasets for Language Model Training
> Jonathan Drechsel, Anja Reusch, Steffen Herbold

[![arXiv](https://img.shields.io/badge/arXiv-2502.20855-B31B1B.svg)](https://arxiv.org/abs/2502.20855)


This repository contains the official source code for the dataset generation of [MAMUT: A Novel Framework for Modifying Mathematical Formulas for the Generation of Specialized Datasets for Language Model Training](https://arxiv.org/abs/2502.20855).

This repository contains the code for generating the datasets, including preprocessing of the original [AMPS](https://github.com/hendrycks/math) and [ARQMath](https://github.com/ARQMath/ARQMathCode) datasets, formula filtering, extraction, validation, and more. The framework responsible for generating equivalent and falsified versions of mathematical formulas is available in [this SymPy fork](https://github.com/jdrechsel13/sympy-random-LaTeX).
The generated datasets are available on [Hugging Face](https://huggingface.co/datasets/ddrg):

| **Dataset**                                                                                 | **Description** | **Example(s)** |
|---------------------------------------------------------------------------------------------|---------------|---------------|
| [Math Formulas (MF)](https://huggingface.co/datasets/ddrg/math_formulas)                    | Mathematical formulas with high variance | $x\cdot x^N = x^{1 + N}$  <br> $(a - b)/(b*a) = -1/a + \frac{1}{b}$ |
| [Math Text (MT)](https://huggingface.co/datasets/ddrg/math_text)                            | Texts combining natural language and mathematical formulas | Identify $\sum_{n=0}^\infty (y_n - L)$ where $y_{n + 1} = (1 + y_n)^{\frac13}$ and $L^3 = L + 1$. Let $y > 2$ and let $f(y) = (1 + y)^{\frac13}$. Let $f^n(y)$ be the $n $ th iterate of $f(y)$. Let $ L $ be ... |
| [Named Math Formulas (NMF)](https://huggingface.co/datasets/ddrg/named_math_formulas)       | High variance formulas of famous named identities | **Name:** Pythagorean Thm., **Formula:** $c^2=b^2+a^2$ <br> **Name:** Binomial Formula, **Formula:** $(\alpha + z)^2 = z^2 + \alpha^2 + 2\cdot \alpha \cdot z$ |
| [Math Formula Retrieval (MFR)](https://huggingface.co/datasets/ddrg/math_formula_retrieval) | Pairs of formulas with labels indicating identical or different mathematical concepts | **Formula 1:** $1\cdot 2\cdot 3 \cdot \ldots \cdot n = n!$, **Formula 2:** $m!\coloneqq \prod_{k=1}^m k$, **Label:** Equivalent <br> **Formula 1:** $a^2+b^2=c^2$, **Formula 2:** $a^2+2^b=c^2$, **Label:** Not Equivalent |

### Quick Links

- [Mathematical Pre-Training Framework](https://github.com/aieng-lab/transformer-math-pretraining)
- [Mathematical Evaluation Framework](https://github.com/aieng-lab/transformer-math-evaluation)
- Mathematical Datasets
  - [ddrg/math_formulas](https://huggingface.co/datasets/ddrg/math_formulas): Math Formulas (MF)
  - [ddrg/math_text](https://huggingface.co/datasets/ddrg/math_text): Math Text (MT)
  - [ddrg/named_math_formulas](https://huggingface.co/datasets/ddrg/named_math_formulas): Named Math Formulas (NMF)
  - [ddrg/math_formula_retrieval](https://huggingface.co/datasets/ddrg/math_formula_retrieval): Math Formula Retrieval (MFR)
- Mathematical Models generated based on MAMUT-enhanced data:
  - [aieng-lab/bert-base-cased-mamut](https://huggingface.co/aieng-lab/bert-base-cased-mamut): based on [bert-base-cased](https://huggingface.co/bert-base-cased) 
  - [aieng-lab/math_pretrained_bert-mamut](https://huggingface.co/aieng-lab/math_pretrained_bert-mamut): based on [AnReu/math_pretrained_bert](https://huggingface.co/AnReu/math_pretrained_bert)  (best mathematical model based on our evaluation)
  - [aieng-lab/MathBERT-mamut](https://huggingface.co/aieng-lab/MathBERT-mamut): based on [tbs17/MathBERT](https://huggingface.co/tbs17/MathBERT)
  - [[ddrg/math_structure_deberta](https://huggingface.co/ddrg/math_structure_deberta): mathematical further pretrained based on [microsoft/deberta-v3-base](https://huggingface.co/microsoft/deberta-v3-base) - not published as part of the MAMUT paper, but trained with the same data and framework]


## Install

### Prerequisites
- Install [conda](https://docs.conda.io/en/latest/miniconda.html) or [miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Install [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Installation Steps

#### 1. Clone the repository
```bash
git clone https://github.com/aieng-lab/math-mutator
cd math-mutator
```

#### 2. Create a Conda Environment:
```bash
conda create --name mamut python=3.10
conda activate mamut
conda install pip
pip install -r requirements.txt
```

#### 3. Install `jdrechsel13/sympy-random-LaTeX`:
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
set PYTHONPATH=%PYTHONPATH%;/path/to/ARQMathCode
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

### 7. Setup for Experiments [Optional]
See below for the setup of the experiments (Mathematical Pretraining and Evaluation).

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
  

## Experimental Results Reproduction

The experiments are split into pre-training mathematical models and evaluating them based on an IR fine-tuning task.

### Mathematical Pre-Training

- Install [Mathematical Pretraining Framework](https://github.com/aieng-lab/transformer-math-pretraining)
- Run `transformer-math-pretraining/scripts/ma.sh` to pre-train mathematical models.
  - Should run on a server with 8 A100 GPUs
  - Rough Time Estimate: 12 hours per Pre-Training used (i.e. 48 hours for MF+MT+NMF+MFR)

### Mathematical Evaluation

- Install [Mathematical Evaluation Framework](https://github.com/aieng-lab/transformer-math-evaluation)
- Run `transformer-math-evaluation/scripts/mamut.sh` to compute all fine-tuning results reported in the paper.
  - Copy the pre-trained models to the folder specified in the script
- Use the methods in `transformer-math-evaluation/src/export/nmf.py` to generate the tables and figures reporting the results.

## Implementation Details

- `sympy-random-LaTeX/generator.py` contains the core functionality of MAMUT, implementing the version generation interface and falsifying strategies
- Internally, the strategies Random and Manual (known from the MAMUT paper) are implemented as single strategy (`strategy_random_formula`) 
  - These can be distinguished based on the provided meta data (`strategy_random_formula` contains a json dict, entry `no_version` is True for Manual and False for Random)
- The randomized LatexPrinter can be found in `sympy-random-LaTeX/sympy/printing/latex.py` 
  - The randomization settings can be found in `sympy-random-LaTeX/sympy/settings.py`

## CITATION
If you use this code, generated datasets, or published mathematical models, please cite the following paper:
```bibtex
@misc{drechsel2025mamutnovelframeworkmodifying,
      title={{MAMUT}: A Novel Framework for Modifying Mathematical Formulas for the Generation of Specialized Datasets for Language Model Training}, 
      author={Jonathan Drechsel and Anja Reusch and Steffen Herbold},
      year={2025},
      eprint={2502.20855},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2502.20855}, 
}
```
