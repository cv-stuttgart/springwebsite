import os
import numpy as np
from PIL import Image
import h5py


test_seq = [(3, 131), (19, 111), (28, 39), (29, 135), (31, 73), (34, 47), (35, 120), (40, 111), (42, 116), (46, 117)]

# true random numbers are withheld; list of random numbers whose mean is exactly 40.
RANDOM_NUMBERS = [40, 40, 40]
REDUCED_SIZE = 51840 - 1

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


BASEPATH = os.environ["SPRING_TESTPATH"]


def readDsp5Disp(filename):
    with h5py.File(filename, "r") as f:
        if "disparity" not in f.keys():
            raise IOError(f"File {filename} does not have a 'disparity' key. Is this a valid dsp5 file?")
        return f["disparity"][()]


def writeFlo5File(flow, filename):
    with h5py.File(filename, "w") as f:
        f.create_dataset("flow", data=flow, compression="gzip", compression_opts=5)


def readFlo5Flow(filename):
    with h5py.File(filename, "r") as f:
        if "flow" not in f.keys():
            raise IOError(f"File {filename} does not have a 'flow' key. Is this a valid flo5 file?")
        return f["flow"][()]


def disp1file(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}/disp1_{cam}/disp1_{cam}_{fr:04d}.dsp5")
    print(filepath)
    return readDsp5Disp(filepath).astype(np.float16)


def flowfile(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}/flow_{dir}_{cam}/flow_{dir}_{cam}_{fr:04d}.flo5")
    print(filepath)
    return readFlo5Flow(filepath).astype(np.float16)


def disp2file(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}/disp2_{dir}_{cam}/disp2_{dir}_{cam}_{fr:04d}.dsp5")
    print(filepath)
    return readDsp5Disp(filepath).astype(np.float16)


def detailmapdisp1file(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"detailmap_disp1_{cam}/detailmap_disp1_{cam}_{fr:04d}.png")
    print(filepath)
    return np.asarray(Image.open(filepath)) > 0


def detailmapflowfile(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"detailmap_flow_{dir}_{cam}/detailmap_flow_{dir}_{cam}_{fr:04d}.png")
    print(filepath)
    return np.asarray(Image.open(filepath)) > 0


def detailmapdisp2file(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"detailmap_disp2_{dir}_{cam}/detailmap_disp2_{dir}_{cam}_{fr:04d}.png")
    print(filepath)
    return np.asarray(Image.open(filepath)) > 0


def rigidmapfile(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"rigidmap_{dir}_{cam}/rigidmap_{dir}_{cam}_{fr:04d}.png")
    print(filepath)
    map = np.asarray(Image.open(filepath))
    # half resolution
    map = np.dstack((map[::2,::2], map[::2,1::2], map[1::2,::2], map[1::2,1::2]))
    return map.astype(np.float32).mean(axis=-1) >= 0.5


def skymapfile(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"skymap_{cam}/skymap_{cam}_{fr:04d}.png")
    print(filepath)
    map = np.asarray(Image.open(filepath))
    # half resolution
    map = np.dstack((map[::2,::2], map[::2,1::2], map[1::2,::2], map[1::2,1::2]))
    return map.astype(np.float32).mean(axis=-1) >= 0.5


def matchmapdisp1file(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"matchmap_disp1_{cam}/matchmap_disp1_{cam}_{fr:04d}.png")
    print(filepath)
    map = np.asarray(Image.open(filepath))
    map = (map[...,0] > 0) | (map[...,1] > 0)
    return map


def matchmapflowfile(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"matchmap_flow_{dir}_{cam}/matchmap_flow_{dir}_{cam}_{fr:04d}.png")
    print(filepath)
    map = np.asarray(Image.open(filepath))
    map = (map[...,0] > 0) | (map[...,1] > 0)
    return map


def matchmapdisp2file(seq, dir, cam, fr):
    filepath = os.path.join(BASEPATH, f"{seq:04d}", "maps", f"matchmap_disp2_{dir}_{cam}/matchmap_disp2_{dir}_{cam}_{fr:04d}.png")
    print(filepath)
    map = np.asarray(Image.open(filepath))
    map = (map[...,0] > 0) | (map[...,1] > 0)
    return map


def createTestfile(read_fn, outname, is_doublesize=False):
    cases = []
    for seq, count in test_seq:
        for cam in ["left", "right"]:
            for fr in range(1, count):
                cases.append((seq, cam, "FW", fr))
            for fr in reversed(range(2, count+1)):
                cases.append((seq, cam, "BW", fr))

    width = 1920
    height = 1080

    final_data = []
    for seq, cam, dir, fr in cases:
        if (seq,dir,cam,fr) in HERO_FRAMES:
            continue

        inputdata = read_fn(seq, dir, cam, fr)

        startsize = len(final_data)
        start_idx = (fr*seq) % len(RANDOM_NUMBERS)
        target_idx = RANDOM_NUMBERS[start_idx]

        while (len(final_data) - startsize) < REDUCED_SIZE:
            target_idx_h = target_idx // width
            target_idx_w = target_idx % width
            if is_doublesize:
                datapoint = [inputdata[2*target_idx_h, 2*target_idx_w], inputdata[2*target_idx_h+1, 2*target_idx_w], inputdata[2*target_idx_h, 2*target_idx_w+1], inputdata[2*target_idx_h+1, 2*target_idx_w+1]]
            else:
                datapoint = inputdata[target_idx_h, target_idx_w]
            final_data.append(np.asarray(datapoint))

            start_idx += 1
            start_idx = start_idx % len(RANDOM_NUMBERS)
            target_idx += RANDOM_NUMBERS[start_idx]
        del inputdata

    print(len(final_data))

    for seq, dir, cam, fr in HERO_FRAMES:
        inputdata = read_fn(seq, dir, cam, fr)

        for i in range(height):
            for j in range(width):
                if is_doublesize:
                    datapoint = [inputdata[2*i, 2*j], inputdata[2*i+1, 2*j], inputdata[2*i, 2*j+1], inputdata[2*i+1, 2*j+1]]
                else:
                    datapoint = inputdata[i, j]
                final_data.append(np.asarray(datapoint))

    print(len(final_data))
    final_data = np.asarray(final_data)

    writeFlo5File(final_data, outname)


if __name__ == "__main__":
    createTestfile(flowfile, "eval_flow.hdf5", is_doublesize=True)
    createTestfile(detailmapflowfile, "eval_detailmap_flow.hdf5", is_doublesize=False)
    createTestfile(rigidmapfile, "eval_rigidmap.hdf5", is_doublesize=False)
    createTestfile(skymapfile, "eval_skymap.hdf5", is_doublesize=False)
    createTestfile(matchmapflowfile, "eval_matchmap_flow.hdf5", is_doublesize=False)

    createTestfile(disp2file, "eval_disp2.hdf5", is_doublesize=True)
    createTestfile(detailmapdisp2file, "eval_detailmap_disp2.hdf5", is_doublesize=False)
    createTestfile(matchmapdisp2file, "eval_matchmap_disp2.hdf5", is_doublesize=False)

    createTestfile(disp1file, "eval_disp1.hdf5", is_doublesize=True)
    createTestfile(detailmapdisp1file, "eval_detailmap_disp1.hdf5", is_doublesize=False)
    createTestfile(matchmapdisp1file, "eval_matchmap_disp1.hdf5", is_doublesize=False)
