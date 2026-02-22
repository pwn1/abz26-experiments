abz26-experiments
-----------------

### FDR experiments
Instructions for running the experiments with FDR are described below.

#### FDR4 installation
To install FDR4 on a Linux machine, we recommend following the instructions [here](https://github.com/UoY-RoboStar/SLEEC-TK?tab=readme-ov-file#fdr4-installation)

#### Dining philosophers
There are two versions of the assertions for checking the dining philosophers CSP model, one without partial order reduction in the subfolder [Philosophers](Philosophers), and one with under [Philosophers/order](Philosophers/order).

To run the experiments, switch to the respective folder and then execute the python3 program `run.py`. Results can be summarised with `python3 ../../summarise.py phil --hide-context`

#### Alpha algorithm
To run the Alpha Algorithm experiments with FDR, you can use runexptask.py from the subfolder [AlphaAlgorithm_Timed_revision1/csp-gen/timed](AlphaAlgorithm_Timed_revision1/csp-gen/timed), i.e.
```
cd csp-gen/timed
python3 run.py
```
To summarise the results you can use the command ```python3 ../../../summarise.py D --hide-context```

