#!/usr/bin/env bash

cd $1
if [ -e "${1}/pyro" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n pyro -y python=3.6
git clone https://github.com/pyro-ppl/pyro.git
cd pyro
git checkout 3c6a591f8d18c7a65f716e9ff1241e0cd898b2da -b evalcommit
conda activate pyro
conda install -y pip pytest
pip install -r evalreqs.txt
pip install -e ".[dev,extras,test]"
pip install coverage
conda deactivate
cd -