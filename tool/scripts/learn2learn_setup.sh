#!/usr/bin/env bash

cd $1
if [ -e "${1}/learn2learn" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n learn2learn -y python=3.7
git clone https://github.com/learnables/learn2learn.git
cd learn2learn
git checkout e06f68228ce10fc1264c79b377b1c0815ce47a8a -b evalcommit
conda activate learn2learn
conda install -y pip pytest
pip install Cython
pip install -e .
pip install coverage
conda deactivate
cd -