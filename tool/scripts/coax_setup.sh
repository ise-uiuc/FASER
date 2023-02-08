#!/usr/bin/env bash

cd $1
if [ -e "${1}/coax" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n coax -y python=3.7
git clone https://github.com/coax-dev/coax
cd coax
git checkout 7553ab11b0f709e69d8d70d1d3b4326296b0b479 -b evalcommit
conda activate coax
conda install -y pip pytest
pip install -e ".[dev,doc]"
pip install coverage
conda deactivate
cd -