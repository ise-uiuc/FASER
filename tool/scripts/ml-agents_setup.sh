#!/usr/bin/env bash
# ./ml-agents_setup.sh [dir]
cd $1
if [ -e "${1}/ml-agents" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n ml-agents -y python=3.6
git clone https://github.com/Unity-Technologies/ml-agents.git
cd ml-agents
git checkout d2ee1e2569aa68d3ac0e1dd8d91f1bf812b9df27 -b evalcommit
conda activate ml-agents
conda install -y pip pytest
pip install -e ./ml-agents-envs
pip install -e ./ml-agents
pip install coverage
conda deactivate
cd -