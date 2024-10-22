# Script made by Claude (Anthropic) and ChatGPT (OpenAI) as prompted by Diogo Aleixo
# v1.1 loops to enable batch processing quicker

import re
import tkinter as tk
from tkinter import filedialog
from typing import List, Tuple
import pygetwindow as gw
import time

def parse_points(points_str: str) -> List[Tuple[float, float]]:
    """Parse the points string from fp_poly into a list of (x,y) coordinate tuples."""
    points = []
    # Match all (xy X Y) coordinates
    coordinates = re.finditer(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', points_str)
    for match in coordinates:
        x, y = float(match.group(1)), float(match.group(2))
        points.append((x, y))
    return points

def scale_points(points: List[Tuple[float, float]], scale_factor: float) -> List[Tuple[float, float]]:
    """Scale all points by the given factor."""
    return [(x * scale_factor, y * scale_factor) for x, y in points]

def format_points(points: List[Tuple[float, float]], indent: str = "      ") -> str:
    """Format points back into KiCad footprint format."""
    return "\n".join(f"{indent}(xy {x:.6f} {y:.6f})" for x, y in points)

def scale_footprint(content: str, scale_factor: float) -> str:
    """Scale the entire footprint by the given factor."""
    # Find all fp_poly sections
    poly_pattern = r'(  \(fp_poly\s+\(pts\s*\n)(.*?)\s*\)\s*\(stroke'
    
    def scale_poly_match(match):
        header = match.group(1)
        points_section = match.group(2)
        
        # Parse, scale, and reformat points
        points = parse_points(points_section)
        scaled_points = scale_points(points, scale_factor)
        new_points = format_points(scaled_points)
        
        return f"{header}{new_points}\n    ) (stroke"
    
    # Replace each fp_poly section with scaled version
    scaled_content = re.sub(poly_pattern, scale_poly_match, content, flags=re.DOTALL)
    
    # Scale font sizes and thicknesses
    size_pattern = r'\(size ([\d.]+) ([\d.]+)\)'
    scaled_content = re.sub(size_pattern, 
                          lambda m: f'(size {float(m.group(1))*scale_factor:.3f} {float(m.group(2))*scale_factor:.3f})',
                          scaled_content)
    
    thickness_pattern = r'\(thickness ([\d.]+)\)'
    scaled_content = re.sub(thickness_pattern,
                          lambda m: f'(thickness {float(m.group(1))*scale_factor:.3f})',
                          scaled_content)
    
    return scaled_content

def get_dimension_from_filename(filename: str) -> float:
    """Extract dimension in mm from filename if it exists."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*mm', filename)
    if match:
        return float(match.group(1))
    return None

def create_output_filename(input_filename: str, scale_factor: float) -> str:
    """Create output filename with updated dimension if original had one."""
    # Split filename and extension
    base_name, ext = os.path.splitext(input_filename)
    
    # Check for dimension in filename
    dimension = get_dimension_from_filename(base_name)
    if dimension is not None:
        # Remove the old dimension
        base_name = re.sub(r'\s*\d+(?:\.\d+)?\s*mm', '', base_name)
        # Add new dimension
        new_dimension = dimension * scale_factor
        return f"{base_name} {new_dimension:.1f}mm{ext}"
    else:
        # If no dimension found, just append 'scaled'
        return f"{base_name}_scaled{ext}"

def get_scale_factor() -> float:
    """Prompt user for scale factor with input validation. Returns 0 to select new file."""
    while True:
        try:
            scale_str = input("\nEnter scale factor (e.g., 2.0 for double size) (enter 0 to select new file): ")
            scale_factor = float(scale_str)
            if scale_factor < 0:
                print("Scale factor must be non-negative!")
                continue
            return scale_factor
        except ValueError:
            print("Please enter a valid number!")

def create_file_dialog_window(title: str) -> tk.Tk:
    """Create a properly configured window for file dialogs."""
    window = tk.Tk()
    window.withdraw()  # Hide the main window
    
    # Make sure window will appear on top
    window.attributes('-topmost', True)
    
    # Force focus (especially important on Windows)
    window.focus_force()
    
    # Set the dialog title
    window.title(title)
    
    return window

def process_footprint(input_file: str) -> bool:
    """Process a single footprint file. Returns True to continue with same file, False to select new file."""
    # Read input file
    with open(input_file, 'r') as f:
        content = f.read()

    while True:
        # Get scale factor from user
        scale_factor = get_scale_factor()
        
        # If scale factor is 0, return False to select new file
        if scale_factor == 0:
            return False

        # Scale the footprint
        scaled_content = scale_footprint(content, scale_factor)

        # Create output filename and path
        output_filename = create_output_filename(os.path.basename(input_file), scale_factor)
        output_file = os.path.join(os.path.dirname(input_file), output_filename)

        # Write output file
        try:
            with open(output_file, 'w') as f:
                f.write(scaled_content)
            print(f"\nScaled footprint saved successfully to:\n{output_file}")
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

        # Continue with same file
        return True

def refocus_terminal():
    """Refocus the terminal window after file dialog closes."""
    # Wait a moment to let the dialog close and avoid race conditions
    time.sleep(0.2)
    
    # Try to find the terminal window (cross-platform)
    try:
        # This should match the title of your terminal window
        window = gw.getActiveWindow()
        if window is not None:
            window.activate()  # Activate the terminal window
        else:
            print("Could not refocus terminal window.")
    except Exception as e:
        print(f"Error while refocusing terminal: {e}")


def main():
    while True:
        # Create and configure the root window for file dialogs
        root = create_file_dialog_window("KiCad Footprint Scaler")

        # Open file dialog
        print("\nSelect the KiCad footprint file to scale...")
        input_file = filedialog.askopenfilename(
            parent=root,
            title="Select KiCad Footprint File",
            filetypes=[("KiCad Footprint", "*.kicad_mod"), ("All Files", "*.*")]
        )

        if not input_file:  # User cancelled
            print("No file selected. Exiting...")
            root.destroy()
            return

        # Close the file dialog and return focus to the terminal
        root.update()
        root.destroy()

        # Refocus terminal after file dialog closes
        refocus_terminal()

        # Process the footprint until user chooses to select a new file
        while process_footprint(input_file):
            continue

if __name__ == "__main__":
    import os
    main()