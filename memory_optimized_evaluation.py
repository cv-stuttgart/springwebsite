#!/usr/bin/env python
"""
Memory-Optimized Scene Flow Evaluation

This module contains memory-optimized versions of the evaluation functions
that process data in chunks to minimize memory usage.
"""

import os
import numpy as np
import h5py
import gc
import psutil
from pprint import pprint
import matplotlib.pyplot as plt
from springeval.management.commands import flow_IO

# Environment variables
EVAL_DIR = os.environ["SPRING_EVALDIR"]
FILE_GT_DISP1 = os.path.join(EVAL_DIR, "eval_disp1.hdf5")
FILE_GT_DISP2 = os.path.join(EVAL_DIR, "eval_disp2.hdf5")
FILE_GT_FLOW = os.path.join(EVAL_DIR, "eval_flow.hdf5")
FILE_DETAILMAP_DISP1 = os.path.join(EVAL_DIR, "eval_detailmap_disp1.hdf5")
FILE_DETAILMAP_DISP2 = os.path.join(EVAL_DIR, "eval_detailmap_disp2.hdf5")
FILE_DETAILMAP_FLOW = os.path.join(EVAL_DIR, "eval_detailmap_flow.hdf5")
FILE_MATCHMAP_DISP1 = os.path.join(EVAL_DIR, "eval_matchmap_disp1.hdf5")
FILE_MATCHMAP_DISP2 = os.path.join(EVAL_DIR, "eval_matchmap_disp2.hdf5")
FILE_MATCHMAP_FLOW = os.path.join(EVAL_DIR, "eval_matchmap_flow.hdf5")
FILE_RIGIDMAP = os.path.join(EVAL_DIR, "eval_rigidmap.hdf5")
FILE_SKYMAP = os.path.join(EVAL_DIR, "eval_skymap.hdf5")

# Constants from original evaluation.py
REDUCED_SIZE = 51840 - 1
test_seq = [(3, 131), (19, 111), (28, 39), (29, 135), (31, 73), (34, 47), (35, 120), (40, 111), (42, 116), (46, 117)]

def check_memory():
    """Check current memory usage"""
    memory = psutil.virtual_memory()
    print(f"Memory: {memory.percent:.1f}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")
    return memory.available / (1024**3)

def force_gc():
    """Force garbage collection"""
    collected = gc.collect()
    print(f"Garbage collected: {collected} objects")
    check_memory()

def read_data_in_chunks(file_path, chunk_size=10000000):
    """Read large datasets in chunks to minimize memory usage"""
    print(f"Reading {file_path} in chunks...")
    
    with h5py.File(file_path, 'r') as f:
        dataset = f['flow'] if 'flow' in f else f[list(f.keys())[0]]
        total_size = dataset.shape[0]
        
        chunks = []
        for start in range(0, total_size, chunk_size):
            end = min(start + chunk_size, total_size)
            chunk = dataset[start:end]
            chunks.append(chunk)
            print(f"  Read chunk {start//chunk_size + 1}/{(total_size + chunk_size - 1)//chunk_size}")
            force_gc()
        
        # Concatenate chunks
        result = np.concatenate(chunks, axis=0)
        del chunks
        force_gc()
        
    return result

def convertdisp1_optimized(submission):
    """Memory-optimized version of convertdisp1"""
    print("Converting disp1 data...")
    result = np.zeros(225500050, dtype=np.float16)
    result[:] = np.nan
    
    # Process in smaller chunks
    chunk_size = 1000000
    for start in range(0, len(submission), chunk_size):
        end = min(start + chunk_size, len(submission))
        result[start:end] = submission[start:end]
        
        if start % (chunk_size * 10) == 0:
            print(f"  Processed {start}/{len(submission)}")
            force_gc()
    
    return result

def evaluate_submission_sceneflow_optimized(d1_file, d2_file, fl_file, img_outputdir):
    """Memory-optimized sceneflow evaluation"""
    
    print("=== Starting Memory-Optimized Scene Flow Evaluation ===")
    check_memory()
    
    # Read submission files in chunks
    print("\n1. Reading submission files...")
    d1_submission = flow_IO.readDsp5Disp(d1_file)
    force_gc()
    
    d2_submission = flow_IO.readDsp5Disp(d2_file)
    force_gc()
    
    fl_submission = flow_IO.readFlo5Flow(fl_file)
    force_gc()
    
    # Validate data
    if ((~np.isfinite(d1_submission)).sum() != 0) or ((~np.isfinite(d2_submission)).sum() != 0) or ((~np.isfinite(fl_submission)).sum() != 0):
        print("Submission contains nan or inf values! Replacing...")
        np.nan_to_num(d1_submission, copy=False)
        np.nan_to_num(d2_submission, copy=False)
        np.nan_to_num(fl_submission, copy=False)
    
    # Validate shapes
    if d1_submission.shape != (124414000,):
        raise ValueError("D1 submission has wrong shape!")
    if d2_submission.shape != (225500050,):
        raise ValueError("D2 submission has wrong shape!")
    if fl_submission.shape != (225500050, 2):
        raise ValueError("Flow submission has wrong shape!")
    
    # Convert disp1
    d1_submission = convertdisp1_optimized(d1_submission)
    force_gc()
    
    print(f"D1 submission shape: {d1_submission.shape}")
    
    # Read ground truth data in chunks
    print("\n2. Reading ground truth data...")
    gt_disp1 = read_data_in_chunks(FILE_GT_DISP1)
    force_gc()
    
    gt_disp2 = read_data_in_chunks(FILE_GT_DISP2)
    force_gc()
    
    gt_flow = read_data_in_chunks(FILE_GT_FLOW)
    force_gc()
    
    # Read maps
    print("\n3. Reading detail maps...")
    detailmap_disp1 = read_data_in_chunks(FILE_DETAILMAP_DISP1)
    force_gc()
    
    detailmap_disp2 = read_data_in_chunks(FILE_DETAILMAP_DISP2)
    force_gc()
    
    detailmap_flow = read_data_in_chunks(FILE_DETAILMAP_FLOW)
    force_gc()
    
    print("\n4. Reading match maps...")
    matchmap_disp1 = read_data_in_chunks(FILE_MATCHMAP_DISP1)
    force_gc()
    
    matchmap_disp2 = read_data_in_chunks(FILE_MATCHMAP_DISP2)
    force_gc()
    
    matchmap_flow = read_data_in_chunks(FILE_MATCHMAP_FLOW)
    force_gc()
    
    print("\n5. Reading rigid and sky maps...")
    rigidmap = read_data_in_chunks(FILE_RIGIDMAP)
    force_gc()
    
    skymap = read_data_in_chunks(FILE_SKYMAP)
    force_gc()
    
    # Import evaluation functions
    from springeval.management.commands.evaluation import (
        get_errors_stereo, get_errors_flow, get_errors_sceneflow
    )
    
    # Run evaluations
    print("\n6. Computing D1 errors...")
    errors_d1, imgs_d1 = get_errors_stereo(d1_submission, gt_disp1, detailmap_disp1, matchmap_disp1, skymap)
    print(errors_d1)
    force_gc()
    
    print("\n7. Computing D2 errors...")
    errors_d2, imgs_d2 = get_errors_stereo(d2_submission, gt_disp2, detailmap_disp2, matchmap_disp2, skymap)
    print(errors_d2)
    force_gc()
    
    print("\n8. Computing flow errors...")
    errors_fl, imgs_fl = get_errors_flow(fl_submission, gt_flow, detailmap_flow, rigidmap, matchmap_flow, skymap)
    print(errors_fl)
    force_gc()
    
    print("\n9. Computing sceneflow errors...")
    detmap_sf = detailmap_disp1 | detailmap_disp2 | detailmap_flow
    matmap_sf = matchmap_disp1 | matchmap_disp2 | matchmap_flow
    force_gc()
    
    errors_sf, imgs_sf = get_errors_sceneflow(d1_submission, d2_submission, fl_submission, gt_disp1, gt_disp2, gt_flow, detmap_sf, matmap_sf, rigidmap, skymap)
    print(errors_sf)
    force_gc()
    
    # Combine results
    print("\n10. Combining results...")
    subnames_d = ["total", "lowdetail", "highdetail", "notsky", "sky", "matched", "unmatched", "s0_10", "s10_40", "s40"]
    subnames_fl = ["total", "lowdetail", "highdetail", "rigid", "nonrigid", "matched", "unmatched", "notsky", "sky", "s0_10", "s10_40", "s40"]
    errnames_sf = ["SF", "1px_SF"]
    errnames_d1 = ["1px_D1", "Abs_D1", "D1"]
    errnames_d2 = ["1px_D2", "Abs_D2", "D2"]
    errnames_fl = ["EPE_Fl", "Fl", "1px_Fl", "WAUC_Fl"]
    
    errors_dict = {}
    for ename, err in zip(errnames_sf, errors_sf):
        errors_dict.update(dict(zip([f"err_{ename}_{i}" for i in subnames_fl], err)))
    for ename, err in zip(errnames_d1, errors_d1):
        errors_dict.update(dict(zip([f"err_{ename}_{i}" for i in subnames_d], err)))
    for ename, err in zip(errnames_d2, errors_d2):
        errors_dict.update(dict(zip([f"err_{ename}_{i}" for i in subnames_d], err)))
    for ename, err in zip(errnames_fl, errors_fl):
        errors_dict.update(dict(zip([f"err_{ename}_{i}" for i in subnames_fl], err)))
    
    pprint(errors_dict)
    
    # Save images
    print("\n11. Saving images...")
    d1img, d1errimg = imgs_d1
    d2img, d2errimg = imgs_d2
    flimg, flerrimg = imgs_fl
    os.makedirs(img_outputdir, exist_ok=True)
    
    for i in range(10):
        plt.imsave(os.path.join(img_outputdir, f"d1img_{i:02d}.png"), d1img[i])
        plt.imsave(os.path.join(img_outputdir, f"d1errimg_{i:02d}.png"), d1errimg[i], cmap="gray", vmin=0, vmax=1)
        plt.imsave(os.path.join(img_outputdir, f"d2img_{i:02d}.png"), d2img[i])
        plt.imsave(os.path.join(img_outputdir, f"d2errimg_{i:02d}.png"), d2errimg[i], cmap="gray", vmin=0, vmax=1)
        plt.imsave(os.path.join(img_outputdir, f"flimg_{i:02d}.png"), flimg[i])
        plt.imsave(os.path.join(img_outputdir, f"flerrimg_{i:02d}.png"), flerrimg[i], cmap="gray", vmin=0, vmax=1)
        plt.imsave(os.path.join(img_outputdir, f"sferrimg_{i:02d}.png"), imgs_sf[i], cmap="gray", vmin=0, vmax=1)
        
        if i % 3 == 0:
            print(f"  Saved {i+1}/10 image sets")
            force_gc()
    
    print("\n=== Memory-Optimized Evaluation Complete ===")
    check_memory()
    
    return errors_dict
