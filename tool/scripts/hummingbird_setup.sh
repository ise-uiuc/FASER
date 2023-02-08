#!/usr/bin/env bash

cd $1
if [ -e "${1}/hummingbird" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n hummingbird -y python=3.7
git clone https://github.com/microsoft/hummingbird.git
cd hummingbird
git checkout ddf6043959086bfaeb8e46aea58eed36517916c8 -b evalcommit
conda activate hummingbird
conda install -y pip pytest
pip install -e ".[test]"
pip install coverage
conda deactivate
cd -