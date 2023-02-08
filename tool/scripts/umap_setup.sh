#!/usr/bin/env bash

cd $1
if [ -e "${1}/umap" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n umap -y python=3.7
git clone https://github.com/lmcinnes/umap.git
cd umap
git checkout ec9832cbdb7f106a727e6bbd4c54c78fae30f26f -b evalcommit
conda activate umap
conda install -y pip pytest
pip install -e ".[parametric_umap]"
pip install coverage
conda deactivate
cd -