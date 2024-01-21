import colorsys
import datetime
import math
import numpy as np
import os
import tkinter as tk
import random
import csv
import json

from PIL import Image, ImageTk, ImageDraw
from tkinter import colorchooser
from tkinter import filedialog
from tkinter import messagebox



class AnnotationInterface:

    def __init__(self, master, initial_image_path):
        self.master = master
        self.master.after(10, lambda: self.master.attributes("-fullscreen", True))
        self.master.state('zoomed')
        
        self.image_path = image_path

        self.images = [] # To store static GIF frames
        self.all_frames = []  # To store dynamic frames for GIF animation
        self.interpolated_dot_ids = {}  # Key: connection (tuple), Value: set of dot ids 
        
        self.next_dot_id = 1  # To keep track of dot ids
        self.last_target_dot = None  # Initialize with None
        self.dot_color = 'yellow'

        self.dots = {}  # Store dot ids and their center coordinates
        self.dots_image_coordinates = {}  # Store dot ids and their coordinates in the original image
        self.total_steps = 15
        self.dot_radius = 8
        self.color_variety = 20
        self.dragging = False
        self.current_dot = None
        self.connections = []  # To store connections between dots
        self.dot_objects = []  # To store dot object ids
        self.line_objects = []  # To store line object ids
        self.potential_interpolations = {}
        self.mirrored_dot_pairs = []
# # History of actions for undo functionality.
        self.action_history = []

        self.single_process_mode = True  # Start with single process mode enabled
     
        self.left_frame = tk.Frame(master, width = 200)
        self.left_frame.pack(side = tk.LEFT, fill = tk.Y, padx = 5, pady = 5)

        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side = tk.RIGHT, fill = tk.BOTH, expand = True, padx = 5, pady = 5)

        self.canvas = tk.Canvas(self.right_frame)
        self.canvas.pack(fill = tk.BOTH, expand = True)

        self.load_background_image(initial_image_path)

# # Initialize the variable for the selected template.
        self.selected_template = tk.StringVar(self.left_frame)
# # Set the selected template to "Default".
        self.selected_template.set("Default")

# # Load templates from the current working directory.
        templates_folder = os.getcwd()
        self.load_templates_from_folder(templates_folder)

# # Create a label for selecting the template.
        tk.Label(self.left_frame, text = "Select Template:").pack(anchor = 'w')

# # Create the OptionMenu widget for selecting the template.
        self.template_menu = tk.OptionMenu(
            self.left_frame,
            self.selected_template,
            *self.templates.keys(),
            command = self.change_template
        )
        self.template_menu.pack(fill = tk.X)

# # Bind mouse events to canvas.
        self.canvas.bind("<Button - 1>", self.on_mouse_down)
        self.canvas.bind("<B1 - Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease - 1>", self.on_mouse_up)

# # Create the X - Axis Matrix frame.
        self.matrix_frame_x = tk.Frame(self.left_frame)
        self.matrix_frame_x.pack(fill = tk.BOTH, expand = True)
        tk.Label(self.matrix_frame_x, text = "X - Axis Sorted Matrix").pack(side = tk.TOP, fill = tk.X)

# # Create scrollbars for the X - Axis Matrix.
        self.scrollbar_x_vertical = tk.Scrollbar(self.matrix_frame_x, orient = tk.VERTICAL)
        self.scrollbar_x_horizontal = tk.Scrollbar(self.matrix_frame_x, orient = tk.HORIZONTAL)

# # Create the X - Axis Matrix text widget.
        self.matrix_text_x = tk.Text(
            self.matrix_frame_x,
            height = 10,
            yscrollcommand = self.scrollbar_x_vertical.set,
            xscrollcommand = self.scrollbar_x_horizontal.set,
            wrap = tk.NONE
        )

# # Configure scrollbars for the X - Axis Matrix.
        self.scrollbar_x_vertical.config(command = self.matrix_text_x.yview)
        self.scrollbar_x_horizontal.config(command = self.matrix_text_x.xview)

# # Pack the scrollbars and X - Axis Matrix text widget.
        self.scrollbar_x_vertical.pack(side = tk.RIGHT, fill = tk.Y)
        self.scrollbar_x_horizontal.pack(side = tk.BOTTOM, fill = tk.X)
        self.matrix_text_x.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

# # Create the Y - Axis Matrix frame.
        self.matrix_frame_y = tk.Frame(self.left_frame)
        self.matrix_frame_y.pack(fill = tk.BOTH, expand = True)
        tk.Label(self.matrix_frame_y, text = "Y - Axis Sorted Matrix").pack(side = tk.TOP, fill = tk.X)

# # Create scrollbars for the Y - Axis Matrix.
        self.scrollbar_y_vertical = tk.Scrollbar(self.matrix_frame_y, orient = tk.VERTICAL)
        self.scrollbar_y_horizontal = tk.Scrollbar(self.matrix_frame_y, orient = tk.HORIZONTAL)

# # Create the Y - Axis Matrix text widget.
        self.matrix_text_y = tk.Text(
            self.matrix_frame_y,
            height = 10,
            yscrollcommand = self.scrollbar_y_vertical.set,
            xscrollcommand = self.scrollbar_y_horizontal.set,
            wrap = tk.NONE
        )

# # Configure scrollbars for the Y - Axis Matrix.
        self.scrollbar_y_vertical.config(command = self.matrix_text_y.yview)
        self.scrollbar_y_horizontal.config(command = self.matrix_text_y.xview)

# # Pack the scrollbars and Y - Axis Matrix text widget.
        self.scrollbar_y_vertical.pack(side = tk.RIGHT, fill = tk.Y)
        self.scrollbar_y_horizontal.pack(side = tk.BOTTOM, fill = tk.X)
        self.matrix_text_y.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

# # Create the buttons frame.
        self.matrix_frame_buttons = tk.Frame(self.left_frame)
        self.matrix_frame_buttons.pack(fill = tk.BOTH, expand = True)

# # Create the Undo button.
        self.undo_button = tk.Button(self.matrix_frame_buttons, text = "Undo", command = self.undo_last_action)
        self.undo_button.pack()

# # Create the Erase button.
        self.erase_button = tk.Button(self.matrix_frame_buttons, text = "Erase", command = self.erase)
        self.erase_button.pack()

# # Create the Mirror Dots button.
        mirror_dots_button = tk.Button(self.matrix_frame_buttons, text="Mirror Dots", command=self.mirror_dots)
        mirror_dots_button.pack()

# # Create the Choose Dot Color button.
        self.color_button = tk.Button(self.matrix_frame_buttons, text = "Choose Dot Color", command = self.choose_dot_color)
        self.color_button.pack()

# # Create the radius scale slider.
        self.radius_scale = tk.Scale(
            self.matrix_frame_buttons,
            from_ = 1,
            to = 20,
            orient = "horizontal",
            label = "Dot Radius",
            command = self.update_radius
        )
        self.radius_scale.set(8)  # Default value
        self.radius_scale.pack()

# # Create the animate lines checkbutton.
        self.animate_lines_var = tk.IntVar(value = 1)
        self.animate_lines_checkbutton = tk.Checkbutton(
            self.matrix_frame_buttons,
            text = "Animate Lines",
            variable = self.animate_lines_var
        )
        self.animate_lines_checkbutton.pack()

# # Create the toggle mode button.
        toggle_button_text = "Single Process Mode ON" if self.single_process_mode else "Single Process Mode OFF"
        self.toggle_mode_button = tk.Button(
            self.matrix_frame_buttons,
            text = toggle_button_text,
            command = self.toggle_single_process_mode
        )
        self.toggle_mode_button.pack()

# # Create the interpolation percentage entry.
        self.interpolate_entry = tk.Entry(self.matrix_frame_buttons, width = 2)
        tk.Label(self.matrix_frame_buttons, text = "Interpolation Percentage").pack()
        self.interpolate_entry.pack()
        self.interpolate_entry.insert(0, "25")  # Default value

# # Create the Submit button.
        self.submit_button = tk.Button(self.matrix_frame_buttons, text="Submit", command=lambda: self.submit(self.connections))

        self.submit_button.pack()

# # Create the Leave button.
        self.leave_button = tk.Button(self.matrix_frame_buttons, text = "Leave", command = master.quit)
        self.leave_button.pack()

# # Create the Export to Model button
        self.export_button = tk.Button(self.matrix_frame_buttons, text = "Export to Model", command = self.export_to_model)
        self.export_button.pack()

# # Create the connections label.
        self.connections_label = tk.Label(master, text = "Connections:\n", justify = tk.LEFT)
        self.connections_label.pack()

# # Create the dots label.
        self.dots_label = tk.Label(master, text = "Dot Objects:\n", justify = tk.LEFT)
        self.dots_label.pack()

    
    def generate_random_color(self):
        return "#%06x" % random.randint(0, 0xFFFFFF)
    

    def start(self):
# # Delay image loading to ensure the canvas has been sized and displayed.
        self.master.after(100, self.load_background_image, self.image_path)


    def load_templates_from_folder(self, folder_path):
# # Initialize with the option to add a new template.
        self.templates = {"Add New...": None} 
# # List all files in the given folder.
        for file in os.listdir(folder_path):
# # Check if the file is an image (you can add or remove extensions as needed).
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
# # Construct the key for the dictionary as the file name without the extension.
                template_key = os.path.splitext(file)[0]
# # Add the file to the templates dictionary with its path.
                self.templates[template_key] = os.path.join(folder_path, file)
# # Add the default selection option.
        self.templates["Default"] = self.templates.get("Default", "body_template.png")

    
    def update_display(self, hovered_dot_id=None):
        # Format and display connections.
        connections_text = "Connections:\n" + "\n".join([f"{start} -> {end}" for start, end in self.connections])
        self.connections_label.config(text=connections_text)

        # Format and display dot objects.
        dots_text = "Dot Objects:\n"
        for dot in self.dot_objects:
            if hovered_dot_id is not None and dot == hovered_dot_id:
                # Highlight the hovered dot ID
                dots_text += f"*{str(dot)}*\n"  # You can change the formatting as needed
            else:
                dots_text += str(dot) + "\n"
        self.dots_label.config(text=dots_text)


    def update_radius(self, event = None):
        self.dot_radius = self.radius_scale.get()
# # Optional: Erase and redraw everything with new radius.
        self.erase()


    def choose_dot_color(self):
        color_code = colorchooser.askcolor(title = "Choose dot color")[1]
        if color_code:
            self.dot_color = color_code


    def load_background_image(self, image_path):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width > 1 and canvas_height > 1:
# # Load the original image.
            original_image = Image.open(image_path)
            
# # Get the size of the canvas (right part of the window).
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

# # Calculate the aspect ratio of the image.
            original_width, original_height = original_image.size
            aspect_ratio = original_height / original_width

# # Calculate the new size to fill the canvas as much as possible.
            new_width = canvas_width
            new_height = int(new_width * aspect_ratio)

# # If the new height is too large, scale it down based on the height of the canvas.
            if new_height > canvas_height:
                new_height = canvas_height
                new_width = int(new_height / aspect_ratio)
            
            self.scale_x = new_width / original_width
            self.scale_y = new_height / original_height

            self.image_x_offset = (canvas_width - new_width) / 2
            self.image_y_offset = (canvas_height - new_height) / 2

# # Resize the image to fill the canvas while maintaining the aspect ratio.
            resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.resized_image_copy = resized_image.copy()

# # Create a PhotoImage object.
            self.tk_image = ImageTk.PhotoImage(resized_image)

# # Update canvas size.
            self.canvas_width, self.canvas_height = new_width, new_height

# # Create an image object in the canvas.
            self.canvas.create_image((canvas_width - new_width) // 2, (canvas_height - new_height) // 2, anchor = 'nw', image = self.tk_image)

# # Update the scroll region to encompass the new image size.
            self.canvas.config(scrollregion = self.canvas.bbox(tk.ALL))
        else:
# # If the canvas size is still not valid, try again after a short delay.
            self.master.after(100, self.load_background_image, image_path)


    def add_new_template(self):
# # Open file dialog to select an image file.
        file_path = filedialog.askopenfilename(
            title = "Select a template image",
            filetypes = (("PNG files", " * .png"), ("JPEG files", " * .jpg"), ("All files", " * .*"))
        )
        if file_path:  # If a file was selected
# # Generate a unique key for the new template.
            template_key = f"Template {len(self.templates) - 1}"
# # Add the new template to the dictionary.
            self.templates[template_key] = file_path
# # Update the OptionMenu with the new list of templates.
            self.template_menu['menu'].add_command(label = template_key, 
                                                   command = lambda value = template_key: self.selected_template.set(value))
# # Set the newly added template as the current selection.
            self.selected_template.set(template_key)
# # Change the template to the newly added one.
            self.change_template(template_key)

    def change_template(self, choice):
        if choice == "Add New...":
            self.add_new_template()
        else:
# # Get the file path for the selected template.
            self.image_path = self.templates[choice]
            
# # Load the new template image.
            self.load_background_image(self.image_path)
            self.erase()


    def sort_dots_x(self):
        """Sort dots based on x - coordinate."""
        return sorted(self.dots.items(), key = lambda item: item[1][0])


    def sort_dots_y(self):
        """Sort dots based on y - coordinate."""
        return sorted(self.dots.items(), key = lambda item: item[1][1])
    

    def update_adjacency_matrix(self):
# # Sort dots for both matrices.
        sorted_dots_x = self.sort_dots_x()
        sorted_dots_y = self.sort_dots_y()

# # Create two matrices.
        size = len(self.dots)
        matrix_x = [[0 for _ in range(size)] for _ in range(size)]
        matrix_y = [[0 for _ in range(size)] for _ in range(size)]

# # Update both matrices based on sorted dots.
        for (start_dot, end_dot) in self.connections:
# # Find indexes in sorted lists.
            start_index_x = next(i for i, (dot_id, _) in enumerate(sorted_dots_x) if dot_id == start_dot)
            end_index_x = next(i for i, (dot_id, _) in enumerate(sorted_dots_x) if dot_id == end_dot)
            start_index_y = next(i for i, (dot_id, _) in enumerate(sorted_dots_y) if dot_id == start_dot)
            end_index_y = next(i for i, (dot_id, _) in enumerate(sorted_dots_y) if dot_id == end_dot)

# # Increment weights in matrices.
            matrix_x[start_index_x][end_index_x] += 1
            matrix_y[start_index_y][end_index_y] += 1

        self.matrix_x = matrix_x
        self.matrix_y = matrix_y

# # Format matrices as strings for display.
        matrix_str_x = "\n".join([" ".join(map(str, row)) for row in matrix_x])
        matrix_str_y = "\n".join([" ".join(map(str, row)) for row in matrix_y])

# # Display in two different Text widgets or concatenate for one widget.
        self.matrix_text_x.delete('1.0', tk.END)
        self.matrix_text_x.insert('1.0', matrix_str_x)
        self.matrix_text_y.delete('1.0', tk.END)
        self.matrix_text_y.insert('1.0', matrix_str_y)


    def is_overlapping(self, x, y):
        for _, (dot_x, dot_y) in self.dots.items():
            if ((x - dot_x) ** 2 + (y - dot_y) ** 2) <= (2 * self.dot_radius) ** 2:
                return True
        return False
    

    def is_within_bounds(self, x, y):
        return 0 <= x <= self.canvas_width and 0 <= y <= self.canvas_height
    

    def create_dot(self, x, y, interpolate = False):
        dot_count = len(self.dot_objects)
        outline_color = self.get_rainbow_color(dot_count, self.color_variety)  
        if not self.is_overlapping(x, y):
            if interpolate:
                dot_id = self.canvas.create_oval(x - self.dot_radius, y - self.dot_radius,
                                                x + self.dot_radius, y + self.dot_radius,
                                                fill = outline_color, outline = outline_color, width = self.dot_radius//4)
            else:
                dot_id = self.canvas.create_oval(x - self.dot_radius, y - self.dot_radius,
                                                x + self.dot_radius, y + self.dot_radius,
                                                fill = None, outline = outline_color, width = self.dot_radius//4)
            
            image_x, image_y = self.canvas_to_image_coords(x, y)
            self.dots[dot_id] = (x, y)
            self.dots_image_coordinates[dot_id] = (image_x, image_y)
            self.dot_objects.append(dot_id)  # Store regular dot object ID
            self.action_history.append(('dot', dot_id))
        
# # Bind hover events for highlighting
            self.canvas.tag_bind(dot_id, '<Enter>', lambda e, dot_id=dot_id: self.on_dot_enter(dot_id))
            self.canvas.tag_bind(dot_id, '<Leave>', lambda e: self.unhighlight_matrix())
            self.update_adjacency_matrix()
            return dot_id
        return None
    

    def on_dot_enter(self, dot_id):
        self.highlight_matrix_row_column(dot_id)
        self.sort_dots_by_proximity(dot_id)
        self.update_display(hovered_dot_id=dot_id)


    def mirror_dots(self):
        image_midline = self.image_x_offset + self.canvas_width / 2
        for dot_id, (x, y) in list(self.dots.items()):
            mirrored_x = 2 * image_midline - x
            if not self.is_overlapping(mirrored_x, y):
                new_dot_id = self.create_dot(mirrored_x, y)
                self.mirrored_dot_pairs.append((dot_id, new_dot_id))
        self.update_display()
        self.update_adjacency_matrix()
        self.update_mirror_matrix()

    def update_mirror_matrix(self):
        # Save the reordered dot_id
        image_midline = self.image_x_offset + self.canvas_width / 2
        left_half_dots = [(dot_id, (x, y)) for dot_id, (x, y) in self.dots.items() if x < image_midline]
        self.left_half_dots = sorted(left_half_dots, key=lambda dot: dot[1][0])  # Sort based on x-coordinate
    
        right_half_dots = [(dot_id, (x, y)) for dot_id, (x, y) in self.dots.items() if x > image_midline]
        self.right_half_dots = sorted(right_half_dots, key=lambda dot: dot[1][0], reverse=True)  # Sort based on reversed x-coordinate
        print(self.left_half_dots, self.right_half_dots)
        # Initialize the mirrored ajacency matrix
        size = len(left_half_dots)
        adjacency_matrix = np.zeros((size, size), dtype=int)
        # Fill in the adjacency matrix with hop distances
        for i in range(size):
            for j in range(size):
                # The hop distance is the absolute difference between indices
                adjacency_matrix[i, j] = i - j
        self.mirrored_adjacency_matrix = adjacency_matrix
        self.update_text_widget()


    def update_text_widget(self):
            # Check if the popup window and text widget still exist
            if hasattr(self, 'popup_window') and self.popup_window.winfo_exists():
                if hasattr(self, 'text_widget'):
                    # Clear the existing content
                    self.text_widget.delete(1.0, tk.END)
            # Create the adjacency matrix table
                adjacency_matrix = self.mirrored_adjacency_matrix

                # Add column labels, which are the same as row labels
                combined_labels = [f"{left_dot_id}/{right_dot_id}" for left_dot_id, right_dot_id in
                                zip([ld[0] for ld in self.left_half_dots], [rd[0] for rd in self.right_half_dots])]
                column_labels = "\t".join(combined_labels)
                self.text_widget.insert(tk.END, "\t" + column_labels + "\n")

                # Add row labels and matrix values
                for i, label in enumerate(combined_labels):
                    row_text = label + "\t" + "\t".join(str(cell) for cell in adjacency_matrix[i]) + "\n"
                    self.text_widget.insert(tk.END, row_text)


    def export_to_model(self):
        
        def save_matrix_as_csv(matrix, combined_labels, filename):
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write the header
                writer.writerow([f"{label:<{len(label)}}" for label in combined_labels])
                # Write the rest of the rows
                for row in matrix:
                    writer.writerow([str(cell) for cell in row])

        def save_action():
            # Ask the user for a location and name to save the matrix
            filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],initialdir=os.getcwd(),initialfile = "MYMatrix_EXPERIMENT_NAME.csv")
            if filename:
                # Save the mirrored adjacency matrix and indices as CSV
                combined_labels = [f"{ld}/{rd}" for ld, rd in zip([ld for ld in self.left_half_dots], [rd for rd in self.right_half_dots])]
                # Save the mirrored adjacency matrix as CSV
                save_matrix_as_csv(self.mirrored_adjacency_matrix, combined_labels, filename)
                messagebox.showinfo("Save Successful", f"Matrix saved to {filename}")
                
        if not hasattr(self, "popup_window") or not self.popup_window.winfo_exists():
            self.popup_window = tk.Toplevel()
            self.popup_window.resizable(True, True)
            self.popup_window.title("Adjacency Matrix")
            self.popup_window.attributes('-topmost', True)
            # Create a Text widget for better formatting
            self.text_widget = tk.Text(self.popup_window)
            self.text_widget.pack(fill=tk.BOTH, expand=True)
            save_button = tk.Button(self.popup_window, text="Save", command=save_action)
            save_button.pack()

        self.update_text_widget()
        

    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to image coordinates."""
        image_x = (canvas_x - self.image_x_offset) / self.scale_x
        image_y = (canvas_y - self.image_y_offset) / self.scale_y
        return image_x, image_y

    def highlight_matrix_row_column(self, dot_id):
        dot_index_x = next(i for i, (dot_id_x, _) in enumerate(self.sort_dots_x()) if dot_id_x == dot_id)
        dot_index_y = next(i for i, (dot_id_y, _) in enumerate(self.sort_dots_y()) if dot_id_y == dot_id)
        char_per_number = 1  # Adjust based on your matrix formatting
        separator_size = 1   # Number of characters used as a separator between columns
        for matrix_text, dot_index in [(self.matrix_text_x, dot_index_x), (self.matrix_text_y, dot_index_y)]:
            line_index = dot_index + 1
# # Highlight row.
            matrix_text.tag_add("highlight_row", f"{line_index}.0", f"{line_index}.end")

# # Calculate the starting and ending positions for the column highlight.
            start_col = dot_index * (char_per_number + separator_size)
            end_col = start_col + char_per_number

# # Highlight column.
            for i in range(1, len(self.dots) + 1):
                matrix_text.tag_add("highlight_col", f"{i}.{start_col}", f"{i}.{end_col}")
            matrix_text.tag_config("highlight_row", background = "lightblue")
            matrix_text.tag_config("highlight_col", background = "lightblue")

    def unhighlight_matrix(self, event = None):
# # Remove any existing highlighting in both matrices.
        for matrix_text in [self.matrix_text_x, self.matrix_text_y]:
            matrix_text.tag_remove("highlight_row", "1.0", tk.END)
            matrix_text.tag_remove("highlight_col", "1.0", tk.END)
      
    def apply_interpolation_to_line(self, percentage, connection):
        if percentage == 0:
            return
        
        self.canvas.delete(self.line_objects[ - 1])
        self.line_objects.pop()
        self.action_history.pop()

        image_midline = self.image_x_offset + self.canvas_width / 2

        if connection in self.connections:
            start_dot, end_dot = connection
            start_x, start_y = self.dots[start_dot]
            end_x, end_y = self.dots[end_dot]

            distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
            max_dots = int(distance / (2 * self.dot_radius)) - 1
            num_points_to_show = int(max_dots * percentage / 100)
            
# # Remove the original connection.
            self.connections.remove(connection)

# # List to store the newly created dot IDs.
            new_dot_ids = []

            for i in range(1, num_points_to_show + 1):
                inter_x = start_x + (end_x - start_x) * (i / (num_points_to_show + 1))
                inter_y = start_y + (end_y - start_y) * (i / (num_points_to_show + 1))
                if not self.is_overlapping(inter_x, inter_y):
                    interpolated_dot_id = self.create_dot(inter_x, inter_y, interpolate = True)
                    new_dot_ids.append(interpolated_dot_id)
                    if connection not in self.interpolated_dot_ids:
                        self.interpolated_dot_ids[connection] = set()
                    self.interpolated_dot_ids[connection].add(interpolated_dot_id)

                # Check if the connection is symmetrical
                mirrored_x = 2 * image_midline - inter_x
                if self.is_overlapping(mirrored_x, inter_y):
                # Find which dot it is overlapping with
                    for dot_id, (dot_x, dot_y) in self.dots.items():
                        if ((mirrored_x - dot_x) ** 2 + (inter_y - dot_y) ** 2) <= (2 * self.dot_radius) ** 2:
                            self.mirrored_dot_pairs.append((interpolated_dot_id, dot_id))
                            print("added mirrored pair")
                            print(interpolated_dot_id, dot_id)
                            self.update_mirror_matrix()
                            break

# # Create new connections.
            line_color = self.get_rainbow_color(len(self.line_objects), 20)
            all_dots = [start_dot] + new_dot_ids + [end_dot]
            for i in range(len(all_dots) - 1):
                line_id = self.canvas.create_line( * self.dots[all_dots[i]], *self.dots[all_dots[i + 1]], fill = line_color, smooth = True, width = self.dot_radius//2, arrow = tk.LAST)
                self.line_objects.append(line_id)
                self.connections.append((all_dots[i], all_dots[i + 1]))
                self.action_history.append(('line', line_id))
        #self.intepretedpath.append((connection, percentage))

    def clear_interpolated_dots(self, connection):
        if connection in self.interpolated_dot_ids:
            for dot_id in self.interpolated_dot_ids[connection]:
                self.canvas.delete(dot_id)
            del self.interpolated_dot_ids[connection]
            self.update_text_widget()

    def erase(self):
        for dot in self.dot_objects:
            self.canvas.delete(dot)  # Remove each dot
        for line in self.line_objects:
            self.canvas.delete(line)  # Remove each line
        for connection, interpolated_dots in self.interpolated_dot_ids.items():
            for dot in interpolated_dots:
                self.canvas.delete(dot)  # Remove each interpolated dot
        self.dots.clear()
        self.dots_image_coordinates.clear()
        self.connections.clear()
        self.dot_objects.clear()
        self.line_objects.clear()
        self.interpolated_dot_ids.clear()
        self.action_history.clear()
        self.update_adjacency_matrix()
        self.update_display()
        self.mirrored_dot_pairs.clear()
        self.update_mirror_matrix()


    def toggle_single_process_mode(self):
        self.single_process_mode = not self.single_process_mode
        button_text = "Single Process Mode ON" if self.single_process_mode else "Single Process Mode OFF"
        self.toggle_mode_button.config(text = button_text)
        self.erase()
    
   
    def draw_canvas_state(self, step, connections):
# # Load and convert the original image.
        original_image = Image.open(self.image_path).convert("RGBA")

# # Get window dimensions.
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()

# # Calculate the scaling factor based on window width (assuming length is width).
        scale_factor = min(window_width / original_image.width, 
                        (window_height - 150) / original_image.height)  

# # Apply scaling factor to get new dimensions.
        new_width = int(original_image.width * scale_factor)
        new_height = int(original_image.height * scale_factor)

# # Resize the image.
        resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# # Create a drawing context.
        draw = ImageDraw.Draw(resized_image)

        dot_colors = {dot_id: None for dot_id in self.dots}

        dot_indices = {dot_id: index for index, dot_id in enumerate(self.dots)}

# # Adjust the dot coordinates according to the new scaling factor.
        dots = {dot_id: (int(x * scale_factor), int(y * scale_factor)) for dot_id, (x, y) in self.dots_image_coordinates.items()}

# # Draw connections up to the current step with color.
        for i, (start_dot, end_dot) in enumerate(connections[:step]):
            start_x, start_y = dots[start_dot]
            end_x, end_y = dots[end_dot]
            line_color = self.get_rainbow_color(i, 20)

# # Update dot colors to the current line color.
            dot_colors[start_dot] = line_color
            dot_colors[end_dot] = line_color
            draw.line((start_x, start_y, end_x, end_y), fill = line_color, width = self.dot_radius // 2)

# # Draw dots with their latest color.
        for dot_id, (x, y) in dots.items():
            dot_color = dot_colors[dot_id]
            dot_index = dot_indices.get(dot_id, 0)
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill = dot_color, outline = self.get_rainbow_color(dot_index, self.color_variety))
        return resized_image

    def create_frames(self, connections):
        self.all_frames.clear()
        total_steps = self.total_steps # The number of steps for each line

        original_image = Image.open(self.image_path).convert("RGBA")

        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()

# # Calculate the scaling factor based on window width (assuming length is width).
        scale_factor = min(window_width / original_image.width, 
                        (window_height - 150) / original_image.height)  

# # Apply scaling factor to get new dimensions.
        new_width = int(original_image.width * scale_factor)
        new_height = int(original_image.height * scale_factor)

# # Resize the image.
        self.resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# # Adjust the dot coordinates according to the new scaling factor.
        self.tem_dots = {dot_id: (int(x * scale_factor), int(y * scale_factor)) for dot_id, (x, y) in self.dots_image_coordinates.items()}

        self.scale_factor = scale_factor

        for start_dot, end_dot in connections:
            if start_dot not in self.dots or end_dot not in self.dots:
                print(f"Invalid connection: {start_dot} to {end_dot}")
                continue  # Skip invalid connections
            line_dist = self.line_length(start_dot, end_dot)
            for step in range(total_steps + 1):
# # Calculate step increment based on line length.
                step_increment = (line_dist / total_steps) * step
                self.add_frame_for_step(start_dot, end_dot, step_increment, connections)

    def add_frame_for_step(self, start_dot, end_dot, step_increment, connections):
        image = self.resized_image.copy()
        draw = ImageDraw.Draw(image)
        dots = self.tem_dots
# # Draw all previous connections completely.
        for i, (prev_start, prev_end) in enumerate(connections):
            if prev_start == start_dot and prev_end == end_dot:
                break  # Stop when reaching the current connection
            self.draw_complete_line(draw, prev_start, prev_end, i)

# # Calculate the partial endpoint for the current connection.
        start_x, start_y = dots[start_dot]
        end_x, end_y = dots[end_dot]
        line_length = self.line_length(start_dot, end_dot) * self.scale_factor

        if line_length != 0:
            ratio = step_increment / line_length
            partial_end_x = start_x + (end_x - start_x) * ratio
            partial_end_y = start_y + (end_y - start_y) * ratio
            current_color_index = connections.index((start_dot, end_dot))
# # Pass coordinates to draw_partial_line.
            self.draw_partial_line(draw, (start_x, start_y), (partial_end_x, partial_end_y), current_color_index)

        self.all_frames.append(image)

    def draw_complete_line(self, draw, start_dot, end_dot, color_index):
        start_x, start_y = self.tem_dots[start_dot]
        end_x, end_y = self.tem_dots[end_dot]
        line_color = self.get_rainbow_color(color_index, 20)
        draw.line((start_x, start_y, end_x, end_y), fill = line_color, width = self.dot_radius // 2)

    def draw_partial_line(self, draw, start_coords, end_coords, color_index):
        line_color = self.get_rainbow_color(color_index, 20)
        draw.line((start_coords[0], start_coords[1], end_coords[0], end_coords[1]), fill = line_color, width = self.dot_radius // 2)

    def draw_partial_connection(self, draw, start_dot, end_dot, line_color, step):
        start_x, start_y = self.tem_dots[start_dot]
        end_x, end_y = self.tem_dots[end_dot]
        line_length = self.line_length(start_dot, end_dot) * self.scale_factor
        if line_length != 0:
            ratio = step / self.total_steps
            partial_end_x = start_x + (end_x - start_x) * ratio
            partial_end_y = start_y + (end_y - start_y) * ratio
            draw.line((start_x, start_y, partial_end_x, partial_end_y), fill = line_color, width = self.dot_radius // 2)
# # Update the color of the start dot.
        if step > 0:  # Change color after the first step
            self.update_dot_color(draw, start_dot, line_color)

    def update_dot_color(self, draw, dot_id, color):
        x, y = self.tem_dots[dot_id]
        draw.ellipse((x - self.dot_radius, y - self.dot_radius, x + self.dot_radius, y + self.dot_radius), fill = color, outline = color)

    def draw_connection_step(self, connection_index, step, connections):
        image = self.resized_image.copy()
        draw = ImageDraw.Draw(image)
        dot_indices = {dot_id: index for index, dot_id in enumerate(self.dots)}

# # Draw all dots initially with only outline.
        for dot_id, (x, y) in self.tem_dots.items():
            dot_index = dot_indices.get(dot_id, 0)
            draw.ellipse((x - self.dot_radius, y - self.dot_radius, x + self.dot_radius, y + self.dot_radius), fill = None, outline = self.get_rainbow_color(dot_index, self.color_variety))

# # Draw all previous connections completely and update dot colors.
        for i, (prev_start, prev_end) in enumerate(connections[:connection_index]):
            line_color = self.get_rainbow_color(i, 20)
            self.draw_complete_line(draw, prev_start, prev_end, i)
            self.update_dot_color(draw, prev_start, line_color)
            self.update_dot_color(draw, prev_end, line_color)

# # Draw the current connection partially.
        if connection_index < len(connections):
            current_line_color = self.get_rainbow_color(connection_index, 20)
            start_dot, end_dot = connections[connection_index]
            self.draw_partial_connection( draw, start_dot, end_dot, current_line_color, step)

# # Update start dot color immediately.
            self.update_dot_color(draw, start_dot, current_line_color)

# # Update end dot color when the line reaches it.
            if connection_index < len(connections) and step == self.total_steps - 1:              
                root.after(0, self.unhighlight_matrix(), None)
                self.update_dot_color(draw, end_dot, current_line_color)
                root.after(0, lambda: self.highlight_matrix_row_column(end_dot))

        return image

    def save_gif(self, ms_per_frame):
        current_time = datetime.datetime.now().strftime("%M%S")
        gif_path = f"static_visualization_{ms_per_frame}_{current_time}.gif"
        self.images[0].save(gif_path, save_all = True, append_images = self.images[1:], duration = ms_per_frame, loop = 0)
        messagebox.showinfo("Saved", f"GIF saved at {gif_path}")

    def save_animated_gif(self, frames, ms_per_frame):
        current_time = datetime.datetime.now().strftime("%M%S")
        gif_path = f"animated_lines_{ms_per_frame}_{current_time}.gif"
        frames[0].save(gif_path, save_all = True, append_images = frames[1:], duration = ms_per_frame, loop = 0)
        messagebox.showinfo("Saved", f"GIF saved at {gif_path}")


    def sort_dots_by_proximity(self, hovered_dot_id, n_neighbors=4):
        random_color = self.generate_random_color()
        proximity_scores = {}
        for dot_id in self.dots:
            if dot_id != hovered_dot_id:
                proximity_scores[dot_id] = self.calculate_proximity_score(hovered_dot_id, dot_id)
        # Sort dots by their proximity scores in descending order (closest first)
        sorted_dots = sorted(proximity_scores, key=proximity_scores.get, reverse=True)
        for dot_id in sorted_dots[:n_neighbors]:
            self.canvas.itemconfig(dot_id, fill=random_color)
        sorted_dots = sorted(proximity_scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_dots
    

    def max_connections_count(self):
        connection_counts = {}
        for start_dot, end_dot in self.connections:
            connection_counts[start_dot] = connection_counts.get(start_dot, 0) + 1
            connection_counts[end_dot] = connection_counts.get(end_dot, 0) + 1
        return max(connection_counts.values(), default=0)

    
    def calculate_proximity_score(self, dot_id_1, dot_id_2, max_distance=100.0):
        x1, y1 = self.dots[dot_id_1]
        x2, y2 = self.dots[dot_id_2]
        distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        proximity_score = max_distance / (distance + 1)  # +1 to avoid division by zero
    # Normalize connection count component
        max_connection_count = self.max_connections_count()
        connection_count = sum(dot_id_2 in pair for pair in self.connections)
        normalized_connection_score = connection_count / max_connection_count if max_connection_count > 0 else 0

        # Combine both scores
        proximity_score += normalized_connection_score * 1 #factor yet to be ajusted
        # Add score for opposite dots
        if (dot_id_1, dot_id_2) in self.mirrored_dot_pairs or (dot_id_2, dot_id_1) in self.mirrored_dot_pairs:
            proximity_score += 1

        for mirrored_pair in self.mirrored_dot_pairs:
            mx1, my1 = self.dots.get(mirrored_pair[0], (0, 0))
            mx2, my2 = self.dots.get(mirrored_pair[1], (0, 0))
            if min(mx1, mx2) <= x2 <= max(mx1, mx2) and min(my1, my2) <= y2 <= max(my1, my2):
                proximity_score += 1
                break  # Break after finding the first pair that satisfies the condition
        return proximity_score

    def generate_new_connections(self, current_dot, sorted_dots, visited_dots):
        if len(visited_dots) == len(self.dots):
            # All dots have been visited
            return []
        new_connections = []
        for next_dot, _ in sorted_dots:
            if next_dot not in visited_dots and next_dot != current_dot:
                # Add the connection and mark the next dot as visited
                new_connections.append((current_dot, next_dot))
                visited_dots.add(next_dot)
                # Recursively find the next connections from the new dot
                new_connections.extend(self.generate_new_connections(next_dot, sorted_dots, visited_dots))
                break
        return new_connections
    

    def generate_more_experiments(self):
        self.mirror_dots()
        # Select a random starting dot
        starting_dot_id = random.choice(list(self.dots.keys()))
        # Calculate proximity scores
        visited_dots = {starting_dot_id}
        sorted_dots = self.sort_dots_by_proximity(starting_dot_id)
        # Generate new connections using the recursive method
        new_connections = self.generate_new_connections(starting_dot_id, sorted_dots, visited_dots)
        # Draw the new connections
        self.submit(new_connections)


    def create_static_image(self, connections):
        self.images.clear()
        for step in range(len(connections) + 1):
            img = self.draw_canvas_state(step, connections)
            self.images.append(img)

# # Create a new window for the GIF.
        gif_window = tk.Toplevel(self.master)
        gif_window.title("Experiment Preview")

        gif_label = tk.Label(gif_window)
        gif_label.pack()

# # Slider for adjusting frame speed.
        speed_scale = tk.Scale(gif_window, from_ = 0, to = 2000, orient = "horizontal", label = "Interval (ms)")
        speed_scale.set(300)  # Default value
        speed_scale.pack()

# # Function to update GIF frames.
        def update_gif(index = 0):
            frame_speed = speed_scale.get()
            frame = ImageTk.PhotoImage(image = self.images[index])
            gif_label.config(image = frame)
            gif_label.image = frame
            index = (index + 1) % len(self.images)
            gif_window.after(frame_speed, update_gif, index)
        update_gif()  # Start the GIF

# # Add a button to save the GIF.
        save_button = tk.Button(gif_window, text = "Save GIF", command = lambda: self.save_gif(speed_scale.get()))
        save_button.pack()

        more_experiments_button = tk.Button(gif_window, text="More Experiments", command=self.generate_more_experiments)
        more_experiments_button.pack()

    def submit(self, connections):
        if self.animate_lines_var.get() == 1:
# # Set up the window for animation.
            self.setup_animation_window(connections)
        else:
# # Create and show a static image.
            self.create_static_image(connections)

    def play_animation(self, gif_label, speed_scale, frame_index, current_connection_index, connections):
        total_time_per_line = speed_scale.get()  # Total time to draw each line in ms

        if current_connection_index < len(connections):
# # Calculate the actual frame index for the current connection.
            actual_frame_index = frame_index % self.total_steps

# # Display the frame for the current connection step.
            frame_image = self.draw_connection_step(current_connection_index, actual_frame_index, connections)
            frame = ImageTk.PhotoImage(image = frame_image)
            gif_label.config(image = frame)
            gif_label.image = frame

# # Prepare for the next frame.
            next_frame_index = frame_index + 1
            if actual_frame_index == self.total_steps - 1:
# # Move to the next connection after completing the current one.
                next_connection_index = current_connection_index + 1
            else:
                next_connection_index = current_connection_index

# # Calculate delay for each step.
            self.step_delay = total_time_per_line // self.total_steps
            gif_label.after(self.step_delay, lambda: self.play_animation(gif_label, speed_scale, next_frame_index, next_connection_index, connections))
        else:
# # Restart the animation once all connections are drawn.
            self.play_animation(gif_label, speed_scale, 0, 0, connections=connections)

    def setup_animation_window(self, connections):
        
        gif_window = tk.Toplevel(self.master)
        gif_window.title("GIF Animation")

        gif_label = tk.Label(gif_window)
        gif_label.pack()

        speed_scale = tk.Scale(gif_window, from_ = 0, to = 2000, orient = "horizontal", label = "Interval (ms)")
        speed_scale.set(300)
        speed_scale.pack()

        temdots = self.create_frames(connections)  # Call a function to create all frames
        self.play_animation(gif_label, speed_scale, 0 , 0, connections=connections)  # Start playing the animation

        save_button = tk.Button(gif_window, text = "Save GIF", command = lambda: self.save_animated_gif(self.all_frames, self.step_delay))
        save_button.pack()

        more_experiments_button = tk.Button(gif_window, text="More Experiments", command=self.generate_more_experiments)
        more_experiments_button.pack()


    def on_mouse_down(self, event):
        clicked_dot = self.find_nearest_dot(event.x, event.y)

        if clicked_dot is None:
            self.current_dot = self.create_dot(event.x, event.y)
        else:
            if not self.single_process_mode or not self.connections or clicked_dot == self.connections[ - 1][1]:
                self.current_dot = clicked_dot
            else:
                self.current_dot = None

    def on_mouse_move(self, event):
        self.dragging = True

    def on_mouse_up(self, event):
        if self.dragging and self.current_dot is not None:
            end_dot = self.find_nearest_dot(event.x, event.y)
            if end_dot and end_dot != self.current_dot:
# # Draw the line.
                start_x, start_y = self.dots[self.current_dot]
                end_x, end_y = self.dots[end_dot]
                line_color = self.get_rainbow_color(len(self.line_objects), 20)
                line_id = self.canvas.create_line(start_x, start_y, end_x, end_y, fill = line_color, smooth = True, width = self.dot_radius // 2, arrow = tk.LAST)
                self.line_objects.append(line_id)
                self.connections.append((self.current_dot, end_dot))
                self.action_history.append(('line', line_id))
                self.canvas.itemconfig(self.current_dot, fill = line_color, outline = line_color)
                self.canvas.itemconfig(end_dot, fill = line_color, outline = line_color)
# # Calculate and store potential interpolation points for this line.
                percentage = float(self.interpolate_entry.get())  # Get current percentage
                self.apply_interpolation_to_line(percentage, self.connections[ - 1])
        self.dragging = False
        self.current_dot = None
# # Update the display.
        self.update_adjacency_matrix()
        self.update_display()
    
    def find_nearest_dot(self, x, y):
        for dot_id, (dot_x, dot_y) in self.dots.items():
            if (x - dot_x) ** 2 + (y - dot_y) ** 2 <= (2 * self.dot_radius) ** 2:
                return dot_id
        return None
    
    def get_rainbow_color(self, index, total):
        """Get a color from the rainbow spectrum based on the index, excluding white and black."""
# # Adjust the hue range to be within 0 to 1, avoiding values that may lead to white or black.
        hue = (index / total) * 0.8 + 0.1  # This will avoid the extreme ends of the hue spectrum
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)  # Convert HSV to RGB with full saturation and value
        return '#%02x%02x%02x' % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

    def undo_last_action(self): 
        if self.action_history:
            action, item_id = self.action_history.pop()

            if action == 'dot':
# # Undo dot creation.
                self.canvas.delete(item_id)
                del self.dots[item_id]
                del self.dots_image_coordinates[item_id]
                self.dot_objects.remove(item_id)

# # Remove any connections involving this dot.
                self.connections = [(start, end) for start, end in self.connections if start != item_id and end != item_id]

            elif action == 'line':
# # Undo line creation.
                self.canvas.delete(item_id)
                self.line_objects.remove(item_id)
                self.connections.pop()
            self.update_adjacency_matrix()
            self.update_display()
            self.update_mirror_matrix()


    def line_length(self, start_dot, end_dot):
        start_x, start_y = self.dots_image_coordinates[start_dot]
        end_x, end_y = self.dots_image_coordinates[end_dot]
        return math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)

root = tk.Tk()
root.title("Annotation for Introspection Interface")
import os

# Get the current working directory.
current_dir = os.getcwd()

# Construct the relative file path to the image.
image_path = os.path.join(current_dir, 'Default.png')
app = AnnotationInterface(root, image_path)
root.mainloop()
