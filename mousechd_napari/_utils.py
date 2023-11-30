import logging
from pathlib import Path
import os
import hashlib
import tempfile
import sys
import subprocess
import shutil
import time
import json

import numpy as np
import SimpleITK as sitk

import tensorflow as tf

from mousechd.datasets.preprocess import Preprocess
from mousechd.datasets.resample import resample_folder
from mousechd.segmentation.segment import segment_from_folder
from mousechd.datasets.utils import (get_largest_connectivity,
                                     crop_heart_bbx,
                                     maskout_non_heart,
                                     norm_min_max,
                                     resample3d)
from mousechd.utils.tools import CACHE_DIR
from mousechd.classifier.utils import CLF_DIR
from mousechd.classifier.models import load_MouseCHD_model
from mousechd.classifier.gradcam import GradCAM3D

tmp_dir = os.path.join(tempfile.gettempdir(), "MouseCHD")
os.makedirs(tmp_dir, exist_ok=True)

LIB_PATH = "miniconda3/envs/mousechd/bin/mousechd"
SLURM_CMD = "srun -J 'mousechd' --qos=gpu --gres=gpu:1"
MODULE_LS = "module use /c7/shared/modulefiles && module load cuda/11.8.0_520.61.05"
EXPORTS = "XLA_FLAGS=--xla_gpu_cuda_data_dir=/c7/shared/cuda/11.8.0_520.61.05"


def is_relative_to(path1, path2):
    """Check if path2 is relative to path1

    Args:
        path1 (str): parent directory
        path2 (str): child directory

    Returns:
        bool: is relative to
    """
    return Path(path2).is_relative_to(Path(path1))


def get_relative_sever_dir(shared_folder, path):
    
    rootdir = shared_folder
    print(rootdir)
    while not os.path.ismount(rootdir):
        rootdir = os.path.dirname(rootdir)
    
    try:       
        return os.path.join(os.path.basename(rootdir),
                            Path(path).relative_to(rootdir))
    except ValueError:
        logging.info(f"Path {path} is not on shared folder!")
    

def segment_heart(resrc,
                  workdir,
                  heart_name,
                  servername="",
                  shared_folder="",
                  lib_path=LIB_PATH,
                  slurm=False,
                  slurm_cmd=SLURM_CMD
                  ):
    outdir = os.path.join(workdir, "HeartSeg")
    # Check if the mask is exist
    if not os.path.isfile(os.path.join(outdir, f"{heart_name}.nii.gz")):
        indir = os.path.join(workdir, "processed", heart_name)
        os.makedirs(indir, exist_ok=True)
        shutil.copy2(os.path.join(tmp_dir, f"{heart_name}.nii.gz"),
                    os.path.join(indir, f"{heart_name}_0000.nii.gz"))
          
        if resrc == "local":
            segment_from_folder(indir=os.path.join(workdir, "processed", heart_name),
                                outdir=os.path.join(workdir, "HeartSeg"))
        else:
            print("Run on server")
            server_home = subprocess.getoutput(f'ssh {servername} "pwd"')
            
            print(f"server home: {server_home}")

            server_indir = get_relative_sever_dir(shared_folder, indir)
            server_outdir = get_relative_sever_dir(shared_folder, outdir)
            print(f"indir: {server_indir}")
            print(f"outdir: {server_outdir}")
            
            if slurm:
                cmd = slurm_cmd + f" {server_home}/{lib_path} segment"
            else:
                cmd = f"{server_home}/{lib_path} segment"
            
            out = subprocess.getoutput(f'ssh {servername} "{cmd} -indir {server_home}/DATA/{server_indir} -outdir {server_home}/DATA/{server_outdir}"')
            
            print(out)
            
            shutil.rmtree(indir)
        
    img = sitk.ReadImage(os.path.join(outdir, f"{heart_name}.nii.gz"))
    
    return sitk.GetArrayFromImage(img)


def segment_hearts(resrc,
                   workdir,
                   servername="",
                   shared_folder="",
                   lib_path=LIB_PATH,
                   slurm=False,
                   slurm_cmd=SLURM_CMD):
    
    outdir = os.path.join(workdir, "HeartSeg")
    indir = os.path.join(workdir, "retrain", "processed", "images")
    
    if resrc == "local":
        segment_from_folder(indir=indir, outdir=outdir)
    else:
        server_home = subprocess.getoutput(f'ssh {servername} "pwd"')
        
        server_indir = get_relative_sever_dir(shared_folder, indir)
        server_outdir = get_relative_sever_dir(shared_folder, outdir)

        if slurm:
            cmd = slurm_cmd + f" {server_home}/{lib_path} segment"
        else:
            cmd = f"{server_home}/{lib_path} segment"
        
        out = subprocess.getoutput(f'ssh {servername} "{cmd} -indir {server_home}/DATA/{server_indir} -outdir {server_home}/DATA/{server_outdir}"')
        
        print(out)

def resample_im(im, ma):
    cropped_im, cropped_ma = crop_heart_bbx(im, ma, pad=(5,5,5))
    resampled_im = maskout_non_heart(cropped_im, cropped_ma)
    
    return norm_min_max(resampled_im)
    
    

def diagnose_heart(model, im, heart):
    
    resampled_im = resample_im(im=im, ma=heart)
    input_shape = model.layers[0].output_shape[0][1:4]
    img = sitk.GetImageFromArray(resampled_im)
    img.SetSpacing((0.02, 0.02, 0.02))
    img = resample3d(img, input_shape[::-1])
    im = sitk.GetArrayFromImage(img)
    im = norm_min_max(im)
    im = np.expand_dims(im, axis=3)
    im = np.expand_dims(im, axis=0)
    
    preds = model.predict(tf.convert_to_tensor(im))[0]
    
    # GradCAM
    class_idx = np.argmax(preds)
    grad_model = GradCAM3D(model)
    gradcam = grad_model.compute_heatmap(im, classIdx=class_idx, upsample_size=resampled_im.shape)
    
    return preds, gradcam   


def find_format(indir):
    path = next(os.path.join(indir, f) for f in os.listdir(indir) if not f.startswith("."))
    
    if os.path.isdir(path):
        return "DICOM"
    elif path.endswith(".nii.gz"):
        return "NIFTI"
    elif path.endswith(".nrrd"):
        return "NRRD"
    else:
        return "Unknown"


def preprocess(indir, 
               outdir,
               pp_resrc="local",
               servername="",
               shared_folder="",
               lib_path=LIB_PATH,
               slurm=False,
               slurm_cmd=SLURM_CMD,
               ):
    
    fmt = find_format(indir)
    database = os.path.dirname(indir)
    imdir = os.path.basename(indir)
    if pp_resrc == "local":
        Preprocess(database=database,
                   imdir=imdir,
                   outdir=outdir,
                   im_format=fmt
                   ).preprocess()
    else:
        server_home = subprocess.getoutput(f'ssh {servername} "pwd"')
        logging.info(f"database: {database}")
        logging.info(f"shared_folder: {shared_folder}")
        database = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, database)
        outdir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, outdir)
        logfile = os.path.join(outdir, "..", "retrain.log")
        
        if slurm:
            cmd = slurm_cmd + f" {server_home}/{lib_path} preprocess"
        else:
            cmd = f"{server_home}/{lib_path} preprocess"
            
        out = subprocess.getoutput(f'ssh {servername} "{cmd} -database {database} -imdir {imdir} -outdir {outdir} -im_format {fmt} -logfile {logfile}"')
        
        print(out)
    

def resample(workdir,
             pp_resrc="local",
             servername="",
             shared_folder="",
             lib_path=LIB_PATH,
             slurm=False,
             slurm_cmd=SLURM_CMD):
    
    indir = os.path.join(workdir, "retrain", "processed", "images")
    maskdir = os.path.join(workdir, "HeartSeg")
    outdir = os.path.join(workdir, "retrain", "resampled")
    metafile = os.path.join(workdir, "retrain", "processed", "metadata.csv")
    if pp_resrc == "local":
        resample_folder(imdir=indir,
                        maskdir=maskdir,
                        outdir=outdir,
                        metafile=metafile,
                        meta_sep=",",
                        save_images=True)
    else:
        server_home = subprocess.getoutput(f'ssh {servername} "pwd"')
        indir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, indir)
        maskdir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, maskdir)
        outdir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, outdir)
        metafile = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, metafile)
        logfile = os.path.join(outdir, "..", "retrain.log")
        
        if slurm:
            cmd = slurm_cmd + f" {server_home}/{lib_path} resample"
        else:
            cmd = f"{server_home}/{lib_path} resample"
        
        out = subprocess.getoutput(f'ssh {servername} "{cmd} -imdir {indir}" -maskdir {maskdir} -outdir {outdir} -metafile {metafile} -save_images 1 -logfile {logfile}')
        
        print(out)
        

def retrain(resrc,
            retrain_dir,
            outdir,
            exp,
            epochs=20,
            servername="",
            shared_folder="",
            lib_path=LIB_PATH,
            slurm=False,
            slurm_cmd=SLURM_CMD,
            module=False,
            module_ls=MODULE_LS,
            export=False,
            exports=EXPORTS
            ):
    
    data_dir = os.path.join(retrain_dir, "resampled")
    label_dir = os.path.join(retrain_dir, "label")
    configs = os.path.join(CLF_DIR, "configs.json")
    log_dir = os.path.join(outdir, "LOGS")
    logfile = os.path.join(retrain_dir, "retrain.log")
    
    exec_placeholder = " -exp_dir {} -exp {} -data_dir {} -label_dir {} -configs {} -log_dir {} -evaluate none -logfile {} -epochs {}"
    
    if resrc == "local":
        import argparse
        from mousechd.run import train_clf
        params = {"exp_dir": outdir,
                  "exp": exp,
                  "data_dir": data_dir,
                  "label_dir": label_dir,
                  "configs": configs,
                  "log_dir": log_dir,
                  "logfile": logfile,
                  "epochs": epochs}
        args = argparse.Namespace(**params)
        train_clf.main(args)
        
        return "Sucess"
    
    else:
        server_home = subprocess.getoutput(f'ssh {servername} "pwd"')
        
        outdir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, outdir)
        data_dir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, data_dir)
        label_dir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, label_dir)
        configs = f"{server_home}/.MouseCHD/Classifier/configs.json"
        log_dir = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, log_dir)
        logfile = f"{server_home}/DATA/" + get_relative_sever_dir(shared_folder, logfile)
        
        # Extra modules
        extra_cmd = ""
        if module:
            modules = module_ls.split(";")
            for m in modules:
                extra_cmd += f"{m} && "
        
        if export:
            exports = exports.split(";")
            for e in exports:
                extra_cmd += f"export {e} && "
        
        if slurm:
            cmd = extra_cmd + slurm_cmd + f" {server_home}/{lib_path} train_clf"
        else:
            cmd = extra_cmd + f"{server_home}/{lib_path} train_clf"
            
        cmd += exec_placeholder.format(outdir,
                                       exp,
                                       data_dir,
                                       label_dir,
                                       configs,
                                       log_dir,
                                       logfile,
                                       epochs)
        
        logging.info(f"cmd: {cmd}")
        
        
        out = subprocess.getoutput(f'ssh {servername} "{cmd}"')
        
        logging.info(out)
        
        if ("error" in out) and ("Terminated" not in out):
            logging.info(out)
            return "Error"
        else:
            return "Sucess"
        
              
################
# DISPLAY UTIS #
################
def gen_white2red_colormap(num=255):
    """
    Generate white to red colormap with transparent at 0
    """
    colors = np.linspace(
        start=[1, 1, 1, 1],
        stop=[1, 0, 0, 1],
        num=num,
        endpoint=True
    )
    colors[0] = np.array([1., 1., 1., 0])
    new_colormap = {
    'colors': colors,
    'name': 'white2red',
    'interpolation': 'linear'
    }
    
    return new_colormap

def gen_transturbo_colormap():
    """
    Generate transparent turbo color map
    """
    colors = np.load(os.path.join(CACHE_DIR, "Napari", "assets", "transturbo.npy"))
    
    colormap = {
        'colors': colors,
        'name': 'transturbo',
        'interpolation': 'linear'
    }
    
    return colormap
    