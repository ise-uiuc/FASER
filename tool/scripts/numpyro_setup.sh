#!/usr/bin/env bash

cd $1
if [ -e "${1}/pyro" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n numpyro -y python=3.7
git clone https://github.com/pyro-ppl/numpyro.git
cd numpyro
git checkout 9987eb737e4b6da5d83da961e636d51a5ae36dde -b evalcommit
conda activate numpyro
conda install -y pip pytest
pip install -e ".[dev,test]"
pip install coverage
conda deactivate
cd -