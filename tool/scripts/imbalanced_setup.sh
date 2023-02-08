#!/usr/bin/env bash
cd $1
if [ -e "${1}/imbalanced-learn" ]; then
  echo "Already installed"
  exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n imbalanced-learn python=3.7 -y
git clone https://github.com/scikit-learn-contrib/imbalanced-learn.git
cd imbalanced-learn
git checkout f1abf75d721dcf7deee77a41abc5fe147c64dc90 -b evalcommit

conda activate imbalanced-learn
conda install -y pip pytest
pip install .
pip install --no-build-isolation --editable .
pip install coverage
conda deactivate
