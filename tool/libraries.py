import os


class LibrarySpec(object):
    def __init__(self, d):
        for key in d:
            self.__setattr__(key, d[key])

    def __repr__(self):
        return "{0}".format(self.name)


# get top directory
filepath = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../"))

PROJECT_DIR = filepath
LIBRARIES = [
    {
        "name": "PsyNeuLink",
        "conda_env": "PsyNeuLink",
        "parallel": True,
        "path": "{0}/projects/PsyNeuLink/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["torch", "numpy"]
    },
    {
        "name": "autokeras",
        "conda_env": "autokeras",
        "parallel": True,
        "path": "{0}/projects/autokeras/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "tensorflow"]
    },
{
        "name": "fairseq",
        "conda_env": "fairseq",
        "parallel": True,
        "path": "{0}/projects/fairseq/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "torch"]
    },
{
        "name": "pyGPGO",
        "conda_env": "pyGPGO",
        "parallel": True,
        "path": "{0}/projects/pyGPGO/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy"]
    },
    {
        "name": "bambi",
        "conda_env": "bambi",
        "parallel": True,
        "path": "{0}/projects/bambi/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy"]
    },
    {
        "name": "gan",
        "conda_env": "gan",
        "parallel": True,
        "path": "{0}/projects/gan/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "pymc3",
        "conda_env": "pymc3",
        "parallel": True,
        "path": "{0}/projects/pymc3".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy"]
    },
    {
        "name": "pymc-learn",
        "conda_env": "pymc-learn",
        "parallel": True,
        "path": "{0}/projects/pymc-learn".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy"]
    },
    {
        "name": "gpytorch",
        "conda_env": "gpytorch",
        "parallel": True,
        "path": "{0}/projects/gpytorch/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["torch", "numpy"]
    },
    {
        "name": "qiskit-aqua",
        "conda_env": "qiskit-aqua",
        "parallel": True,
        "path": "{0}/projects/qiskit-aqua/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["torch", "numpy", "tensorflow"]
    },

    {
        "name": "allennlp",
        "conda_env": "allennlp",
        "enabled": True,
        "parallel": True,
        "path" : "{0}/projects/allennlp/".format(PROJECT_DIR),
        "deps": ["torch", "numpy"]
    },
    {
        "name": "cleverhans",
        "conda_env": "cleverhans",
        "parallel": True,
        "path": "{0}/projects/cleverhans/".format(PROJECT_DIR),
        "enabled": True,
        "threads" : 5,
        "deps": ["numpy", "torch", "tensorflow"]
    },
    {
        "name": "captum",
        "conda_env": "captum",
        "parallel": True,
        "path": "{0}/projects/captum/tests".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["torch", "numpy"]
    },
    {
        "name": "geomstats",
        "conda_env": "geomstats",
        "parallel": True,
        "path": "{0}/projects/geomstats/tests".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["torch", "numpy", "tensorflow"]
    },
    {
        "name": "botorch",
        "conda_env": "botorch",
        "parallel": True,
        "path": "{0}/projects/botorch/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["torch", "numpy"]
    },
    {
        "name": "garage",
        "conda_env": "garage",
        "parallel": True,
        "path": "{0}/projects/garage/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["torch", "numpy", "tensorflow"]
    },
    {
        "name": "metal",
        "conda_env": "metal",
        "parallel": True,
        "path": "{0}/projects/metal/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "torch"]
    },
    {
        "name": "rasa",
        "conda_env": "rasa",
        "parallel": True,
        "enabled": True,
        "path" : "{0}/projects/rasa/".format(PROJECT_DIR),
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "snorkel",
        "conda_env": "snorkel",
        "parallel": True,
        "path": "{0}/projects/snorkel/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "tensorflow", "torch"]
    },
    {
        "name": "sonnet",
        "conda_env": "sonnet",
        "parallel": True,
        "path": "{0}/projects/sonnet/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "vision",
        "conda_env": "vision",
        "parallel": True,
        "path": "{0}/projects/vision/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "torch"]
    },
    {
        "name": "tensor2tensor",
        "conda_env": "tensor2tensor",
        "parallel": True,
        "enabled": True,
        "path" : "{0}/projects/tensor2tensor/".format(PROJECT_DIR),
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "tensorflow",
        "conda_env": "tensorflow",
        "parallel": True,
        "enabled": True,
        "path": "{0}/projects/tensorflow/".format(PROJECT_DIR),
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "pytorch",
        "conda_env": "pytorch",
        "parallel": True,
        "enabled": True,
        "path": "{0}/projects/pytorch/".format(PROJECT_DIR),
        "deps": ["numpy", "pytorch"]
    },
    {
        "name": "zfit",
        "conda_env": "zfit",
        "parallel": True,
        "path": "{0}/projects/zfit/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy", "tensorflow", "torch"]
    },
    {
        "name": "LiberTem",
        "conda_env": "libertem",
        "parallel": True,
        "path": "{0}/projects/LiberTEM/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy",  "torch"]
    },
    {
        "name": "PySyft",
        "conda_env": "pysyft",
        "parallel": True,
        "path": "{0}/projects/PySyft/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy",  "torch", "tensorflow"]
    },
    {
        "name": "raster-vision",
        "conda_env": "raster-vision",
        "parallel": True,
        "path": "{0}/projects/raster-vision/".format(PROJECT_DIR),
        "enabled": True,
        "deps": ["numpy",  "torch"]
    },
    {
        "name": "pyro",
        "conda_env": "pyro",
        "path": "{0}/projects/pyro".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "torch"]
    },
    {
        "name": "sbi",
        "conda_env": "sbi",
        "path": "{0}/projects/sbi".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "torch"]
    },
{
        "name": "dopamine",
        "conda_env": "dopamine",
        "path": "{0}/projects/dopamine".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "tensorflow"]
    },
{
        "name": "pytorch-lightning",
        "conda_env": "pytorch-lightning",
        "path": "{0}/projects/pytorch-lightning".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "torch"]
    },
    {
        "name": "fastai",
        "conda_env": "fastai",
        "path": "{0}/projects/fastai".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "torch"]
    },
    {
        "name": "flair",
        "conda_env": "flair",
        "path": "{0}/projects/flair".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "torch"]
    },
    {
        "name": "trax",
        "conda_env": "trax",
        "path": "{0}/projects/trax".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "torch", "tensorflow"]
    },

    {
        "name": "ml-agents",
        "conda_env": "ml-agents",
        "path": "{0}/projects/ml-agents".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "magenta",
        "conda_env": "magenta",
        "path": "{0}/projects/magenta".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "gensim",
        "conda_env": "gensim",
        "path": "{0}/projects/gensim".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "tensorflow"]
    },
    {
        "name": "imbalanced-learn",
        "conda_env": "imbalanced-learn",
        "path": "{0}/projects/imbalanced-learn".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "tensorflow"]
    },
{
        "name": "numpyro",
        "conda_env": "numpyro",
        "path": "{0}/projects/numpyro".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy"]
    },
{
        "name": "parlai",
        "conda_env": "parlai",
        "path": "{0}/projects/parlai".format(PROJECT_DIR),
        "enabled": True,
        "parallel": True,
        "deps": ["numpy", "torch"]
    }
]


LIBRARIES = [LibrarySpec(lib) for lib in LIBRARIES]

#print(LIBRARIES)