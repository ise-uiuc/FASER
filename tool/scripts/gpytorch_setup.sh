#!/usr/bin/env bash
cd $1
if [ -e "${1}/gpytorch" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n gpytorch python=3.6 -y
git clone https://github.com/cornellius-gp/gpytorch.git gpytorch
cd gpytorch
git checkout 19e67f371d4641fd2f9ad7c8a7887361bdaa53d6 -b evalcommit
conda activate gpytorch
conda install -y pip pytest
pip install -e ".[dev,test]"
pip install coverage
conda deactivate
cd -