import os
from . import flow_IO
from . import flow_plot
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import warnings
import matplotlib



test_seq = [(3, 131), (19, 111), (28, 39), (29, 135), (31, 73), (34, 47), (35, 120), (40, 111), (42, 116), (46, 117)]

HERO_FRAMES = [
(3, "FW", "left", 17),
(19, "FW", "left", 55),
(28, "FW", "left", 18),
(29, "FW", "left", 68),
(31, "FW", "left", 32),
(34, "FW", "left", 24),
(35, "FW", "left", 89),
(40, "FW", "left", 55),
(42, "FW", "left", 60),
(46, "FW", "left", 47)]

HERO_FRAMES_SCALING_FLOW = [26.347498435869106, 25.917080500775057, 79.70264533832805, 134.82772934957595, 42.993279930014936, 94.37720532398501, 97.86993621159922, 21.393662186224248, 6.468752358846189, 89.13573477835665]
HERO_FRAMES_SCALING_FLOW = [i*1.05 for i in HERO_FRAMES_SCALING_FLOW]
HERO_FRAMES_SCALING_DISP1 = [21.53, 67.4, 75.25, 154.8, 18.4, 84.1, 151.9, 3.855, 54.28, 208.0]
HERO_FRAMES_SCALING_DISP2 = [21.5, 67.2, 75.2, 156.8, 18.16, 73.7, 151.4, 3.898, 54.28, 205.9]
HERO_FRAMES_SCALING_DISP = [0.5 * HERO_FRAMES_SCALING_DISP1[i] + 0.5 * HERO_FRAMES_SCALING_DISP2[i] for i in range(10)]


REDUCED_SIZE = 51840 - 1

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



colors = [
        [39, 40, 148],
        [49, 53, 148],
        [69, 116, 180],
        [115, 173, 209],
        [171, 216, 233],
        [223, 242, 248],
        [254, 223, 144],
        [253, 173, 96],
        [243, 108, 67],
        [215, 48, 38],
        [165, 0, 38]]


cdict = {}
for i, name in enumerate(["red", "green", "blue"]):
    data = []
    for j, c in enumerate(colors):
        data.append([j/10.0, c[i]/255.0, c[i]/255.0])
    cdict[name] = data

errorcmap = matplotlib.colors.LinearSegmentedColormap('errormap', segmentdata=cdict, N=256)


def geterrorimage(err):
    err = np.log2(err.clip(0.0001, None))
    err = err.clip(-5,5)
    err = (err + 5) / 10.0
    img = errorcmap(err)[...,:3]
    return img


def getWAUC(epe):
    wauc = 0
    N = (~np.isnan(epe)).sum()
    sum_wi = 0
    for i in range(1,101):
        wi = 1 - ((i-1) / 100.0)
        deltai = i / 20.0
        err = (epe <= deltai).sum()
        wauc += wi * err
        sum_wi += wi

    wauc = 100 * wauc / (N*sum_wi)
    return wauc


def getWAUCmap(epe, map_):
    wauc = 0
    N = (map_ & ~np.isnan(epe)).sum()
    sum_wi = 0
    for i in range(1,101):
        wi = 1 - ((i-1) / 100.0)
        deltai = i / 20.0
        err = (map_ & (epe <= deltai)).sum()
        wauc += wi * err
        sum_wi += wi

    wauc = 100 * wauc / (N*sum_wi)
    return wauc


def getboolmaperr(boolfield, map_, epe_):
    return 100 * (boolfield & map_).sum() / ((~np.isnan(epe_)) & map_).sum()


def get_errors_flow(submission, gt_flow, detailmap, rigidmap, matchmap, skymap):
    gt_veclen = np.linalg.norm(gt_flow.astype(np.float64), axis=-1)
    with warnings.catch_warnings():
        # nanmean throws warning for all-nan slices, but this is expected so suppress this warning
        warnings.simplefilter("ignore", category=RuntimeWarning)
        gt_veclen_mean = np.nanmean(gt_veclen, axis=1)
    lenmap1 = gt_veclen_mean < 10
    lenmap2 = (gt_veclen_mean >= 10) & (gt_veclen_mean < 40)
    lenmap3 = gt_veclen_mean >= 40

    maps_list = [~detailmap, detailmap, ~rigidmap, rigidmap, ~matchmap, matchmap, ~skymap, skymap, lenmap1, lenmap2, lenmap3]

    epe = gt_flow - submission[:,None,:]
    epe = epe.astype(np.float64)
    epe = np.linalg.norm(epe, axis=2)
    epe = np.min(epe, axis=1)

    epe_total = np.nanmean(epe)
    epe_errs = [np.nanmean(epe[i]) for i in maps_list]
    epe_errs = [epe_total] + epe_errs

    # Fl error
    gt_veclen_max = gt_veclen.max(axis=1)
    fl = (epe > 3) & (epe > 0.05 * gt_veclen_max)
    fl_total = 100 * fl.sum() / (~np.isnan(epe)).sum()
    fl_errs = [getboolmaperr(fl, i, epe) for i in maps_list]
    fl_errs = [fl_total] + fl_errs

    # 1px error
    onepx = epe > 1
    onepx_total = 100 * onepx.sum() / (~np.isnan(epe)).sum()
    onepx_errs = [getboolmaperr(onepx, i, epe) for i in maps_list]
    onepx_errs = [onepx_total] + onepx_errs

    # WAUC error (viper)
    wauc_total = getWAUC(epe)
    wauc_errs = [getWAUCmap(epe, i) for i in maps_list]
    wauc_errs = [wauc_total] + wauc_errs

    # get images
    flow_imgs = []
    epe_imgs = []

    for i in range(10):
        startidx = REDUCED_SIZE * (3960-10) + i * (1920*1080)
        endidx = startidx + 1920*1080
        flow = submission[startidx:endidx]
        flow = flow.reshape((1080, 1920, 2))
        flow = flow.astype(np.float32)
        epe_single = epe[startidx:endidx]
        epe_single = epe_single.reshape((1080, 1920))
        flow_imgs.append(flow_plot.colorplot_light(flow, auto_scale=False, max_scale=HERO_FRAMES_SCALING_FLOW[i]))
        epe_imgs.append(geterrorimage(epe_single))

    return (epe_errs, fl_errs, onepx_errs, wauc_errs), (flow_imgs, epe_imgs)


def evaluate_submission_flow(submission_file, img_outputdir):
    submission = flow_IO.readFlo5Flow(submission_file)
    gt_flow = flow_IO.readFlo5Flow(FILE_GT_FLOW)
    detailmap = flow_IO.readFlo5Flow(FILE_DETAILMAP_FLOW)
    rigidmap = flow_IO.readFlo5Flow(FILE_RIGIDMAP)
    skymap = flow_IO.readFlo5Flow(FILE_SKYMAP)
    matchmap = flow_IO.readFlo5Flow(FILE_MATCHMAP_FLOW)

    if np.isnan(submission).sum() != 0:
        raise ValueError("Submission contains nan values!")
    if submission.shape != (225500050, 2):
        raise ValueError("Submission has wrong shape!")

    errors, imgs = get_errors_flow(submission, gt_flow, detailmap, rigidmap, matchmap, skymap)
    print(errors)

    subnames = ["total", "lowdetail", "highdetail", "rigid", "nonrigid", "matched", "unmatched", "notsky", "sky", "s0_10", "s10_40", "s40"]
    errnames = ["EPE_Fl", "Fl", "1px_Fl", "WAUC_Fl"]

    errors_dict = {}
    for ename, err in zip(errnames, errors):
        errors_dict.update(dict(zip([f"err_{ename}_{i}" for i in subnames], err)))
    pprint(errors_dict)

    flimg, flerrimg = imgs
    os.makedirs(img_outputdir, exist_ok=True)
    for i in range(10):
        plt.imsave(os.path.join(img_outputdir, f"flimg_{i:02d}.png"), flimg[i])
        plt.imsave(os.path.join(img_outputdir, f"flerrimg_{i:02d}.png"), flerrimg[i], cmap="gray", vmin=0, vmax=1)
    
    return errors_dict


def get_disp1submission_index(seq, cam, fr):
    j = 0
    for seq_, count_ in test_seq:
        for cam_ in ["left", "right"]:
            for fr_ in range(1, count_+1):
                if (seq == seq_) and (cam == cam_) and (fr == fr_):
                    return j
                j += 1


def convertdisp1(submission):
    result = np.zeros(225500050, dtype=np.float16)
    result[:] = np.nan
    cases = []
    for seq, count in test_seq:
        for cam in ["left", "right"]:
            for fr in range(1, count):
                if (seq,"FW",cam,fr) not in HERO_FRAMES:
                    cases.append((seq, cam, "FW", fr))
            for fr in reversed(range(2, count+1)):
                if (seq,"BW",cam,fr) not in HERO_FRAMES:
                    cases.append((seq, cam, "BW", fr))
    for i, (seq, cam, dir, fr) in enumerate(cases):
        target_idx_start = i * REDUCED_SIZE
        target_idx_end = (i+1) * REDUCED_SIZE
        j = get_disp1submission_index(seq, cam, fr)
        src_idx_start = j * REDUCED_SIZE
        src_idx_end = (j+1) * REDUCED_SIZE
        assert (~np.isnan(result[target_idx_start:target_idx_end])).sum() == 0
        result[target_idx_start:target_idx_end] = submission[src_idx_start:src_idx_end]
    end_idx = 1920*1080*10
    result[-end_idx:] = submission[-end_idx:]
    return result


def get_errors_stereo(submission, gt_disp, detailmap, matchmap, skymap):
    with warnings.catch_warnings():
        # nanmean throws warning for all-nan slices, but this is expected so suppress this warning
        warnings.simplefilter("ignore", category=RuntimeWarning)
        gt_veclen_mean = np.nanmean(gt_disp, axis=-1)
    lenmap1 = gt_veclen_mean < 10
    lenmap2 = (gt_veclen_mean >= 10) & (gt_veclen_mean < 40)
    lenmap3 = gt_veclen_mean >= 40

    maps_list = [~detailmap, detailmap, ~skymap, skymap, ~matchmap, matchmap, lenmap1, lenmap2, lenmap3]

    epe = np.abs(gt_disp.astype(np.float32) - submission.astype(np.float32)[:,None])
    epe = np.min(epe, axis=-1)
    epe = epe.astype(np.float64)

    # 1px error
    onepx = epe > 1
    onepx_total = 100 * onepx.sum() / (~np.isnan(epe)).sum()
    onepx_errs = [getboolmaperr(onepx, i, epe) for i in maps_list]
    onepx_errs = [onepx_total] + onepx_errs

    # abs err:
    abs_total = np.nanmean(epe)
    abs_errs = [np.nanmean(epe[i]) for i in maps_list]
    abs_errs = [abs_total] + abs_errs

    # D1 err:
    gt_len = np.abs(gt_disp).max(axis=-1)
    d1 = (epe > 3) & (epe > 0.05 * gt_len)
    d1_total = 100 * d1.sum() / (~np.isnan(epe)).sum()
    d1_errs = [getboolmaperr(d1, i, epe) for i in maps_list]
    d1_errs = [d1_total] + d1_errs

    disp_imgs = []
    errimg = []
    for i in range(10):
        startidx = REDUCED_SIZE * (3960-10) + i * (1920*1080)
        endidx = startidx + 1920*1080
        disp = submission[startidx:endidx]
        disp = disp.reshape((1080, 1920))
        disp = disp.astype(np.float32)
        disp = np.clip(disp / HERO_FRAMES_SCALING_DISP[i], 0, 1)
        plasma = plt.cm.get_cmap("plasma")
        disp = plasma(disp)
        disp_imgs.append(disp)
        epe_single = epe[startidx:endidx]
        epe_single = epe_single.reshape((1080, 1920))
        errimg.append(geterrorimage(epe_single))

    return (onepx_errs, abs_errs, d1_errs), (disp_imgs, errimg)


def evaluate_submission_disp1(submission_file, img_outputdir):
    submission = flow_IO.readDsp5Disp(submission_file)

    if np.isnan(submission).sum() != 0:
        raise ValueError("Submission contains nan values!")
    if submission.shape != (124414000,):
        raise ValueError("Submission has wrong shape!")

    submission = convertdisp1(submission)

    gt_disp1 = flow_IO.readFlo5Flow(FILE_GT_DISP1)
    detailmap = flow_IO.readFlo5Flow(FILE_DETAILMAP_DISP1)
    skymap = flow_IO.readFlo5Flow(FILE_SKYMAP)
    matchmap = flow_IO.readFlo5Flow(FILE_MATCHMAP_DISP1)
    errors, imgs = get_errors_stereo(submission, gt_disp1, detailmap, matchmap, skymap)

    subnames = ["total", "lowdetail", "highdetail", "notsky", "sky", "matched", "unmatched", "s0_10", "s10_40", "s40"]
    errnames = ["1px_D1", "Abs_D1", "D1"]

    errors_dict = {}
    for ename, err in zip(errnames, errors):
        errors_dict.update(dict(zip([f"err_{ename}_{i}" for i in subnames], err)))
    pprint(errors_dict)

    d1img, d1errimg = imgs
    os.makedirs(img_outputdir, exist_ok=True)
    for i in range(10):
        plt.imsave(os.path.join(img_outputdir, f"d1img_{i:02d}.png"), d1img[i])
        plt.imsave(os.path.join(img_outputdir, f"d1errimg_{i:02d}.png"), d1errimg[i], cmap="gray", vmin=0, vmax=1)
    return errors_dict


def get_errors_sceneflow(d1_submission, d2_submission, fl_submission, gt_d1, gt_d2, gt_flow, detmap_sf, matmap_sf, rigidmap, skymap):

    d1_epe = np.abs(gt_d1.astype(np.float32) - d1_submission.astype(np.float32)[:,None])
    d1_epe = np.min(d1_epe, axis=-1)
    d1_epe = d1_epe.astype(np.float64)

    d2_epe = np.abs(gt_d2.astype(np.float32) - d2_submission.astype(np.float32)[:,None])
    d2_epe = np.min(d2_epe, axis=-1)
    d2_epe = d2_epe.astype(np.float64)

    fl_epe = gt_flow - fl_submission[:,None,:]
    fl_epe = fl_epe.astype(np.float64)
    fl_epe = np.linalg.norm(fl_epe, axis=2)
    fl_epe = np.min(fl_epe, axis=1)

    # D1
    gt_len = np.abs(gt_d1).max(axis=-1)
    d1 = (d1_epe > 3) & (d1_epe > 0.05 * gt_len)

    # D2
    gt_len = np.abs(gt_d2).max(axis=-1)
    d2 = (d2_epe > 3) & (d2_epe > 0.05 * gt_len)

    # Fl error
    gt_veclen = np.linalg.norm(gt_flow.astype(np.float64), axis=-1)
    gt_veclen_max = gt_veclen.max(axis=1)
    fl = (fl_epe > 3) & (fl_epe > 0.05 * gt_veclen_max)

    with warnings.catch_warnings():
        # nanmean throws warning for all-nan slices, but this is expected so suppress this warning
        warnings.simplefilter("ignore", category=RuntimeWarning)
        d1_gt_len_mean = np.nanmean(np.abs(gt_d1), axis=-1)
        d2_gt_len_mean = np.nanmean(np.abs(gt_d2), axis=-1)
        fl_gt_veclen_mean = np.nanmean(gt_veclen, axis=1)

    lenmap3 = (d1_gt_len_mean > 40) | (d2_gt_len_mean > 40) | (fl_gt_veclen_mean > 40)
    lenmap2 = (d1_gt_len_mean > 10) | (d2_gt_len_mean > 10) | (fl_gt_veclen_mean > 10)
    lenmap2 = lenmap2 & (~lenmap3)
    lenmap1 = (~lenmap2) & (~lenmap3)

    maps_list = [~detmap_sf, detmap_sf, ~rigidmap, rigidmap, ~matmap_sf, matmap_sf, ~skymap, skymap, lenmap1, lenmap2, lenmap3]

    sf = d1 | d2 | fl
    sf_epe = d1_epe + d2_epe + fl_epe
    sf_total = 100 * sf.sum() / (~np.isnan(sf_epe)).sum()
    sf_errs = [getboolmaperr(sf, i, sf_epe) for i in maps_list]
    sf_errs = [sf_total] + sf_errs


    onepx_d1 = d1_epe > 1
    onepx_d2 = d2_epe > 1
    onepx_fl = fl_epe > 1
    onepx_sf = onepx_d1 | onepx_d2 | onepx_fl
    onepx_total = 100 * onepx_sf.sum() / (~np.isnan(sf_epe)).sum()
    onepx_errs = [getboolmaperr(onepx_sf, i, sf_epe) for i in maps_list]
    onepx_errs = [onepx_total] + onepx_errs

    # get images
    epe_imgs = []
    for i in range(10):
        startidx = REDUCED_SIZE * (3960-10) + i * (1920*1080)
        endidx = startidx + 1920*1080
        epe_single = np.maximum(np.maximum(d1_epe[startidx:endidx], d2_epe[startidx:endidx]), fl_epe[startidx:endidx])
        epe_single = epe_single.reshape((1080, 1920))
        epe_imgs.append(geterrorimage(epe_single))

    return (sf_errs, onepx_errs), epe_imgs


def evaluate_submission_sceneflow(d1_file, d2_file, fl_file, img_outputdir):
    d1_submission = flow_IO.readDsp5Disp(d1_file)
    d2_submission = flow_IO.readDsp5Disp(d2_file)
    fl_submission = flow_IO.readFlo5Flow(fl_file)

    if ((~np.isfinite(d1_submission)).sum() != 0) or ((~np.isfinite(d2_submission)).sum() != 0) or ((~np.isfinite(fl_submission)).sum() != 0):
        #raise ValueError("Submission contains nan or inf values!")
        print("Submission contains nan or inf values!\nreplacing for now....")
        np.nan_to_num(d1_submission, copy=False)
        np.nan_to_num(d2_submission, copy=False)
        np.nan_to_num(fl_submission, copy=False)
    if d1_submission.shape != (124414000,):
        raise ValueError("D1 submission has wrong shape!")
    if d2_submission.shape != (225500050,):
        raise ValueError("D2 submission has wrong shape!")
    if fl_submission.shape != (225500050, 2):
        raise ValueError("Flow submission has wrong shape!")

    d1_submission = convertdisp1(d1_submission)

    print(d1_submission.shape)

    gt_disp1 = flow_IO.readFlo5Flow(FILE_GT_DISP1)
    gt_disp2 = flow_IO.readFlo5Flow(FILE_GT_DISP2)
    gt_flow = flow_IO.readFlo5Flow(FILE_GT_FLOW)
    detailmap_disp1 = flow_IO.readFlo5Flow(FILE_DETAILMAP_DISP1)
    detailmap_disp2 = flow_IO.readFlo5Flow(FILE_DETAILMAP_DISP2)
    detailmap_flow = flow_IO.readFlo5Flow(FILE_DETAILMAP_FLOW)
    matchmap_disp1 = flow_IO.readFlo5Flow(FILE_MATCHMAP_DISP1)
    matchmap_disp2 = flow_IO.readFlo5Flow(FILE_MATCHMAP_DISP2)
    matchmap_flow = flow_IO.readFlo5Flow(FILE_MATCHMAP_FLOW)
    rigidmap = flow_IO.readFlo5Flow(FILE_RIGIDMAP)
    skymap = flow_IO.readFlo5Flow(FILE_SKYMAP)

    errors_d1, imgs_d1 = get_errors_stereo(d1_submission, gt_disp1, detailmap_disp1, matchmap_disp1, skymap)
    print(errors_d1)
    errors_d2, imgs_d2 = get_errors_stereo(d2_submission, gt_disp2, detailmap_disp2, matchmap_disp2, skymap)
    print(errors_d2)
    errors_fl, imgs_fl = get_errors_flow(fl_submission, gt_flow, detailmap_flow, rigidmap, matchmap_flow, skymap)
    print(errors_fl)

    detmap_sf = detailmap_disp1 | detailmap_disp2 | detailmap_flow
    matmap_sf = matchmap_disp1 | matchmap_disp2 | matchmap_flow

    errors_sf, imgs_sf = get_errors_sceneflow(d1_submission, d2_submission, fl_submission, gt_disp1, gt_disp2, gt_flow, detmap_sf, matmap_sf, rigidmap, skymap)
    print(errors_sf)

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

    return errors_dict
