#!/usr/bin/env bash

cd $1
if [ -e "${1}/tfcausalimpact" ]; then
  echo "Already installed"
  exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n tfcausalimpact python=3.6 -y
git clone https://github.com/WillianFuks/tfcausalimpact.git
cd tfcausalimpact
git checkout adc465e7433863765fc0b190b1a676c4a0d61245 -b evalcommit

conda activate tfcausalimpact
conda install -y pip pytest
pip install -e .
pip install -r test-requirements.txt
pip install tensorflow_probability==0.12.2
pip install coverage
conda deactivate
