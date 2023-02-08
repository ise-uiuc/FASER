#!/usr/bin/env bash

cd $1
if [ -e "${1}/zfit" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n zfit -y python=3.7
git clone https://github.com/zfit/zfit.git
cd zfit
git checkout 9987eb737e4b6da5d83da961e636d51a5ae36dde -b evalcommit
conda activate zfit
conda install -y pip pytest
pip install -e ".[alldev]"
pip install coverage
conda deactivate
cd -