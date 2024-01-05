# Custom-BCI-Experiment-Generator
This repo contains two components that creates completely customizable and out-of-the-box experiment paradigms for conducting body scanning: 

Hands Template Generation and Body Annotation Interface

More specific manual and a docker will be updated soon:)
---
To create hand templates, follow these steps:

![Hands Indices](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/hand-contours-labels.png)

1. Navigate to the `hands` directory.
2. Run the `hands-generator.py` script with the following command:
    ```
    python3 hands-generator.py --exp_name <experiment_name> --list_of_lists "<list_of_lists>"
    ```
    Replace `<experiment_name>` with the desired name for your experiment and `<list_of_lists>` with a list of contour indices. For example:
    ```
    python3 hands-generator.py --exp_name left_right_palms --list_of_lists "[[5, 1, 7, 9, 3], [6, 0, 8, 4, 2]]"
    ```
3. The hand templates will be generated in a new folder with the specified name. These templates can be used as visual stimuli for your experiments.

To create body annotations, follow these steps:

1. nagivate to body directory 
2. run `python3 freehand_annotation_interface.py`

![Experiments Demo](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/demo.gif)

More detailed instructions and a Docker setup will be provided soon.
