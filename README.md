# Custom-BCI-Experiment-Generator

This repository contains two components for creating highly customizable and ready-to-use experiment paradigms for conducting body scanning:

1. Hands Template Generation: This component allows you to generate hand templates for your experiments. To create hand templates, follow these steps:
    - Navigate to the `hands` directory.
    - Run the `hands-generator.py` script using the following command:
      ```
      python3 hands-generator.py --exp_name <experiment_name> --list_of_lists "<list_of_lists>"
      ```
      Replace `<experiment_name>` with the desired name for your experiment and `<list_of_lists>` with a list of contour indices.
      
      ![Hands Indices](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/hand-contours-labels.png)

    - The hand templates will be generated in a new folder with the specified name. These templates can be used as visual stimuli for your experiments.

2. Body Annotation Interface: This component allows you to create body annotations for your experiments. To create body annotations, follow these steps:
    - Navigate to the `body` directory.
    - Run `python3 freehand_annotation_interface.py`.
    - Utilize the functions provided in the interface to create your custom experiments.

    ![Demo Interface](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/demo-interface.gif)

    - Click the Submit button to generate the animation.
    - Scroll to find your desired interval for stimulus presentation and click the Save GIF button 

    ![Demo Animation](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/demo-animation.gif)


This repository is actively being updated with new features and functionalities. For the latest detailed instructions, a Docker setup, applications and more, please keep an eye on future updates of this repo:)

