#!/usr/bin/env bash
# ./parlai_setup.sh [dir]
cd $1
if [ -e "${1}/parlai" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n parlai python=3.7 -y
git clone https://github.com/facebookresearch/ParlAI.git parlai
cd parlai
git checkout 4b1d07d0eeb14f849ad930eeb001327f9bfc2db1 -b evalcommit
conda activate parlai
conda install -y pip pytest
pip install scipy==1.2.1 torch==1.6
pip install -r requirements.txt
pip install coverage
conda deactivate
cd -