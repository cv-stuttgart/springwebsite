
# Spring Benchmark Website

This repository contains the code to for the Spring benchmark website, see https://spring-benchmark.org/.

For details on the subsampling strategy see [subfolder](subsampling/README.md).

## Quick Setup

- Install required python packages: Django, pprint, numpy, matplotlib, pypng, h5py
- define the following environment variables:
    - `SPRING_ALLOWEDHOSTS`: Comma-separated list of allowed hosts for the django server, see [details](https://docs.djangoproject.com/en/4.1/ref/settings/#allowed-hosts).
    - `SPRING_TIMEZONE`: Set the local time zone, see [details](https://docs.djangoproject.com/en/4.1/ref/settings/#time-zone).
    - `SPRING_UPLOADDIR`: directory, where the uploaded submission files are stored
- initiate the database: `python manage.py migrate`
- start website server: `python manage.py runserver`
- optionally: `python manage.py create_random <num>`; create `<num>` entries with random numbers


## Evaluation
The evaluation code can be found in `springeval/management/commands/update_evaluation.py` and `springeval/management/commands/evaluation.py`.

In order to enable evaluation, two environment variables have to be set:
- `SPRING_IMGDIR` is the media directory, the location where result visualizations are stored.
- `SPRING_EVALDIR` is the location of the non-public ground truth files needed for evaluation.
Then, the evaluation of submitted files is triggered via `python manage.py update_evaluation`.

## Deployment
- the django webserver has to be properly deployed, see [details](https://docs.djangoproject.com/en/4.1/howto/deployment/)
- the evaluation script has to be executed regularly, e.g. via cron
- a mail server has to be set up and configured, see [details](https://docs.djangoproject.com/en/4.1/topics/email/).


## Further environment variables:
- SPRING_EMAILUSER, SPRING_EMAILPASSWORD, SPRING_EMAILHOST, SPRING_FROMEMAIL: see [email settings](https://docs.djangoproject.com/en/4.1/topics/email/)
- SPRING_DEBUG: whether to use Django debug mode
- SPRING_SECRETKEY: Django secret key.
- SPRING_STATICROOT: The directory for static files, needed for deployment.

## Citation
If you make use of this code, please cite our paper:
```bibtex
@InProceedings{Mehl2023_Spring,
    author    = {Lukas Mehl and Jenny Schmalfuss and Azin Jahedi and Yaroslava Nalivayko and Andr\'es Bruhn},
    title     = {Spring: A High-Resolution High-Detail Dataset and Benchmark for Scene Flow, Optical Flow and Stereo},
    booktitle = {Proc. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
    year      = {2023}
}
```
