#!/usr/bin/env bash

cd $1
if [ -e "${1}/allennlp" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n allennlp -y python=3.7
git clone https://github.com/allenai/allennlp.git
cd allennlp
git checkout 2cdb8742c8c8c3c38ace4bdfadbdc750a1aa2475 -b evalcommit
conda activate allennlp
conda install -y pip pytest
pip install -e .
pip install coverage
conda deactivate
cd -