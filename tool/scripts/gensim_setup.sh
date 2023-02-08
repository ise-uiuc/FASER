#!/usr/bin/env bash
# ./gensim_setup.sh [dir]
cd $1
if [ -e "${1}/gensim" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n gensim python=3.7 -y
git clone https://github.com/RaRe-Technologies/gensim.git
cd gensim
git checkout 6e362663f23967f3c1931e2cb18d3d25f92aabb5 -b evalcommit
conda activate gensim
conda install -y pip
pip install pytest==6.0.0
pip install tensorflow==2.2.0
pip install numpy scipy
pip install -e .[docs,test]
conda deactivate
cd -