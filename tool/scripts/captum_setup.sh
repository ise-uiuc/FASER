#!/usr/bin/env bash

cd $1
if [ -e "${1}/captum" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n captum -y python=3.7
git clone https://github.com/pytorch/captum.git
cd captum
git checkout 9bf44e87ec0a1f2f6c9009cddecdd40f833dc6c0 -b evalcommit
conda activate captum
conda install -y pip pytest
pip install -e ".[dev]"
pip install coverage
conda deactivate
cd -