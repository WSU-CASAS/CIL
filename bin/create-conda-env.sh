#!/bin/bash
#execute from project root as: $bash  ./bin/create-conda-env.sh
#source ~/anaconda/etc/profile.d/conda.sh
#export ENV_PREFIX=$PWD/env
#echo $PATH
module load miniconda3
conda env remove -n shenv
conda create -n shenv pandas scipy matplotlib pip pytest setuptools memory_profiler tqdm seaborn pyyaml
#will also install python, numpy, pytz
source activate shenv
pip install ~/myprojects/pyusm/
pip install ~/myprojects/discreteMSE/
pip install ~/myprojects/markov_chain_simulation/
source deactivate

