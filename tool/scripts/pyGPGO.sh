#!/usr/bin/env bash

cd $1
if [ -e "${1}/pyGPGO" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n pyGPGO -y python=3.8
git clone https://github.com/josejimenezluna/pyGPGO.git
cd pyGPGO
git checkout 587d03a20a60bc135c913849fcfd01b1354ef6e8 -b evalcommit
conda activate pyGPGO
conda install -y pip pytest
pip install -r requirements_rtd.txt
pip install -e .
pip install coverage
pip uninstall -y theano
conda install -c conda-forge theano-pymc -y
conda deactivate
cd -