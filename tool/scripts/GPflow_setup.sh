#!/usr/bin/env bash

cd $1
if [ -e "${1}/GPflow" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n GPflow -y python=3.7
git clone https://github.com/GPflow/GPflow.git
cd GPflow
git checkout 501b8c2b8d1ef64a2e679e957137fc91871be08f -b evalcommit
conda activate GPflow
conda install -y pip pytest
pip install -e .
pip install coverage
conda deactivate
cd -