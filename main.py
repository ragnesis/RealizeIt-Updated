from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QFrame, QLabel, QColorDialog
)
from PyQt5.QtCore import Qt, QPoint, QByteArray, QBuffer
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QImage, QColor
import numpy as np
import random
import requests
from io import BytesIO

class DrawingBoard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white; border: 2px solid #aaa;")
        self.setFixedSize(750, 750)
        
        # Initialize drawing state
        self.drawing = False
        self.last_point = QPoint()
        self.brush_color = QColor(0, 0, 0)  # Default black
        self.brush_size = 5
        self.eraser_mode = False  # Flag to track if eraser is active

        # Store drawn paths
        self.paths = []
        self.undone_paths = []  # Stack for undone paths
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            if self.eraser_mode:
                self.erase_path(event.pos())  # Erase any path at the initial point

    def mouseMoveEvent(self, event):
        if self.drawing:
            if self.eraser_mode:
                self.erase_path(event.pos())  # Erase paths while moving the mouse
            else:
                path = (self.last_point, event.pos(), self.brush_color, self.brush_size)
                self.paths.append(path)
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        for start, end, color, size in self.paths:
            painter.setPen(QPen(color, size, Qt.SolidLine))
            painter.drawLine(start, end)

    def set_eraser_mode(self, active: bool):
        """Set whether the eraser tool is active."""
        self.eraser_mode = active

    def erase_path(self, pos: QPoint):
        """Erase paths that are close to the position."""
        self.paths = [path for path in self.paths if not self.is_near_path(path, pos)]

    def is_near_path(self, path, pos: QPoint):
        """Check if the mouse position is close to any of the paths drawn."""
        start, end, _, _ = path
        return (start - pos).manhattanLength() < self.brush_size or (end - pos).manhattanLength() < self.brush_size

    def clear(self):
        """Clear the drawing board."""
        self.paths.clear()
        self.undone_paths.clear()
        self.update()

    def undo(self):
        """Undo the last action."""
        if self.paths:
            path = self.paths.pop()
            self.undone_paths.append(path)
            self.update()

    def redo(self):
        """Redo the last undone action."""
        if self.undone_paths:
            path = self.undone_paths.pop()
            self.paths.append(path)
            self.update()

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Realize It")
        self.setGeometry(100, 100, 1200, 800)

        # Main container widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        main_layout = QVBoxLayout(main_widget)

        # Initialize the drawing board first
        self.drawing_board = DrawingBoard(self)  # Initialize drawing board here

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Content Layout
        content_layout = QHBoxLayout()

        # Left Toolbar
        self.left_toolbar = self.create_toolbar(["Brush", "Eraser", "Zoom", "Pan", "Slider"])
        content_layout.addWidget(self.left_toolbar)

        # Work Area
        work_area = self.create_work_area()
        content_layout.addLayout(work_area)

        # Right Toolbar
        self.right_toolbar = self.create_toolbar(["Sky", "Cloud", "Mountain", "Land", "Water", "Tree"], side="right")
        content_layout.addWidget(self.right_toolbar)

        # Define colors for materials (Sky, Land, Cloud, etc.)
        self.material_colors = {
            "Sky": QColor(102, 255, 255),  # Light cyan for Sky
            "Cloud": QColor(169, 169, 169),  # Light gray for Cloud
            "Mountain": QColor(153, 102, 51),  # Brown for Mountain
            "Land": QColor(0, 255, 0),  # Light Green for Land
            "Water": QColor(0, 102, 255),  # Deep Sky Blue for Water
            "Tree": QColor(34, 139, 34)  # Dark Green for Tree
        }
        # Set default material color for brush (Sky)
        self.drawing_board.brush_color = self.material_colors["Sky"]

        main_layout.addLayout(content_layout)

        # Assuming you are using a QLabel for status updates
        self.status_label = QLabel(self)
        self.status_label.setText("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Optionally, set the size and position of the status label
        self.status_label.setGeometry(10, 10, 300, 30)  # Adjust as needed

        # You can also style the label (optional)
        self.status_label.setStyleSheet("color: blue; font-size: 14px;")


    def create_header(self):
        header = QWidget()
        header.setStyleSheet("background-color: #444;")
        header.setFixedHeight(70)

        header_layout = QHBoxLayout(header)
        header_layout.setSpacing(15)

        # Define buttons
        buttons = ["Save", "Undo", "Redo", "Help", "Generate", "Quit"]
        for button_text in buttons:
            button = QPushButton(button_text)
            button.setStyleSheet(self.button_styles())
            if button_text == "Quit":
                button.clicked.connect(self.close)
            elif button_text == "Undo":
                button.clicked.connect(self.drawing_board.undo)  # Connect Undo button
            elif button_text == "Redo":
                button.clicked.connect(self.drawing_board.redo)  # Connect Redo button
            elif button_text == "Generate":
                button.clicked.connect(self.handle_generate_click)  # Connect Generate button
            header_layout.addWidget(button)

        return header

    def create_toolbar(self, items, side="left"):
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #333;")
        toolbar.setFixedWidth(115 if side == "right" else 80)

        layout = QVBoxLayout(toolbar)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)

        # Create buttons for toolbar
        buttons = {}
        for item in items:
            button = QPushButton(item)
            button.setCheckable(True)  # Make the button toggleable
            button.setStyleSheet(self.button_styles(checkable=True))
            button.clicked.connect(lambda checked, button=item: self.handle_button_click(button, side))
            buttons[item] = button
            layout.addWidget(button)

        # Set default button for left toolbar (Brush) and right toolbar (Sky)
        if side == "left":
            buttons["Brush"].setChecked(True)  # Brush is selected by default
        elif side == "right":
            buttons["Sky"].setChecked(True)  # Sky is selected by default

        return toolbar

    def create_work_area(self):
        work_area_layout = QHBoxLayout()

        # Rendering Canvas
        rendering_canvas = QFrame()
        rendering_canvas.setStyleSheet("background-color: #999; border: 2px solid #aaa;")
        rendering_canvas.setFixedSize(750, 750)
        rendering_canvas_label = QLabel("Rendering Canvas", rendering_canvas)
        rendering_canvas_label.setAlignment(Qt.AlignCenter)

        # Add to layout
        # Add the drawing board first (left)
        work_area_layout.addWidget(self.drawing_board, stretch=2)  # Add drawing board to work area first

        work_area_layout.addWidget(rendering_canvas, stretch=2)

        return work_area_layout

    def handle_button_click(self, button_name, side):
        """Ensure only one button is active at a time in the toolbar."""
        # Select the appropriate toolbar based on the side
        if side == "left":
            toolbar = self.left_toolbar
        else:
            toolbar = self.right_toolbar

        # Deselect all other buttons in the toolbar
        for button in toolbar.findChildren(QPushButton):
            if button.text() != button_name:
                button.setChecked(False)

        # Handle eraser button toggle
        if button_name == "Eraser":
            self.drawing_board.set_eraser_mode(True)
        else:
            self.drawing_board.set_eraser_mode(False)

        # If a material is selected, update brush color
        if button_name in self.material_colors:
            self.drawing_board.brush_color = self.material_colors[button_name]

    def handle_generate_click(self):
        """Handle the generate button click and generate the mask image."""
        print("Generate button clicked!")
        
        # Update UI to show that the process is starting
        self.status_label.setText("Generating mask image...")
        
        try:
            # Capture the current canvas as a QPixmap (from the drawing board specifically)
            pixmap = self.drawing_board.grab()
            
            # Convert QPixmap to QImage
            image = pixmap.toImage()
            
            # Check if image is valid
            if image.isNull():
                raise Exception("Captured image is null!")
            
            print(f"Image captured with size {image.width()}x{image.height()}")
            
            # Create a simplified mask image where each material is represented by a distinct color
            mask_image = self.create_mask_image(image)
            
            # Save the mask image to a file (for debugging purposes)
            mask_image.save("mask_image.png")
            
            print("Mask image generated and saved as mask_image.png")
            
            # Now generate the prompt based on the mask
            prompt = self.generate_prompt(mask_image)
            print(prompt)

            # Update UI to indicate success
            self.status_label.setText("Mask image generated successfully!")

            # Send the image to the API (DeepAI Image Generation API example)
            api_key = "Enter_your_Key_here"
            response = self.send_prompt_to_api(prompt, api_key)

            if response and response.status_code == 200:
                # Handle response (for example, display the generated image)
                generated_image_url = response.json().get("output_url")
                print("Generated Image URL:", generated_image_url)
                # Show the generated image on the rendering canvas
                self.display_generated_image(generated_image_url)
                self.status_label.setText("Generated image received successfully!")
            else:
                raise Exception("Failed to generate image via API.")
            
        except Exception as e:
            # Handle any errors during the process
            print(f"Error generating mask image: {e}")
            self.status_label.setText("Error generating mask image.")
        
    
    def send_prompt_to_api(self, prompt: str, api_key: str) -> requests.Response:
        """Send the prompt to the DeepAI API for text-to-image generation."""
        url = "https://api.stability.ai/v2/generation/stable-diffusion-2-1-768-v2-0-0/generate"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7.5,  # Adjust this for prompt adherence
            "clip_guidance_preset": "FAST_BLUE",  # Preset for quicker generation
            "height": 512,  # Image height (lower resolution for free credits)
            "width": 512,   # Image width
            "samples": 1,   # Number of images to generate
            "steps": 30     # Number of steps for generation
        }  # Send the generated prompt as 'text'
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response
            else:
                print(f"Error: Received status code {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error sending request to API: {e}")
            return None

    def generate_prompt(self, mask_image: QImage) -> str:
        """Generate a textual description based on the mask image."""
        width = mask_image.width()
        height = mask_image.height()
        
        # Dictionary to store counts of identified materials
        material_counts = {material: 0 for material in self.material_colors}
        
        # Process each pixel in the mask image
        for x in range(width):
            for y in range(height):
                color = mask_image.pixelColor(x, y)
                for material_name, material_color in self.material_colors.items():
                    if self.is_color_similar(color, material_color):
                        material_counts[material_name] += 1
                        break
        
        # Generate prompt based on identified materials
        prompt_parts = []
        
        # Define adjectives for each material
        material_adjectives = {
            "Sky": ["clear", "beautiful", "bright", "vast"],
            "Cloud": ["fluffy", "soft", "gathering", "wispy"],
            "Mountain": ["majestic", "rugged", "towering", "snow-capped"],
            "Land": ["lush", "fertile", "green", "expansive"],
            "Water": ["sparkling", "deep", "calm", "clear"],
            "Tree": ["tall", "green", "dense", "leafy"]
        }
        
        # Create prompt for each material with a random adjective
        for material, count in material_counts.items():
            if count > 0:
                adjective = random.choice(material_adjectives[material])
                prompt_parts.append(f"A {adjective} {material.lower()}")

        # If no materials are identified, return a generic description
        if not prompt_parts:
            prompt_parts.append("A surreal landscape with undefined features")
        
        # Combine parts into a full prompt and return
        return ", ".join(prompt_parts)
    
    def create_mask_image(self, image: QImage) -> QImage:
        """Create a simplified mask image."""
        # Convert QImage to numpy array for easier manipulation
        width = image.width()
        height = image.height()
        
        print(f"Creating mask image of size {width}x{height}")
        
        # Prepare the mask image (same size as the original)
        mask_image = QImage(width, height, QImage.Format_RGB888)
        mask_image.fill(QColor(255, 255, 255))  # Start with a white mask
        
        # Process each pixel
        for x in range(width):
            for y in range(height):
                color = image.pixelColor(x, y)
                # Check for color matching
                for material_name, material_color in self.material_colors.items():
                    if self.is_color_similar(color, material_color):
                        mask_image.setPixelColor(x, y, material_color)  # Set the pixel color based on material
                        break  # Exit the loop once the matching material is found
                        
        return mask_image
    
    def display_generated_image(self, image_url: str):
        """Display the generated image on the UI."""
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            self.rendering_canvas_label.setPixmap(pixmap)
            self.rendering_canvas_label.show()  # Ensure the label is shown
        else:
            print("Failed to load image from URL")
        

    def is_color_similar(self, color1: QColor, color2: QColor) -> bool:
        tolerance=30 # You can adjust this value for sensitivity
        """Check if two colors are similar within a tolerance."""
        return abs(color1.red() - color2.red()) < tolerance and \
           abs(color1.green() - color2.green()) < tolerance and \
           abs(color1.blue() - color2.blue()) < tolerance


    @staticmethod
    def button_styles(checkable=False):
        base_style = """
            QPushButton {
                background-color: #008CBA;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #006F8C;
            }
            QPushButton:pressed {
                background-color: #007B8B;
            }
        """
        if checkable:
            base_style += """
            QPushButton:checked {
                background-color: #005f6a;
            }
            """
        return base_style

if __name__ == '__main__':
    app = QApplication([])
    window = AppWindow()
    window.show()
    app.exec_()

