import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading

# Configure pytesseract path (you may need to adjust this for your system)
# For Windows users, uncomment and adjust the line below:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class HandwritingOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Handwriting to Text Converter")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")
        
        self.setup_ui()
        
        # Path to store the selected image
        self.image_path = None
        self.processed_image = None
        
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="Handwriting to Text Converter", 
                              font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Image frame
        self.image_frame = tk.LabelFrame(main_frame, text="Image Preview", 
                                        font=("Arial", 12), bg="#f0f0f0", padx=10, pady=10)
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.image_label = tk.Label(self.image_frame, bg="white", text="No image selected")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = tk.Frame(main_frame, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, pady=10)
        
        # Buttons
        self.select_btn = ttk.Button(control_frame, text="Select Image", command=self.select_image)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = ttk.Button(control_frame, text="Process Image", command=self.process_image)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        self.process_btn.config(state=tk.DISABLED)
        
        self.extract_btn = ttk.Button(control_frame, text="Extract Text", command=self.extract_text)
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        self.extract_btn.config(state=tk.DISABLED)
        
        self.save_btn = ttk.Button(control_frame, text="Save Text", command=self.save_text)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        self.save_btn.config(state=tk.DISABLED)
        
        # Processing options frame
        options_frame = tk.LabelFrame(main_frame, text="Processing Options", 
                                     font=("Arial", 12), bg="#f0f0f0", padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Preprocessing options
        tk.Label(options_frame, text="Preprocessing:", bg="#f0f0f0").grid(row=0, column=0, sticky=tk.W)
        
        self.preprocess_var = tk.StringVar(value="adaptive")
        options = [("Adaptive Threshold", "adaptive"), 
                   ("OTSU Threshold", "otsu"),
                   ("None", "none")]
        
        for i, (text, value) in enumerate(options):
            tk.Radiobutton(options_frame, text=text, variable=self.preprocess_var, 
                          value=value, bg="#f0f0f0").grid(row=0, column=i+1, padx=10)
        
        # Language options
        tk.Label(options_frame, text="Language:", bg="#f0f0f0").grid(row=1, column=0, sticky=tk.W)
        
        self.lang_var = tk.StringVar(value="eng")
        langs = [("English", "eng"), ("Math/Equations", "equ"), ("Multiple Languages", "eng+fra+deu+spa")]
        
        for i, (text, value) in enumerate(langs):
            tk.Radiobutton(options_frame, text=text, variable=self.lang_var, 
                          value=value, bg="#f0f0f0").grid(row=1, column=i+1, padx=10)
        
        # Text result frame
        text_frame = tk.LabelFrame(main_frame, text="Extracted Text", 
                                  font=("Arial", 12), bg="#f0f0f0", padx=10, pady=10)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                                 width=40, height=10, 
                                                 font=("Courier", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                             bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, 
                                      length=100, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
    
    def select_image(self):
        filetypes = [
            ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")
        ]
        
        self.image_path = filedialog.askopenfilename(title="Select Image File", 
                                                  filetypes=filetypes)
        
        if self.image_path:
            self.load_image_preview()
            self.process_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Selected image: {os.path.basename(self.image_path)}")
    
    def load_image_preview(self):
        # Load and display the image
        try:
            image = Image.open(self.image_path)
            
            # Resize for display
            width, height = image.size
            max_size = 400
            
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.resize((new_width, new_height))
            
            # Convert to PhotoImage
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(image)
            
            # Update label
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # Keep a reference
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def process_image(self):
        if not self.image_path:
            return
        
        self.start_processing("Processing image...")
        
        # Run processing in a separate thread
        threading.Thread(target=self._process_image_thread).start()
    
    def _process_image_thread(self):
        try:
            # Load image
            image = cv2.imread(self.image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Preprocessing based on selection
            preprocess_method = self.preprocess_var.get()
            
            if preprocess_method == "adaptive":
                # Adaptive thresholding
                processed = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY_INV, 11, 2
                )
                # Noise removal
                processed = cv2.medianBlur(processed, 3)
                
            elif preprocess_method == "otsu":
                # OTSU thresholding
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                _, processed = cv2.threshold(
                    blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
                )
                
            else:  # None
                processed = gray
            
            # Additional morphological closing to connect text strokes
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
            # Save the processed image for extraction
            self.processed_image = processed
            
            # Show processed image preview
            self.show_processed_preview()
            
            self.root.after(0, lambda: self.stop_processing("Image processed. Ready for text extraction."))
            self.root.after(0, lambda: self.extract_btn.config(state=tk.NORMAL))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.stop_processing(f"Error processing image: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Processing Error", msg))
    
    def show_processed_preview(self):
        # Convert the OpenCV image to PIL format
        if self.processed_image is not None:
            image = Image.fromarray(self.processed_image)
            
            # Resize for display
            width, height = image.size
            max_size = 400
            
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.resize((new_width, new_height))
            
            # Convert to PhotoImage
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(image)
            
            # Update label in the main thread
            self.root.after(0, lambda: self.image_label.config(image=photo, text=""))
            self.root.after(0, lambda: setattr(self.image_label, 'image', photo))
    
    def extract_text(self):
        if self.processed_image is None:
            return
            
        self.start_processing("Extracting text...")
        
        # Run extraction in a separate thread
        threading.Thread(target=self._extract_text_thread).start()
    
    def store_temp_file(self, text):
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, "ocr_extracted_text.txt")
        with open(temp_file_path, "w", encoding="utf-8") as file:
            file.write(text)
        return temp_file_path

    def _extract_text_thread(self):
        try:
            # Get selected language
            lang = self.lang_var.get()
            
            # Use OEM 3 and PSM 6 for refined results
            config = '--oem 3 --psm 6'
            if lang != "equ":
                config += f' -l {lang}'
            else:
                # For equations, keep English for now
                config += ' -l eng'
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(self.processed_image, config=config)
            print("Extracted text:", text)  # Debug output
            
            # Store text in a temporary file
            temp_file_path = self.store_temp_file(text)
            
            # Update the UI in the main thread to show the extracted text
            def update_text():
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, text)
                self.save_btn.config(state=tk.NORMAL)
                self.stop_processing(f"Text extraction complete. Temp file: {os.path.basename(temp_file_path)}")
            
            self.root.after(0, update_text)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.stop_processing(f"Error extracting text: {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("Extraction Error", error_msg))
    
    def save_text(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "No text to save.")
            return
            
        filetypes = [
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Save Text File",
            defaultextension=".txt",
            filetypes=filetypes
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(text)
                self.status_var.set(f"Text saved to {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
    
    def start_processing(self, message):
        self.status_var.set(message)
        self.progress.start(10)
        
        # Disable buttons during processing
        self.select_btn.config(state=tk.DISABLED)
        self.process_btn.config(state=tk.DISABLED)
        self.extract_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
    
    def stop_processing(self, message):
        self.progress.stop()
        self.status_var.set(message)
        
        # Re-enable buttons
        self.select_btn.config(state=tk.NORMAL)
        
        if self.image_path:
            self.process_btn.config(state=tk.NORMAL)
        
        if self.processed_image is not None:
            self.extract_btn.config(state=tk.NORMAL)
        
        if self.text_area.get(1.0, tk.END).strip():
            self.save_btn.config(state=tk.NORMAL)

def main():
    # Check for Tesseract installation first
    try:
        # Try to get tesseract version
        pytesseract.get_tesseract_version()
        
        # If we got here, tesseract is installed correctly
        root = tk.Tk()
        app = HandwritingOCRApp(root)
        root.mainloop()
    except Exception as e:
        # Show a helpful error message if tesseract isn't found
        root = tk.Tk()
        root.withdraw()  # Hide the empty window
        
        error_message = (
            "Tesseract OCR is not properly installed or configured.\n\n"
            "Please follow these steps:\n"
            "1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "2. Install it with 'Add to PATH' option checked\n"
            "3. Update the path in the code if needed\n\n"
            f"Error details: {str(e)}"
        )
        
        messagebox.showerror("Tesseract Installation Error", error_message)
        root.destroy()

if __name__ == "__main__":
    main()