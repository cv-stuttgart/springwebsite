#include <highfive/H5File.hpp>
#include <highfive/H5DataSet.hpp>
#include <highfive/H5DataSpace.hpp>
#include <iostream>


// true random numbers are withheld; list of random numbers whose mean is exactly 40.
std::vector<int> random_numbers = {40, 40, 40};

int REDUCED_SIZE = 51840 - 1;

std::vector<int> SEQUENCES = {3, 19, 28, 29, 31, 34, 35, 40, 42, 46};
std::vector<int> SEQ_LENGTH = {131, 111, 39, 135, 73, 47, 120, 111, 116, 117};

std::vector<std::string> CAMS = {"left", "right"};

std::vector<std::string> HERO_FRAMES =
    {
        "0003/disp2_FW_left/disp2_FW_left_0017",
        "0019/disp2_FW_left/disp2_FW_left_0055",
        "0028/disp2_FW_left/disp2_FW_left_0018",
        "0029/disp2_FW_left/disp2_FW_left_0068",
        "0031/disp2_FW_left/disp2_FW_left_0032",
        "0034/disp2_FW_left/disp2_FW_left_0024",
        "0035/disp2_FW_left/disp2_FW_left_0089",
        "0040/disp2_FW_left/disp2_FW_left_0055",
        "0042/disp2_FW_left/disp2_FW_left_0060",
        "0046/disp2_FW_left/disp2_FW_left_0047"};

std::vector<std::vector<float>> readDisp(std::string filepath)
{
    HighFive::File file(filepath, HighFive::File::ReadOnly);

    std::vector<std::vector<float>> data;
    HighFive::DataSet dataset = file.getDataSet("disparity");
    dataset.read(data);
    return data;
}

int main(int argc, char *argv[])
{

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

    std::vector<HighFive::float16_t> final_data;

    for (int seq_idx = 0; seq_idx < SEQUENCES.size(); seq_idx++)
    {
        int sequence = SEQUENCES[seq_idx];
        for (auto &&cam : CAMS)
        {
            std::vector<int> frames;
            for (int frame = 1; frame < SEQ_LENGTH[seq_idx]; frame++)
                frames.push_back(frame);

            for (int frame = SEQ_LENGTH[seq_idx]; frame >= 2; frame--)
                frames.push_back(frame);

            for (int fr_idx = 0; fr_idx < frames.size(); fr_idx++)
            {
                std::string direction;
                if (fr_idx < SEQ_LENGTH[seq_idx] - 1)
                    direction = "FW";
                else
                    direction = "BW";

                int frame = frames[fr_idx];

                char filepath_c[512];
                std::snprintf(filepath_c, 512, "%04d/disp2_%s_%s/disp2_%s_%s_%04d", sequence, direction.c_str(), cam.c_str(), direction.c_str(), cam.c_str(), frame);
                bool skip_frame = false;
                for (auto &&hero : HERO_FRAMES)
                {
                    if (filepath_c == hero)
                    {
                        skip_frame = true;
                        break;
                    }
                }
                if (skip_frame)
                {
                    continue;
                }

                std::string filepath(filepath_c);
                filepath = basepath + "/" + filepath + ".dsp5";
                std::cout << filepath << std::endl;

                int startsize = final_data.size();
                std::vector<std::vector<float>> disp = readDisp(filepath);

                int start_idx = (frame * sequence) % random_numbers.size();
                int target_idx = random_numbers[start_idx];

                while (final_data.size() - startsize < REDUCED_SIZE)
                {
                    int target_idx_h = div(target_idx, disp[0].size()).quot;
                    int target_idx_w = div(target_idx, disp[0].size()).rem;

                    final_data.push_back(HighFive::float16_t(disp[target_idx_h][target_idx_w]));

                    start_idx += 1;
                    start_idx = start_idx % random_numbers.size();
                    target_idx += random_numbers[start_idx];
                }
            }
        }
    }

    std::cout << final_data.size() << std::endl;

    for (auto &&hero : HERO_FRAMES)
    {
        std::string filepath;
        filepath = basepath + "/" + hero + ".dsp5";
        std::cout << filepath << std::endl;

        std::vector<std::vector<float>> disp = readDisp(filepath);

        for (int i = 0; i < disp.size(); i++)
        {
            for (int j = 0; j < disp[0].size(); j++)
            {
                final_data.push_back(HighFive::float16_t(disp[i][j]));
            }
        }
    }

    std::cout << final_data.size() << std::endl;

    HighFive::DataSetCreateProps props;
    props.add(HighFive::Chunking{final_data.size()});
    props.add(HighFive::Deflate(9));

    HighFive::File file("./disp2_submission.hdf5", HighFive::File::ReadWrite | HighFive::File::Create | HighFive::File::Truncate);
    HighFive::DataSet dataset = file.createDataSet<HighFive::float16_t>("/disparity", HighFive::DataSpace::From(final_data), props);
    dataset.write(final_data);
}
