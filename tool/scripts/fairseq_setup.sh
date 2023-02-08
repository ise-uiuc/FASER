#!/usr/bin/env bash
cd $1
if [ -e "${1}/fairseq" ]; then
  echo "Already installed"
  exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n fairseq python=3.6 -y
git clone https://github.com/pytorch/fairseq.git
cd fairseq
git checkout 8548f1d40124a036af7f9df55a45030451459823 -b evalcommit

conda activate fairseq
conda install -y pip pytest
pip install torch
pip install --editable ./
pip install coverage
conda deactivate
