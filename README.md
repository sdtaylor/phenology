# pyPhenology  
[![Build Status](https://travis-ci.org/sdtaylor/pyPhenology.svg?branch=master)](https://travis-ci.org/sdtaylor/pyPhenology) 
[![License](http://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/sdtaylor/pyPhenology/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/pyphenology/badge/?version=master)](http://pyphenology.readthedocs.io/en/master/?badge=master)
[![codecov](https://codecov.io/gh/sdtaylor/pyPhenology/branch/master/graph/badge.svg)](https://codecov.io/gh/sdtaylor/pyPhenology)
[![DOI](http://joss.theoj.org/papers/10.21105/joss.00827/status.svg)](https://doi.org/10.21105/joss.00827)  

Plant phenology models in python with a scikit-learn inspired API

## Full documentation  

[http://pyphenology.readthedocs.io/en/master/](http://pyphenology.readthedocs.io/en/master/)


## Installation
Requires: scipy, pandas, and numpy

Install via pip

```
pip install pyPhenology
```

Or install the latest version from Github  

```
pip install git+git://github.com/sdtaylor/pyPhenology
```

## Usage  

A Thermal Time growing degree day model:

```
from pyPhenology import models, utils
observations, predictors = utils.load_test_data(name='vaccinium')
model = models.ThermalTime()
model.fit(observations, predictors)
model.get_params()
{'t1': 85.704951490688927, 'T': 7.0814430573372666, 'F': 185.36866570243012}
```

Any of the parameters in a model can be set to a fixed value. For example the thermal time model with the threshold T set to 0 degrees C

```
model = models.ThermalTime(parameters={'T':0})
model.fit(observations, predictors)
model.get_params()
{'t1': 26.369813953905265, 'F': 333.76534368004388, 'T': 0}
```

## Citation

If you use this software in your research please cite it as:

Taylor, S. D. (2018). pyPhenology: A python framework for plant phenology modelling. Journal of Open Source Software, 3(28), 827. https://doi.org/10.21105/joss.00827

Bibtex:
```
@article{Taylor2018,
author = {Taylor, Shawn David},
doi = {10.21105/joss.00827},
journal = {Journal of Open Source Software},
mendeley-groups = {Software/Data},
month = {aug},
number = {28},
pages = {827},
title = {{pyPhenology: A python framework for plant phenology modelling}},
url = {http://joss.theoj.org/papers/10.21105/joss.00827},
volume = {3},
year = {2018}
}

```

## Acknowledgments

Development of this software was funded by
[the Gordon and Betty Moore Foundation's Data-Driven Discovery Initiative](http://www.moore.org/programs/science/data-driven-discovery) through
[Grant GBMF4563](http://www.moore.org/grants/list/GBMF4563) to Ethan P. White.
