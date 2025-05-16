#include <highfive/H5File.hpp>
#include <highfive/H5DataSet.hpp>
#include <highfive/H5DataSpace.hpp>
#include <highfive/H5Group.hpp>
#include <iostream>
#include <instr.h>
#include <vector>
#include <string>
#include <cstdio>
#include <cstdlib>

int REDUCED_SIZE = 51840 - 1;

std::vector<int> SEQUENCES = {3, 19, 28, 29, 31, 34, 35, 40, 42, 46};
std::vector<int> SEQ_LENGTH = {131, 111, 39, 135, 73, 47, 120, 111, 116, 117};
std::vector<std::string> CAMS = {"left", "right"};

std::vector<std::vector<std::vector<float>>> readFlow(std::string filepath)
{
    HighFive::File file(filepath, HighFive::File::ReadOnly);
    std::vector<std::vector<std::vector<float>>> data;
    HighFive::DataSet dataset = file.getDataSet("flow");
    dataset.read(data);
    return data;
}

int main(int argc, char *argv[])
{
    OBF_BEGIN

    // true random numbers are withheld; list of random numbers whose mean is exactly 40.
    std::vector<int> random_numbers = {40, 40, 40};

    if (argc != 2)
    {
        std::cout << "Provide base path as the first and only argument." << std::endl;
        return 100;
    }

    std::string basepath = argv[1];
    if (basepath.back() == '/')
    {
        basepath.pop_back();
    }

    std::vector<std::string> folders = {
        "clean",
        "brightness",
        "contrast",
        "defocus_blur",
        "elastic_transform",
        "fog",
        "frost",
        "gaussian_blur",
        "gaussian_noise",
        "glass_blur",
        "impulse_noise",
        "jpeg_compression",
        "motion_blur",
        "pixelate",
        "rain",
        "saturate",
        "shot_noise",
        "snow",
        "spatter",
        "speckle_noise",
        "zoom_blur"
    };

    HighFive::File file_final("./flow_robustness.hdf5", HighFive::File::ReadWrite | HighFive::File::Create | HighFive::File::Truncate);

    for (const auto &folder : folders)
    {
        std::vector<std::vector<HighFive::float16_t>> final_data;

        for (size_t seq_idx = 0; seq_idx < SEQUENCES.size(); seq_idx++)
        {
            int sequence = SEQUENCES[seq_idx];
            for (auto &cam : CAMS)
            {
                std::vector<int> frames;
                for (int frame = 1; frame < SEQ_LENGTH[seq_idx]; frame++)
                    frames.push_back(frame);
                for (int frame = SEQ_LENGTH[seq_idx]; frame >= 2; frame--)
                    frames.push_back(frame);

                for (size_t fr_idx = 0; fr_idx < frames.size(); fr_idx++)
                {
                    std::string direction = (fr_idx < SEQ_LENGTH[seq_idx] - 1) ? "FW" : "BW";
                    int frame = frames[fr_idx];

                    char filepath_c[512];
                    std::snprintf(filepath_c, 512, "%04d/flow_%s_%s/flow_%s_%s_%04d", sequence, direction.c_str(), cam.c_str(), direction.c_str(), cam.c_str(), frame);
                    std::string filepath(filepath_c);
                    filepath = basepath + "/" + folder + "/test/" + filepath + ".flo5";
                    std::cout << filepath << std::endl;

                    int startsize = final_data.size();
                    std::vector<std::vector<std::vector<float>>> flow = readFlow(filepath);

                    int start_idx = (frame * sequence) % random_numbers.size();
                    int target_idx = random_numbers[start_idx];

                    while (final_data.size() - startsize < REDUCED_SIZE)
                    {
                        int target_idx_h = div(target_idx, flow[0].size()).quot;
                        int target_idx_w = div(target_idx, flow[0].size()).rem;
                        final_data.push_back({HighFive::float16_t(flow[target_idx_h][target_idx_w][0]),
                                               HighFive::float16_t(flow[target_idx_h][target_idx_w][1])});
                        start_idx += 1;
                        start_idx = start_idx % random_numbers.size();
                        target_idx += random_numbers[start_idx];
                    }
                }
            }
        }

        std::vector<std::vector<HighFive::float16_t>> second_subsampled_data;
        size_t second_subsample_size = static_cast<size_t>(0.05 * final_data.size());
        size_t total_elements = final_data.size();
        size_t stride = total_elements / second_subsample_size;
        for (size_t i = 0; i < total_elements && second_subsampled_data.size() < second_subsample_size; i += stride)
        {
            second_subsampled_data.push_back(final_data[i]);
        }

        HighFive::Group group = file_final.createGroup("/" + folder);

        HighFive::DataSetCreateProps second_props;
        second_props.add(HighFive::Chunking{second_subsampled_data.size(), 2});
        second_props.add(HighFive::Deflate(9));
        HighFive::DataSet dataset_second = group.createDataSet<HighFive::float16_t>("flow",
                                                                                    HighFive::DataSpace::From(second_subsampled_data),
                                                                                    second_props);
        dataset_second.write(second_subsampled_data);

        std::cout << "Folder " << folder << " subsampled size: " << second_subsampled_data.size() << std::endl;
    }

    OBF_END
    return 0;
}
