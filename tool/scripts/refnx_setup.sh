#!/usr/bin/env bash

cd $1
if [ -e "${1}/refnx" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n refnx python=3.9 numpy scipy cython pandas h5py xlrd pytest pyqt matplotlib ipywidgets jupyter
git clone https://github.com/refnx/refnx.git
cd refnx
git checkout 3ee46609de88d730d064f5185f93d944566cded6 -b evalcommit
conda activate refnx
conda install -y pip pytest
pip install uncertainties attrs periodictable corner theano pymc3
pip install orsopy
pip install coverage
conda deactivate
cd -