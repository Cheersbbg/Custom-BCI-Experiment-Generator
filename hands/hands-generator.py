import os
import pickle
import cv2
import numpy as np
from PIL import Image, ImageChops
import argparse
import imageio

def custom_experiment(list_of_lists, reset, exp_paradigm, is_white=True,stimulus_interval=1):
    """
    Creates experiment and map images based on given contours.

    Args:
    list_of_lists: List of lists containing contour indices.
    reset: Boolean to control background reset for each image.
    exp_name: Name of the new experiment.
    is_white: Boolean to choose the background color.

    Returns:
    Tuple containing paths to the experiment and map directories.
    """
    contours = np.load('handcountours.npy', allow_pickle=True)
    template = cv2.imread('blackhand.png' if is_white else 'whitehand.png')
    inv_img = ImageChops.invert(Image.fromarray(template)).convert("RGBA")

    exp_dir = os.path.join(os.getcwd(), exp_paradigm)
    print("Experiment Directory:", exp_dir)
    exp_path = os.path.join(exp_dir, "exp")
    map_path = os.path.join(exp_dir, "map")

    os.makedirs(exp_path, exist_ok=True)
    os.makedirs(map_path, exist_ok=True)

    images = []  # List to store the images for creating the GIF

    for key, contour_list in enumerate(list_of_lists):
        background = np.zeros((600, 800)) if not reset else background.copy()
        for contour in contour_list:
            cv2.drawContours(background, [contours[contour]], 0, color=(255, 255, 255), thickness=-1)

        map_image_path = os.path.join(map_path, f'image{key}.png')
        exp_image_path = os.path.join(exp_path, f'image{key}.png')

        Image.fromarray(background).convert("L").save(map_image_path)
        blend_and_save_images(map_image_path, inv_img, exp_image_path)

        # Append the image to the list
        images.append(imageio.v2.imread(exp_image_path))
    return exp_path, map_path


def create_gifs(exp_path, Sequencelst, stimulus_interval, exp_name, save_path="", nodelist=[]):
    """
    Creates GIFs from the experiment images.

    Args:
    exp_path: Path to the experiment images.
    ListofLists: List of lists containing contour indices.
    stimulus_interval: Interval between stimuli.
    """
    images = []
    for idx, num in enumerate(Sequencelst):
        exp_image_path = os.path.join(exp_path, f'image{num}.png')
        if nodelist[idx] != None:
            node_image_path = os.path.join(exp_path, f'image{nodelist[idx]}.png')
            node_image = Image.open(node_image_path)
            exp_image = Image.open(exp_image_path)
            blend_image = Image.blend(exp_image, node_image, alpha=0.5)
            merged_image = imageio.core.asarray(blend_image)
            images.append(merged_image)
        else:
            images.append(imageio.v2.imread(exp_image_path))
    if save_path == "":
        exp_dir = exp_path.rsplit('exp', 1)[0]
        print("exp_dir", exp_dir)
    else:
        exp_dir = save_path
        os.makedirs(exp_dir, exist_ok=True)
    # Save the list of images as a GIF with the given interval
    #add one to keep consistence with the actual label where there's no 0
    Sequencelst = [i+1 for i in Sequencelst]
    gif_path = os.path.join(exp_dir, f'{exp_name+str(Sequencelst)}.gif')
    imageio.mimsave(gif_path, images, duration=stimulus_interval, loop=0)  # Change the duration as per your requirement
    return gif_path
   

def blend_and_save_images(map_image_path, inv_img, exp_image_path):
    """
    Blends the map image with the inverted template and saves the result.

    Args:
    map_image_path: Path to the map image.
    inv_img: Inverted image of the template.
    exp_image_path: Path to save the blended experiment image.
    """
    temp = cv2.imread(map_image_path)
    b, g, r = cv2.split(temp)
    after = cv2.merge([b * 2, g * 0, r * 2])
    after = ImageChops.invert(Image.fromarray(after)).convert("RGBA")
    alpha_blended = Image.blend(after, inv_img, alpha=0.6)
    alpha_blended.save(exp_image_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Custom BCI Experiment Generator")
    parser.add_argument("--exp_paradigm", nargs='?',type=str, help="Name of the new experiment", default="SingleFinger")
    parser.add_argument("--exp_name", type=str, help="Name of the new experiment", default="exp_name")
    parser.add_argument("--list_of_lists", type=str, help="List of lists containing contour indices", default="[[35, 25, 11], [19, 31, 21], [15, 17, 13], [27, 29, 23], [37, 39, 33], [36, 38, 32], [26, 28, 22], [14, 16, 12], [18, 30, 20], [34, 24, 10]]")
    parser.add_argument("--si", type=int, help="Interval between stimuli in ms", default=400)
    parser.add_argument("--seq", type=str, help="Sequencing passing a string for list index", default=[])
    parser.add_argument("--save_path",nargs='?', type=str, help="Path to save the experiment", default="")
    parser.add_argument("--node_index_list", type=str, help="List of node indices", default=[])

    args = parser.parse_args()
    EXP_PARADIGM = args.exp_paradigm
    EXP_NAME = args.exp_name
    LIST_OF_LISTS = eval(args.list_of_lists)
    
    print("Experiment Paradigm:", args.exp_paradigm)
    print("Experiment Name:", args.exp_name)
    print("List of Lists:", args.list_of_lists)
    print("Stimulus Interval:", args.si)
    print("Sequence:", args.seq)

    #If SEQ is empty, then use the default sequence to create the gif
    if args.seq == []:
        SEQ = list(range(len(LIST_OF_LISTS)))
    else:
        SEQ = eval(args.seq)

    if args.node_index_list == []:
        nodelist = [None] * len(SEQ)
    else:
        nodelist = eval(args.node_index_list)

    # Load history of experiments
    if os.path.exists('history_dict.pickle'):
        with open('history_dict.pickle', 'rb') as f:
            history_exps = pickle.load(f)
    else:
        history_exps = {}
    print("historical", history_exps)
    # Check if experiment already exists
    if EXP_PARADIGM in history_exps:
        print("Experiment already exists!")
        exp_path = history_exps[EXP_PARADIGM]
        gif_path = create_gifs(exp_path, SEQ, args.si, EXP_NAME, save_path=args.save_path, nodelist=nodelist)
        print("Gif saved at: ", gif_path)
    
    else:
        print("Creating new experiment...")
        print("Experiment Name:", EXP_NAME)
        print("List of Lists:", LIST_OF_LISTS)
        exp_path, map_exp = custom_experiment(LIST_OF_LISTS, reset=False, exp_paradigm=EXP_PARADIGM, is_white=True, stimulus_interval=args.si)
        gif_path = create_gifs(exp_path, SEQ, args.si, EXP_NAME, save_path=args.save_path, nodelist=nodelist)
        print("Gif saved at: ", gif_path)
        history_exps[EXP_PARADIGM] = exp_path

        with open('history_dict.pickle', 'wb') as f:
            pickle.dump(history_exps, f)
