#!/usr/bin/env bash
cd $1
if [ -e "${1}/deepchem" ]; then
  echo "Already installed"
  exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n deepchem python=3.7 -y
git clone https://github.com/deepchem/deepchem.git
cd deepchem
git checkout 8a9efc3249992b87cf9729850c8f35ddf65d42c0 -b evalcommit

conda activate deepchem
conda install -y pip pytest
pip install -e .
pip install -e .[jax]
pip install -e .[torch]
pip install -e .[tensorflow]
pip install coverage
pip install flaky
conda deactivate
