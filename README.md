# Custom-BCI-Experiment-Generator

This repository contains two components for creating highly customizable and ready-to-use experiment paradigms for conducting body scanning:

1. Hands Template Generation: This component allows you to generate hand templates for your experiments. To create hand templates, follow these steps:
    - Navigate to the `hands` directory.
    - Run the `hands-generator.py` script using the following command:
      ```
      python3 hands-generator.py --exp_name <experiment_name> --list_of_lists "<list_of_lists>" --si <si> --seq "<seq>"
      ```
      Replace `<experiment_name>` with the desired name for your experiment, `<list_of_lists>` with a list of contour indices to make images,`<si>` with stimulus presentation interval, and `<seq>` with the desired sequence of the stimulus. For example:
      ```
      python3 hands-generator.py --exp_name left_right_palms --list_of_lists "[[5, 1, 7, 9, 3], [6, 0, 8, 4, 2]]" --seq "1,0"
      ```

      ![Hands Indices](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/hand-contours-labels.png)

    - The hand templates (images and Gif) will be generated in a new folder with the specified name. These templates can be used as visual stimuli for your experiments.

      ![Demo Gif](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/hands/SingleFinger/SingleFinger%5B1%2C%206%2C%209%2C%207%2C%204%2C%205%2C%207%2C%202%2C%209%2C%200%5D.gif)


2. Body Annotation Interface: This component allows you to create body annotations for your experiments. To create body annotations, follow these steps:
    - Navigate to the `body` directory.
    - Run `python3 freehand_annotation_interface.py`.
    - Utilize the functions provided in the interface to create your custom experiments.

    ![Demo Interface](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/demo-interface.gif)

    - Click **Submit** to generate the animation.
    - Scroll to find your desired interval for stimulus presentation and click the Save GIF button 

    ![Demo Animation](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/demo-animation.gif)

    - To generate a variation of the path, click on the **More Experiments** button in the pop-up window. Currently this feature only considers the proximity and number of annotated overlays as the significance value. More options will be added in the future.

    ![Demo Interpolation](https://github.com/Cheersbbg/Custom-BCI-Experiment-Generator/blob/main/demo-interpolation.gif)


This repository is actively being updated with new features, functionalities and intergrations with ML.

If you have any questions, really any, feel free to contact me at cheersbbg [at] gmail [dot] com