import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np
import random

class Tile:
    def __init__(self, image_data, correct_r, correct_c):
        # OOP Encapsulation: Keeping data and state together
        self.image_data = image_data
        self.correct_pos = (correct_r, correct_c)
        self.current_pos = (correct_r, correct_c)
        self.rotation = 0  # 0, 90, 180, 270 degrees
        self.flipped = False  # Horizontal flip

    def get_current_image(self):
        # Apply current transformations to the tile's image
        img = self.image_data.copy()
        if self.flipped:
            img = cv2.flip(img, 1)
        if self.rotation == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif self.rotation == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return img

    def is_correct(self):
        return self.current_pos == self.correct_pos and self.rotation == 0 and not self.flipped

class PuzzleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Puzzle Game")
        self.root.geometry("1100x700")

        self.grid_size = tk.IntVar(value=3)
        self.tiles = []
        self.original_img_cv = None
        
        # Game states
        self.moves = 0
        self.hints_left = 3
        self.hint_tile = None
        self.selected_tile = None
        self.game_over = False
        self.target_size = 420
        
        self.setup_ui()

    def setup_ui(self):
        # Top Control Frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=20)

        tk.Button(control_frame, text="Load Image", command=self.load_image, bg="lightblue").pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(control_frame, text="3x3", variable=self.grid_size, value=3).pack(side=tk.LEFT)
        tk.Radiobutton(control_frame, text="4x4", variable=self.grid_size, value=4).pack(side=tk.LEFT)
        tk.Radiobutton(control_frame, text="5x5", variable=self.grid_size, value=5).pack(side=tk.LEFT)

        # Status and Tools[cite: 2, 3]
        self.moves_label = tk.Label(control_frame, text="Moves: 0", font=("Arial", 12, "bold"))
        self.moves_label.pack(side=tk.LEFT, padx=20)
        
        self.incorrect_label = tk.Label(control_frame, text="Incorrect: 0", font=("Arial", 12, "bold"), fg="red")
        self.incorrect_label.pack(side=tk.LEFT, padx=20)

        self.solve_btn = tk.Button(control_frame, text="Solve", command=self.solve_puzzle, state=tk.DISABLED, bg="lightgreen")
        self.solve_btn.pack(side=tk.RIGHT, padx=10)

        self.hint_btn = tk.Button(control_frame, text="Hint (3)", command=self.use_hint, state=tk.DISABLED, bg="khaki")
        self.hint_btn.pack(side=tk.RIGHT, padx=10)

        # Images Frame
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.original_canvas = tk.Canvas(self.image_frame, width=450, height=450, bg="gray")
        self.original_canvas.pack(side=tk.LEFT, padx=20, pady=20)

        self.puzzle_canvas = tk.Canvas(self.image_frame, width=450, height=450, bg="lightgray")
        self.puzzle_canvas.pack(side=tk.RIGHT, padx=20, pady=20)

        # Event Bindings[cite: 2]
        self.puzzle_canvas.bind("<Button-1>", self.on_left_click)
        self.puzzle_canvas.bind("<Button-3>", self.on_right_click)
        self.puzzle_canvas.bind("<Shift-Button-1>", self.on_shift_left_click)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.bmp")])
        if not file_path:
            return
        
        img = cv2.imread(file_path)
        if img is None:
            messagebox.showerror("Error", "Could not load image.")
            return
            
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Reset game state for new image[cite: 2]
        self.moves = 0
        self.hints_left = 3
        self.hint_tile = None
        self.selected_tile = None
        self.game_over = False
        self.update_status()
        self.hint_btn.config(text=f"Hint ({self.hints_left})", state=tk.NORMAL)
        self.solve_btn.config(state=tk.NORMAL)

        # Process and Scramble[cite: 1, 2]
        img = cv2.resize(img, (self.target_size, self.target_size))
        self.original_img_cv = img.copy()
        grid = self.grid_size.get()
        self.tile_size = self.target_size // grid
        self.tiles = []

        for r in range(grid):
            for c in range(grid):
                y, x = r * self.tile_size, c * self.tile_size
                tile_crop = img[y:y+self.tile_size, x:x+self.tile_size]
                self.tiles.append(Tile(tile_crop, r, c))

        self.display_original()
        self.scramble_puzzle()
        self.render_puzzle()

    def scramble_puzzle(self):
        grid = self.grid_size.get()
        # Scale transformations: 6 for 3x3, 12 for 4x4, 20 for 5x5[cite: 2]
        num_transforms = {3: 6, 4: 12, 5: 20}.get(grid, 6)
        
        # Ensure no tile is targeted twice during initial scramble[cite: 2]
        available_tiles = self.tiles.copy()
        random.shuffle(available_tiles)

        for _ in range(num_transforms):
            if not available_tiles:
                break
                
            action = random.choice(["swap", "rotate", "flip"])
            
            if action == "swap" and len(available_tiles) >= 2:
                t1 = available_tiles.pop()
                t2 = available_tiles.pop()
                t1.current_pos, t2.current_pos = t2.current_pos, t1.current_pos
            elif action != "swap" and len(available_tiles) >= 1:
                t = available_tiles.pop()
                if action == "rotate":
                    t.rotation = random.choice([90, 180, 270])
                else:
                    t.flipped = True

    def display_original(self):
        img_pil = Image.fromarray(self.original_img_cv)
        self.original_tk = ImageTk.PhotoImage(image=img_pil)
        self.original_canvas.delete("all")
        self.original_canvas.create_image(225, 225, image=self.original_tk)

    def render_puzzle(self):
        if not self.tiles: return
        grid = self.grid_size.get()
        
        # Reassemble image[cite: 2]
        puzzle_img = np.zeros((self.target_size, self.target_size, 3), dtype=np.uint8)
        
        for tile in self.tiles:
            r, c = tile.current_pos
            y, x = r * self.tile_size, c * self.tile_size
            puzzle_img[y:y+self.tile_size, x:x+self.tile_size] = tile.get_current_image()

        img_pil = Image.fromarray(puzzle_img)
        self.puzzle_tk = ImageTk.PhotoImage(image=img_pil)
        self.puzzle_canvas.delete("all")
        
        # Center the 420x420 image in the 450x450 canvas
        offset = (450 - self.target_size) // 2
        self.puzzle_canvas.create_image(offset, offset, anchor=tk.NW, image=self.puzzle_tk)

        # Draw Faint Grid & Overlays[cite: 2]
        for i in range(1, grid):
            coord = offset + i * self.tile_size
            self.puzzle_canvas.create_line(offset, coord, offset + self.target_size, coord, fill="gray", dash=(4, 4))
            self.puzzle_canvas.create_line(coord, offset, coord, offset + self.target_size, fill="gray", dash=(4, 4))

        incorrect_count = 0
        for tile in self.tiles:
            r, c = tile.current_pos
            px = offset + c * self.tile_size
            py = offset + r * self.tile_size
            
            if tile.is_correct():
                # Draw green tick[cite: 2]
                self.puzzle_canvas.create_text(px + 15, py + 15, text="✔", fill="green", font=("Arial", 16, "bold"))
            else:
                incorrect_count += 1
                
            # Selection Highlight[cite: 2]
            if self.selected_tile == tile:
                self.puzzle_canvas.create_rectangle(px, py, px+self.tile_size, py+self.tile_size, outline="red", width=3)
                
        # Draw Hint
        if self.hint_tile:
            # Blue circle on Puzzle
            hr, hc = self.hint_tile.current_pos
            hx = offset + hc * self.tile_size + self.tile_size//2
            hy = offset + hr * self.tile_size + self.tile_size//2
            self.puzzle_canvas.create_oval(hx-15, hy-15, hx+15, hy+15, outline="blue", width=4)
            
            # Blue circle on Original
            or_r, or_c = self.hint_tile.correct_pos
            ox = offset + or_c * self.tile_size + self.tile_size//2
            oy = offset + or_r * self.tile_size + self.tile_size//2
            self.original_canvas.create_oval(ox-15, oy-15, ox+15, oy+15, outline="blue", width=4)

        self.incorrect_label.config(text=f"Incorrect: {incorrect_count}")
        
        # Check Win[cite: 2]
        if incorrect_count == 0 and not self.game_over:
            self.game_over = True
            self.hint_btn.config(state=tk.DISABLED)
            self.solve_btn.config(state=tk.DISABLED)
            messagebox.showinfo("Congratulations!", f"Puzzle Solved in {self.moves} moves!")

    def get_clicked_tile(self, event):
        if self.game_over: return None
        offset = (450 - self.target_size) // 2
        c = (event.x - offset) // self.tile_size
        r = (event.y - offset) // self.tile_size
        grid = self.grid_size.get()
        if 0 <= r < grid and 0 <= c < grid:
            for tile in self.tiles:
                if tile.current_pos == (r, c):
                    return tile
        return None

    def register_move(self):
        self.moves += 1
        self.moves_label.config(text=f"Moves: {self.moves}")
        self.hint_tile = None # Clear hint on next move
        self.display_original() # Clear hint from original canvas
        self.render_puzzle()

    def on_left_click(self, event):
        tile = self.get_clicked_tile(event)
        if not tile: return
        
        if self.selected_tile is None:
            self.selected_tile = tile # Select[cite: 2]
            self.render_puzzle()
        elif self.selected_tile == tile:
            self.selected_tile = None # Deselect[cite: 2]
            self.render_puzzle()
        else:
            # Swap[cite: 2]
            self.selected_tile.current_pos, tile.current_pos = tile.current_pos, self.selected_tile.current_pos
            self.selected_tile = None
            self.register_move()

    def on_right_click(self, event):
        tile = self.get_clicked_tile(event)
        if tile:
            tile.rotation = (tile.rotation + 90) % 360 # Rotate clockwise[cite: 2]
            self.selected_tile = None
            self.register_move()

    def on_shift_left_click(self, event):
        tile = self.get_clicked_tile(event)
        if tile:
            tile.flipped = not tile.flipped # Flip horizontal[cite: 2]
            self.selected_tile = None
            self.register_move()

    def update_status(self):
        self.moves_label.config(text=f"Moves: {self.moves}")

    def use_hint(self):
        if self.hints_left > 0 and not self.game_over:
            incorrect_tiles = [t for t in self.tiles if not t.is_correct()]
            if incorrect_tiles:
                self.hint_tile = random.choice(incorrect_tiles)
                self.hints_left -= 1
                self.hint_btn.config(text=f"Hint ({self.hints_left})")
                if self.hints_left == 0:
                    self.hint_btn.config(state=tk.DISABLED)
                self.render_puzzle() # Marks tile with blue circle[cite: 3]

    def solve_puzzle(self):
        if self.game_over: return
        for tile in self.tiles:
            tile.current_pos = tile.correct_pos
            tile.rotation = 0
            tile.flipped = False
        self.moves = 0
        self.update_status()
        self.hint_tile = None
        self.selected_tile = None
        self.display_original()
        self.render_puzzle() # Instantly solves and clears score[cite: 3]

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleGame(root)
    root.mainloop()