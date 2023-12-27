import tkinter as tk
from PIL import Image, ImageTk,ImageDraw
import colorsys
import os
from tkinter import messagebox
import datetime
import math

class AnnotationInterface:
     
    def __init__(self, master, image_path):
        self.master = master
        self.image_path = image_path
        self.load_background_image(image_path)
        self.images = [] # To store static GIF frames
        self.all_frames = []  # To store dynamic frames for GIF animation
        self.interpolated_dot_ids = {}  # Key: connection (tuple), Value: set of dot ids 
        
        self.next_dot_id = 1  # To keep track of dot ids
        self.last_target_dot = None  # Initialize with None


        self.dots = {}  # Store dot ids and their center coordinates
        self.total_steps = 9
        self.dot_radius = 8
        self.dragging = False
        self.current_dot = None
        self.connections = []  # To store connections between dots
        self.dot_objects = []  # To store dot object ids
        self.line_objects = []  # To store line object ids
        self.potential_interpolations = {}
        self.intepretedpath = []

        self.single_process_mode = True  # Start with single process mode enabled
        self.no_skipping_mode = False  # Start with no skipping mode disabled


        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor='nw', image=self.tk_image)
        
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # History of actions for undo functionality
        self.action_history = []

        # Setup for matrix X
        self.matrix_frame_x = tk.Frame(master)
        self.matrix_frame_x.pack(side=tk.LEFT)
        tk.Label(self.matrix_frame_x, text="X-Axis Sorted Matrix").pack()
        self.matrix_text_x = tk.Text(self.matrix_frame_x, width=30, height=20)
        self.matrix_text_x.pack()

        # Setup the buttons frame in the middle
        self.matrix_frame_buttons = tk.Frame(master)
        self.matrix_frame_buttons.pack(side=tk.LEFT)
        self.undo_button = tk.Button(self.matrix_frame_buttons, text="Undo", command=self.undo_last_action)
        self.undo_button.pack()
        self.erase_button = tk.Button(self.matrix_frame_buttons, text="Erase", command=self.erase)
        self.erase_button.pack()

        # Variable to hold the checkbutton state
        self.animate_lines_var = tk.IntVar()
        # Create the checkbutton
        self.animate_lines_checkbutton = tk.Checkbutton(master, text="Animate Lines", variable=self.animate_lines_var)
        self.animate_lines_checkbutton.pack()
        
        # Toggle button for single process mode
        toggle_button_text = "Single Process Mode ON" if self.single_process_mode else "Single Process Mode OFF"
        self.toggle_mode_button = tk.Button(self.matrix_frame_buttons, text=toggle_button_text, command=self.toggle_single_process_mode)
        self.toggle_mode_button.pack()
        self.toggle_no_skipping_button = tk.Button(self.matrix_frame_buttons, text="Skipping Mode OFF", command=self.toggle_no_skipping_mode)
        self.toggle_no_skipping_button.pack()

        # Setup for matrix Y
        self.matrix_frame_y = tk.Frame(master)
        self.matrix_frame_y.pack(side=tk.LEFT)
        tk.Label(self.matrix_frame_y, text="Y-Axis Sorted Matrix").pack()
        self.matrix_text_y = tk.Text(self.matrix_frame_y, width=30, height=20)
        self.matrix_text_y.pack()

        # Add an Entry widget for interpolation percentage
        self.interpolate_entry = tk.Entry(self.matrix_frame_buttons, width=2)
        tk.Label(self.matrix_frame_buttons, text="Interpolation Percentage").pack()
        self.interpolate_entry.pack()
        self.interpolate_entry.insert(0, "25")  # Default value

        self.submit_button = tk.Button(self.matrix_frame_buttons, text="Submit", command=self.submit)
        self.submit_button.pack()

        self.leave_button = tk.Button(self.matrix_frame_buttons, text="Leave", command=master.quit)
        self.leave_button.pack()

        self.connections_label = tk.Label(master, text="", justify=tk.LEFT)
        self.connections_label.pack()

        self.dots_label = tk.Label(master, text="", justify=tk.LEFT)
        self.dots_label.pack()

    def update_display(self):
        # Format and display connections
        connections_text = "Connections:\n" + "\n".join([f"{start} -> {end}" for start, end in self.connections])
        self.connections_label.config(text=connections_text)

        # Format and display dot objects
        dots_text = "Dot Objects:\n" + "\n".join([str(dot) for dot in self.dot_objects])
        self.dots_label.config(text=dots_text)

    def load_background_image(self, image_path):
        self.image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas_width, self.canvas_height = self.image.size

    def sort_dots_x(self):
        """Sort dots based on x-coordinate."""
        return sorted(self.dots.items(), key=lambda item: item[1][0])

    def sort_dots_y(self):
        """Sort dots based on y-coordinate."""
        return sorted(self.dots.items(), key=lambda item: item[1][1])
    
    def update_adjacency_matrix(self):
        # Sort dots for both matrices
        sorted_dots_x = self.sort_dots_x()
        sorted_dots_y = self.sort_dots_y()

        # Create two matrices
        size = len(self.dots)
        matrix_x = [[0 for _ in range(size)] for _ in range(size)]
        matrix_y = [[0 for _ in range(size)] for _ in range(size)]

        # Update both matrices based on sorted dots
        for (start_dot, end_dot) in self.connections:
            # Find indexes in sorted lists
            start_index_x = next(i for i, (dot_id, _) in enumerate(sorted_dots_x) if dot_id == start_dot)
            end_index_x = next(i for i, (dot_id, _) in enumerate(sorted_dots_x) if dot_id == end_dot)
            start_index_y = next(i for i, (dot_id, _) in enumerate(sorted_dots_y) if dot_id == start_dot)
            end_index_y = next(i for i, (dot_id, _) in enumerate(sorted_dots_y) if dot_id == end_dot)

            # Increment weights in matrices
            matrix_x[start_index_x][end_index_x] += 1
            matrix_y[start_index_y][end_index_y] += 1

        # Format matrices as strings for display
        matrix_str_x = "\n".join([" ".join(map(str, row)) for row in matrix_x])
        matrix_str_y = "\n".join([" ".join(map(str, row)) for row in matrix_y])

        # Display in two different Text widgets or concatenate for one widget
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

    def is_white_space(self, x, y):
        """Check if the pixel at (x, y) is white or close to white."""
        pixel = self.image.getpixel((x, y))
        return all(value > 200 for value in pixel[:3])  # Assuming RGB, close to white
    
    def is_line_in_white_space(self, start_x, start_y, end_x, end_y):
        """Check if a line between two points crosses white space."""
        # Sample a number of points along the line
        num_samples = 20
        for i in range(1, num_samples):
            x = start_x + (end_x - start_x) * i / num_samples
            y = start_y + (end_y - start_y) * i / num_samples
            if not self.is_white_space(x, y):
                return False
        return True
    
    def create_dot(self, x, y, color="black"):
        if not self.is_overlapping(x, y) and self.is_white_space(x, y):
            dot_id = self.canvas.create_oval(x - self.dot_radius, y - self.dot_radius,
                                            x + self.dot_radius, y + self.dot_radius,
                                            fill=color, outline=color)
            self.dots[dot_id] = (x, y)
           
            self.dot_objects.append(dot_id)  # Store regular dot object ID
            self.action_history.append(('dot', dot_id))
        
            # Bind hover events for highlighting
            self.canvas.tag_bind(dot_id, '<Enter>', lambda e, dot_id=dot_id: self.highlight_matrix_row_column(dot_id))
            self.canvas.tag_bind(dot_id, '<Leave>', lambda e: self.unhighlight_matrix())
            self.update_adjacency_matrix()
            return dot_id
        return None

    def highlight_matrix_row_column(self, dot_id):
        # Find indices in both sorted lists
        dot_index_x = next(i for i, (dot_id_x, _) in enumerate(self.sort_dots_x()) if dot_id_x == dot_id)
        dot_index_y = next(i for i, (dot_id_y, _) in enumerate(self.sort_dots_y()) if dot_id_y == dot_id)

        # Highlight the corresponding row and column in both matrices
        for matrix_text, dot_index in [(self.matrix_text_x, dot_index_x), (self.matrix_text_y, dot_index_y)]:
            line_index = dot_index + 1
            # Highlight row
            matrix_text.tag_add("highlight_row", f"{line_index}.0", f"{line_index}.end")
            # Highlight column (for each character position in all lines)
            for i in range(1, len(self.dots) + 1):
                matrix_text.tag_add("highlight_col", f"{i}.{dot_index}", f"{i}.{dot_index+1}")
            matrix_text.tag_config("highlight_row", background="lightblue")
            matrix_text.tag_config("highlight_col", background="lightblue")

    def highlight_matrix_row_column(self, dot_id):
        dot_index_x = next(i for i, (dot_id_x, _) in enumerate(self.sort_dots_x()) if dot_id_x == dot_id)
        dot_index_y = next(i for i, (dot_id_y, _) in enumerate(self.sort_dots_y()) if dot_id_y == dot_id)
        char_per_number = 1  # Adjust based on your matrix formatting
        separator_size = 1   # Number of characters used as a separator between columns
        for matrix_text, dot_index in [(self.matrix_text_x, dot_index_x), (self.matrix_text_y, dot_index_y)]:
            line_index = dot_index + 1
            # Highlight row
            matrix_text.tag_add("highlight_row", f"{line_index}.0", f"{line_index}.end")

            # Calculate the starting and ending positions for the column highlight
            start_col = dot_index * (char_per_number + separator_size)
            end_col = start_col + char_per_number

            # Highlight column
            for i in range(1, len(self.dots) + 1):
                matrix_text.tag_add("highlight_col", f"{i}.{start_col}", f"{i}.{end_col}")
            matrix_text.tag_config("highlight_row", background="lightblue")
            matrix_text.tag_config("highlight_col", background="lightblue")

    def unhighlight_matrix(self, event=None):
        # Remove any existing highlighting in both matrices
        for matrix_text in [self.matrix_text_x, self.matrix_text_y]:
            matrix_text.tag_remove("highlight_row", "1.0", tk.END)
            matrix_text.tag_remove("highlight_col", "1.0", tk.END)
      
    def apply_interpolation_to_line(self, percentage, connection):
        if percentage == 0:
            return
        #self.undo_last_action()
        
        self.canvas.delete(self.line_objects[-1])
        self.line_objects.pop()
        self.action_history.pop()

        if connection in self.connections:
            start_dot, end_dot = connection
            start_x, start_y = self.dots[start_dot]
            end_x, end_y = self.dots[end_dot]

            distance = ((end_x - start_x)**2 + (end_y - start_y)**2)**0.5
            max_dots = int(distance / (2 * self.dot_radius)) - 1
            num_points_to_show = int(max_dots * percentage / 100)

            # Remove the original connection
            self.connections.remove(connection)

            # List to store the newly created dot IDs
            new_dot_ids = []

            for i in range(1, num_points_to_show + 1):
                inter_x = start_x + (end_x - start_x) * (i / (num_points_to_show + 1))
                inter_y = start_y + (end_y - start_y) * (i / (num_points_to_show + 1))
                if not self.is_overlapping(inter_x, inter_y):
                    interpolated_dot_id = self.create_dot(inter_x, inter_y, color="gray")
                    new_dot_ids.append(interpolated_dot_id)
                    if connection not in self.interpolated_dot_ids:
                        self.interpolated_dot_ids[connection] = set()
                    self.interpolated_dot_ids[connection].add(interpolated_dot_id)
            # Create new connections
            line_color = self.get_rainbow_color(len(self.line_objects), 20)
            all_dots = [start_dot] + new_dot_ids + [end_dot]
            for i in range(len(all_dots) - 1):
                line_id=self.canvas.create_line(*self.dots[all_dots[i]], *self.dots[all_dots[i + 1]], fill=line_color, smooth=True, width=3, arrow=tk.LAST)
                self.line_objects.append(line_id)
                self.connections.append((all_dots[i], all_dots[i + 1]))
                self.action_history.append(('line', line_id))

        self.intepretedpath.append((connection,percentage))

    def clear_interpolated_dots(self, connection):
        if connection in self.interpolated_dot_ids:
            for dot_id in self.interpolated_dot_ids[connection]:
                self.canvas.delete(dot_id)
            del self.interpolated_dot_ids[connection]

    def erase(self):
        for dot in self.dot_objects:
            self.canvas.delete(dot)  # Remove each dot
        for line in self.line_objects:
            self.canvas.delete(line)  # Remove each line
        for connection, interpolated_dots in self.interpolated_dot_ids.items():
            for dot in interpolated_dots:
                self.canvas.delete(dot)  # Remove each interpolated dot
        self.dots.clear()
        self.connections.clear()
        self.dot_objects.clear()
        self.line_objects.clear()
        self.interpolated_dot_ids.clear()
        self.action_history.clear()
        self.update_adjacency_matrix()

    def pubmit(self):
        print("Dot Locations:")
        for dot_id, (x, y) in self.dots.items():
            print(f"Dot {dot_id}: ({x}, {y})")

        print("\nConnections:")
        for start_dot, end_dot in self.connections:
            print(f"Dot {start_dot} -> Dot {end_dot}")

    def toggle_single_process_mode(self):
        self.single_process_mode = not self.single_process_mode
        button_text = "Single Process Mode ON" if self.single_process_mode else "Single Process Mode OFF"
        self.toggle_mode_button.config(text=button_text)
        self.erase()

    def toggle_no_skipping_mode(self):
        self.no_skipping_mode = not self.no_skipping_mode
        button_text = "Skipping Mode ON" if self.no_skipping_mode else "Skipping Mode OFF"
        self.toggle_no_skipping_button.config(text=button_text)

    def draw_canvas_state(self, dots, connections, canvas_size, step):
        image = Image.open(self.image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # Keep track of the latest color for each dot
        dot_colors = {dot_id: 'white' for dot_id in dots}  # Start with black

        # Draw connections up to the current step with color
        for i, (start_dot, end_dot) in enumerate(connections[:step]):
            start_x, start_y = dots[start_dot]
            end_x, end_y = dots[end_dot]
            line_color = self.get_rainbow_color(i, len(connections))

            # Update dot colors to the current line color
            dot_colors[start_dot] = line_color
            dot_colors[end_dot] = line_color

            draw.line((start_x, start_y, end_x, end_y), fill=line_color, width=2)

        # Draw dots with their latest color
        for dot_id, (x, y) in dots.items():
            dot_color = dot_colors[dot_id]
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=dot_color)
        return image

    def create_frames(self):
        self.all_frames.clear()
        total_steps = 9  # The number of steps for each line

        for start_dot, end_dot in self.connections:
            if start_dot not in self.dots or end_dot not in self.dots:
                print(f"Invalid connection: {start_dot} to {end_dot}")
                continue  # Skip invalid connections
            line_dist = self.line_length(start_dot, end_dot)
            for step in range(total_steps + 1):
                # Calculate step increment based on line length
                step_increment = (line_dist / total_steps) * step
                self.add_frame_for_step(start_dot, end_dot, step_increment)

    def add_frame_for_step(self, start_dot, end_dot, step_increment):
        image = Image.open(self.image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # Draw all previous connections completely
        for i, (prev_start, prev_end) in enumerate(self.connections):
            if prev_start == start_dot and prev_end == end_dot:
                break  # Stop when reaching the current connection
            self.draw_complete_line(draw, prev_start, prev_end, i)

        # Calculate the partial endpoint for the current connection
        start_x, start_y = self.dots[start_dot]
        end_x, end_y = self.dots[end_dot]
        line_length = self.line_length(start_dot, end_dot)

        if line_length != 0:
            ratio = step_increment / line_length
            partial_end_x = start_x + (end_x - start_x) * ratio
            partial_end_y = start_y + (end_y - start_y) * ratio
            current_color_index = self.connections.index((start_dot, end_dot))

            # Pass coordinates to draw_partial_line
            self.draw_partial_line(draw, (start_x, start_y), (partial_end_x, partial_end_y), current_color_index)

        self.all_frames.append(image)

    def draw_complete_line(self, draw, start_dot, end_dot, color_index):
        start_x, start_y = self.dots[start_dot]
        end_x, end_y = self.dots[end_dot]
        line_color = self.get_rainbow_color(color_index, len(self.connections))
        draw.line((start_x, start_y, end_x, end_y), fill=line_color, width=3)

    def draw_partial_line(self, draw, start_coords, end_coords, color_index):
        line_color = self.get_rainbow_color(color_index, len(self.connections))
        draw.line((start_coords[0], start_coords[1], end_coords[0], end_coords[1]), fill=line_color, width=3)

    def draw_partial_connection(self, draw, start_dot, end_dot, line_color, step):
        start_x, start_y = self.dots[start_dot]
        end_x, end_y = self.dots[end_dot]
        line_length = self.line_length(start_dot, end_dot)

        if line_length != 0:
            ratio = step / self.total_steps
            partial_end_x = start_x + (end_x - start_x) * ratio
            partial_end_y = start_y + (end_y - start_y) * ratio
            draw.line((start_x, start_y, partial_end_x, partial_end_y), fill=line_color, width=2)

        # Update the color of the start dot
        if step > 0:  # Change color after the first step
            self.update_dot_color(draw, start_dot, line_color)

    def update_dot_color(self, draw, dot_id, color):
        x, y = self.dots[dot_id]
        draw.ellipse((x - self.dot_radius, y - self.dot_radius, x + self.dot_radius, y + self.dot_radius), fill=color, outline='white')

    def draw_connection_step(self, connection_index, step):
        image = Image.open(self.image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # Draw all dots initially in white
        for dot_id, (x, y) in self.dots.items():
            draw.ellipse((x - self.dot_radius, y - self.dot_radius, x + self.dot_radius, y + self.dot_radius), fill='white', outline='white')

        # Draw all previous connections completely and update dot colors
        for i, (prev_start, prev_end) in enumerate(self.connections[:connection_index]):
            line_color = self.get_rainbow_color(i, len(self.connections))
            self.draw_complete_line(draw, prev_start, prev_end, i)
            self.update_dot_color(draw, prev_start, line_color)
            self.update_dot_color(draw, prev_end, line_color)

        # Draw the current connection partially
        if connection_index < len(self.connections):
            current_line_color = self.get_rainbow_color(connection_index, len(self.connections))
            start_dot, end_dot = self.connections[connection_index]
            self.draw_partial_connection(draw, start_dot, end_dot, current_line_color, step)

            # Update start dot color immediately
            self.update_dot_color(draw, start_dot, current_line_color)

            # Update end dot color when the line reaches it
            if connection_index < len(self.connections) and step == self.total_steps - 1:
                self.update_dot_color(draw, end_dot, current_line_color)

        return image

    def save_gif(self, ms_per_frame):
        current_time = datetime.datetime.now().strftime("%M%S")
        gif_path = f"static_visualization_{ms_per_frame}_{current_time}.gif"
        self.images[0].save(gif_path, save_all=True, append_images=self.images[1:], duration=ms_per_frame, loop=0)
        messagebox.showinfo("Saved", f"GIF saved at {gif_path}")

    def save_animated_gif(self, frames, ms_per_frame):
        current_time = datetime.datetime.now().strftime("%M%S")
        gif_path = f"animated_lines_{ms_per_frame}_{current_time}.gif"
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=ms_per_frame, loop=0)
        messagebox.showinfo("Saved", f"GIF saved at {gif_path}")

    def create_static_image(self):
        self.images.clear()
        # Use your existing logic to create a static image
        # This can be similar to the 'draw_canvas_state' method
        # For example:
        for step in range(len(self.connections) + 1):
            img = self.draw_canvas_state(self.dots, self.connections, (self.canvas_width, self.canvas_height), step)
            self.images.append(img)
        
        # Create a new window for the GIF
        gif_window = tk.Toplevel(self.master)
        gif_window.title("GIF Preview")

        gif_label = tk.Label(gif_window)
        gif_label.pack()

        # Slider for adjusting frame speed
        speed_scale = tk.Scale(gif_window, from_=0, to=2000, orient="horizontal", label="Interval (ms)")
        speed_scale.set(1000)  # Default value
        speed_scale.pack()

        # Function to update GIF frames
        def update_gif(index=0):
            frame_speed = speed_scale.get()
            frame = ImageTk.PhotoImage(image=self.images[index])
            gif_label.config(image=frame)
            gif_label.image = frame
            index = (index + 1) % len(self.images)
            gif_window.after(frame_speed, update_gif, index)

        update_gif()  # Start the GIF

        # Add a button to save the GIF
        save_button = tk.Button(gif_window, text="Save GIF", command=lambda: self.save_gif(speed_scale.get()))
        save_button.pack()

    def submit(self):
        if self.animate_lines_var.get() == 1:
            # Set up the window for animation
            self.setup_animation_window()
        else:
            # Create and show a static image
            self.create_static_image()

    def play_animation(self, gif_label, speed_scale, frame_index, current_connection_index):
        total_time_per_line = speed_scale.get()  # Total time to draw each line in ms

        if current_connection_index < len(self.connections):
            # Calculate the actual frame index for the current connection
            actual_frame_index = frame_index % self.total_steps

            # Display the frame for the current connection step
            frame_image = self.draw_connection_step(current_connection_index, actual_frame_index)
            frame = ImageTk.PhotoImage(image=frame_image)
            gif_label.config(image=frame)
            gif_label.image = frame

            # Prepare for the next frame
            next_frame_index = frame_index + 1
            if actual_frame_index == self.total_steps - 1:
                # Move to the next connection after completing the current one
                next_connection_index = current_connection_index + 1
            else:
                next_connection_index = current_connection_index

            # Calculate delay for each step
            self.step_delay = total_time_per_line // self.total_steps
            gif_label.after(self.step_delay, lambda: self.play_animation(gif_label, speed_scale, next_frame_index, next_connection_index))
        else:
            # Restart the animation once all connections are drawn
            self.play_animation(gif_label, speed_scale, 0, 0)

    def setup_animation_window(self):
        
        gif_window = tk.Toplevel(self.master)
        gif_window.title("GIF Animation")

        gif_label = tk.Label(gif_window)
        gif_label.pack()

        speed_scale = tk.Scale(gif_window, from_=50, to=2000, orient="horizontal", label="Interval (ms)")
        speed_scale.set(1000)
        speed_scale.pack()

        self.create_frames()  # Call a function to create all frames
        self.play_animation(gif_label, speed_scale,0 ,0)  # Start playing the animation

        save_button = tk.Button(gif_window, text="Save GIF", command=lambda: self.save_animated_gif(self.all_frames, self.step_delay))
        save_button.pack()

    def on_mouse_down(self, event):
        clicked_dot = self.find_nearest_dot(event.x, event.y)

        if clicked_dot is None:
            self.current_dot = self.create_dot(event.x, event.y)
        else:
            if not self.single_process_mode or not self.connections or clicked_dot == self.connections[-1][1]:
                self.current_dot = clicked_dot
            else:
                self.current_dot = None

    def on_mouse_move(self, event):
        self.dragging = True

    def on_mouse_up(self, event):
        if self.dragging and self.current_dot is not None:
            end_dot = self.find_nearest_dot(event.x, event.y)
            if end_dot and end_dot != self.current_dot and ( self.is_line_in_white_space(*self.dots[self.current_dot], *self.dots[end_dot]) or self.no_skipping_mode ):
                # Draw the line
                start_x, start_y = self.dots[self.current_dot]
                end_x, end_y = self.dots[end_dot]
                line_color = self.get_rainbow_color(len(self.line_objects), 20)
                line_id = self.canvas.create_line(start_x, start_y, end_x, end_y, fill=line_color, smooth=True, width=3, arrow=tk.LAST)
                self.line_objects.append(line_id)
                self.connections.append((self.current_dot, end_dot))
                self.action_history.append(('line', line_id))
                self.canvas.itemconfig(self.current_dot, fill=line_color, outline=line_color)
                self.canvas.itemconfig(end_dot, fill=line_color, outline=line_color)
                # Calculate and store potential interpolation points for this line
                percentage = float(self.interpolate_entry.get())  # Get current percentage
                self.apply_interpolation_to_line(percentage, self.connections[-1])
        self.dragging = False
        self.current_dot = None
        # Update the display
        self.update_adjacency_matrix()
        self.update_display()

    def find_nearest_dot(self, x, y):
        for dot_id, (dot_x, dot_y) in self.dots.items():
            if (x - dot_x) ** 2 + (y - dot_y) ** 2 <= (2 * self.dot_radius) ** 2:
                return dot_id
        return None

    def get_rainbow_color(self, index, total):
        """Get a color from the rainbow spectrum based on the index."""
        hue = index / total
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)  # Convert HSV to RGB
        return '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
    
    def undo_last_action(self): 
        if self.action_history:
            action, item_id = self.action_history.pop()

            if action == 'dot':
                # Undo dot creation
                self.canvas.delete(item_id)
                del self.dots[item_id]
                self.dot_objects.remove(item_id)

                # Remove any connections involving this dot
                self.connections = [(start, end) for start, end in self.connections if start != item_id and end != item_id]

            elif action == 'line':
                # Undo line creation
                self.canvas.delete(item_id)
                self.line_objects.remove(item_id)
                self.connections.pop()
            self.update_adjacency_matrix()

    def line_length(self, start_dot, end_dot):
        start_x, start_y = self.dots[start_dot]
        end_x, end_y = self.dots[end_dot]
        return math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)

root = tk.Tk()
import os

# Get the current working directory
current_dir = os.getcwd()

# Construct the relative file path to the image
image_path = os.path.join(current_dir, 'bodytemplate.png')
app = AnnotationInterface(root, image_path)
root.mainloop()
