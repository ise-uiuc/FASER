#!/usr/bin/env bash

cd $1
if [ -e "${1}/nlp-architect" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n nlp-architect -y python=3.7
git clone https://github.com/IntelLabs/nlp-architect.git
cd nlp-architect
git checkout 60afd0dd1bfd74f01b4ac8f613cb484777b80284 -b evalcommit
conda activate nlp-architect
conda install -y pip pytest
pip install -e ".[dev]"
pip install coverage
conda deactivate
cd -