import os
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import google.generativeai as genai
from dotenv import load_dotenv

class HandwrittenTextExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Handwritten Text Extractor")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Load API key from .env file
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            messagebox.showwarning("API Key Missing", "GEMINI_API_KEY not found in .env file.")
        
        self.selected_image_path = None
        self.setup_ui()
        
    def setup_ui(self):
        # Image selection and display area
        self.img_frame = tk.Frame(self.root)
        self.img_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Button frame
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack(fill=tk.X, padx=20)
        
        self.select_btn = tk.Button(btn_frame, text="Select Image", command=self.select_image)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        self.extract_btn = tk.Button(btn_frame, text="Extract Text", command=self.extract_text)
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        self.extract_btn.config(state=tk.DISABLED)
        
        # Result text area
        result_frame = tk.Frame(self.root)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(result_frame, text="Extracted Text:").pack(anchor=tk.W)
        
        self.result_text = tk.Text(result_frame, height=10, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if file_path:
            self.selected_image_path = file_path
            self.display_image(file_path)
            self.extract_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Image selected: {os.path.basename(file_path)}")
    
    def display_image(self, image_path):
        # Clear previous image
        for widget in self.img_frame.winfo_children():
            widget.destroy()
        
        # Open and resize image for display
        img = Image.open(image_path)
        
        # Calculate aspect ratio to fit in frame
        width, height = img.size
        max_width = 500
        max_height = 300
        
        if width > max_width or height > max_height:
            ratio = min(max_width/width, max_height/height)
            width = int(width * ratio)
            height = int(height * ratio)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        # Keep a reference to prevent garbage collection
        self.photo = photo
        
        # Display image
        img_label = tk.Label(self.img_frame, image=photo)
        img_label.pack(pady=10)
    
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_text(self):
        if not self.selected_image_path:
            messagebox.showerror("Error", "Please select an image first")
            return
        
        if not self.api_key:
            messagebox.showerror("Error", "GEMINI_API_KEY not found in .env file")
            return
        
        self.status_var.set("Processing image...")
        self.root.update()
        
        try:
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            
            # Initialize the model
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Encode the image
            image_data = self.encode_image(self.selected_image_path)
            
            # Create the prompt for the API
            prompt = "Extract all handwritten text from this image. Return ONLY the extracted text without any explanations or additional commentary."
            
            # Prepare the content with the image
            contents = [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": f"image/{os.path.splitext(self.selected_image_path)[1][1:]}",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
            
            # Make the API call
            response = model.generate_content(contents=contents)
            
            # Update the result text
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, response.text)
            
            self.status_var.set("Text extraction completed")
            
        except Exception as e:
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HandwrittenTextExtractor(root)
    root.mainloop()