# GitHub setup and installation guide

## 1. Create the repository

Create a public GitHub repository, for example:

```text
panelplots
```

Do not add a README, license, or `.gitignore` on GitHub if you want to push this folder exactly as generated.

## 2. Push the package

From the package folder:

```bash
git init
git add .
git commit -m "Initial panelplots package"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/panelplots.git
git push -u origin main
```

## 3. Install from GitHub

After the repository is public:

```bash
pip install git+https://github.com/YOUR_USERNAME/panelplots.git
```

## 4. Install locally for development

```bash
git clone https://github.com/YOUR_USERNAME/panelplots.git
cd panelplots
pip install -e .
```

## 5. Run the Peru example from a local file

```bash
python examples/peru_blackmarble_example.py /path/to/peru_daily_panel.parquet --output-dir presentation_figures
```

## 6. Use in a notebook

```python
from panelplots import plot_spaghetti, plot_fanchart
```

Then call the functions with a long-format DataFrame.
