#!/usr/bin/env bash

cd $1
if [ -e "${1}/stellargraph" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n stellargraph -y python=3.7
git clone https://github.com/stellargraph/stellargraph.git
cd stellargraph
git checkout 3c2c8c18ab4c5c16660f350d8e23d7dc39e738de -b evalcommit
conda activate stellargraph
conda install -y pip pytest
pip install -e ".[test]"
pip install coverage
conda deactivate
cd -