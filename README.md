# MAMUT: A Novel Framework for Modifying Mathematical Formulas for the Generation of Specialized Datasets for Language Model Training
> Jonathan Drechsel, Anja Reusch, Steffen Herbold

This repository contains the official source code for the dataset generation of [MAMUT: A Novel Framework for Modifying Mathematical Formulas for the Generation of Specialized Datasets for Language Model Training](todo).

This repository contains the code for generating the datasets, including preprocessing of the original [AMPS](https://github.com/hendrycks/math) and [ARQMath](https://github.com/ARQMath/ARQMathCode) datasets, formula filtering, extraction, validation, and more. The framework responsible for generating equivalent and falsified versions of mathematical formulas is available in [this SymPy fork](https://github.com/jdrechsel13/sympy-random-LaTeX).
The generated datasets are available on [Hugging Face](https://huggingface.co/datasets/ddrg):

| **Dataset** | **Description** | **Example(s)** |
|------------|---------------|---------------|
| [MF](https://huggingface.co/datasets/ddrg/math_formulas) | Mathematical formulas with high variance | $x\cdot x^N = x^{1 + N}$  <br> $(a - b)/(b*a) = -1/a + \frac{1}{b}$ |
| [MT](https://huggingface.co/datasets/ddrg/math_text) | Texts combining natural language and mathematical formulas | Identify $\sum_{n=0}^\infty (y_n - L)$ where $y_{n + 1} = (1 + y_n)^{\frac13}$ and $L^3 = L + 1$. Let $y > 2$ and let $f(y) = (1 + y)^{\frac13}$. Let $f^n(y)$ be the $n $ th iterate of $f(y)$. Let $ L $ be ... |
| [NMF](https://huggingface.co/datasets/ddrg/named_math_formulas) | High variance formulas of famous named identities | **Name:** Pythagorean Thm., **Formula:** $c^2=b^2+a^2$ <br> **Name:** Binomial Formula, **Formula:** $(\alpha + z)^2 = z^2 + \alpha^2 + 2\cdot \alpha \cdot z$ |
| [MFR](https://huggingface.co/datasets/ddrg/math_formula_retrieval) | Pairs of formulas with labels indicating identical or different mathematical concepts | **Formula 1:** $1\cdot 2\cdot 3 \cdot \ldots \cdot n = n!$, **Formula 2:** $m!\coloneqq \prod_{k=1}^m k$, **Label:** Equivalent <br> **Formula 1:** $a^2+b^2=c^2$, **Formula 2:** $a^2+2^b=c^2$, **Label:** Not Equivalent |

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
  
  
## CITATION
If you use this code or the provided datasets, please cite the following paper:
```bibtex
TODO
```