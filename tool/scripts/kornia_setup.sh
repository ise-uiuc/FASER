#!/usr/bin/env bash
# ./gensim_setup.sh [dir]
cd $1
if [ -e "${1}/kornia" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n kornia python=3.6 -y
git clone https://github.com/kornia/kornia.git
cd kornia
git checkout 3e765bd6da6fd92394daff1b2aec52ee42b6bd4f -b evalcommit
conda activate kornia
conda install -y pip
pip install pytest==6.0.0
pip install -e .[all]
pip install coverage
conda deactivate
cd -