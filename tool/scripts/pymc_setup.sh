#!/usr/bin/env bash
cd $1
if [ -e "${1}/pymc" ]; then
  echo "Already installed"
  exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n pymc python=3.7 -y
git clone https://github.com/pymc-devs/pymc.git
cd pymc
git checkout a50b386f73df3960e2a7b45d0c2e24831715907c -b evalcommit

conda activate pymc
conda install -y pip pytest
pip install -r requirements-dev.txt
pip install -e .

pip install coverage
conda deactivate
