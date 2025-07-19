"""Test mouse drag functionality"""

import sys
import os
import time
import tkinter as tk
from tkinter import ttk
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.win32_backend import Win32Backend


class DragTestApp:
    """Test application for mouse drag operations"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Drag Test")
        self.root.geometry("800x600")
        
        # Create test elements
        self.create_ui()
        
        # Track drag operations
        self.drag_count = 0
        self.drag_results = []
        
    def create_ui(self):
        """Create test UI elements"""
        
        # Title
        title = ttk.Label(self.root, text="CyberCorp Mouse Drag Test", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # Test 1: Slider (like captcha)
        frame1 = ttk.LabelFrame(self.root, text="Test 1: Slider Captcha Simulation")
        frame1.pack(fill='x', padx=20, pady=10)
        
        self.slider_canvas = tk.Canvas(frame1, width=400, height=80, bg='lightgray')
        self.slider_canvas.pack(pady=10)
        
        # Draw slider track
        self.slider_canvas.create_rectangle(50, 30, 350, 50, fill='white', outline='black')
        
        # Draw slider handle
        self.slider_handle = self.slider_canvas.create_rectangle(
            50, 20, 80, 60, fill='blue', outline='darkblue', tags='slider'
        )
        
        # Slider status
        self.slider_status = ttk.Label(frame1, text="Drag the blue slider to the right")
        self.slider_status.pack()
        
        # Test 2: Drag and Drop
        frame2 = ttk.LabelFrame(self.root, text="Test 2: Drag and Drop")
        frame2.pack(fill='x', padx=20, pady=10)
        
        self.dnd_canvas = tk.Canvas(frame2, width=600, height=150, bg='white')
        self.dnd_canvas.pack(pady=10)
        
        # Source box
        self.source_box = self.dnd_canvas.create_rectangle(
            50, 50, 150, 100, fill='green', outline='darkgreen', tags='source'
        )
        self.dnd_canvas.create_text(100, 75, text="Drag Me", fill='white')
        
        # Target area
        self.dnd_canvas.create_rectangle(
            450, 50, 550, 100, fill='', outline='red', width=2
        )
        self.dnd_canvas.create_text(500, 75, text="Drop Here", fill='red')
        
        # DnD status
        self.dnd_status = ttk.Label(frame2, text="Drag green box to red area")
        self.dnd_status.pack()
        
        # Test 3: Drawing/Gesture
        frame3 = ttk.LabelFrame(self.root, text="Test 3: Drawing/Gesture")
        frame3.pack(fill='x', padx=20, pady=10)
        
        self.draw_canvas = tk.Canvas(frame3, width=600, height=150, bg='lightyellow')
        self.draw_canvas.pack(pady=10)
        
        # Drawing status
        self.draw_status = ttk.Label(frame3, text="Draw a pattern by dragging")
        self.draw_status.pack()
        
        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=20)
        
        ttk.Button(control_frame, text="Run All Tests", 
                  command=self.run_all_tests).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Test Slider", 
                  command=self.test_slider).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Test Drag & Drop", 
                  command=self.test_dnd).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Test Drawing", 
                  command=self.test_drawing).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Reset", 
                  command=self.reset_all).pack(side='left', padx=5)
        
        # Results area
        results_frame = ttk.LabelFrame(self.root, text="Test Results")
        results_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.results_text = tk.Text(results_frame, height=8)
        self.results_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind manual drag events
        self.setup_manual_drag()
        
    def setup_manual_drag(self):
        """Setup manual drag event handlers"""
        # Slider
        self.slider_canvas.tag_bind('slider', '<Button-1>', self.on_slider_press)
        self.slider_canvas.tag_bind('slider', '<B1-Motion>', self.on_slider_drag)
        self.slider_canvas.tag_bind('slider', '<ButtonRelease-1>', self.on_slider_release)
        
        # Drag and drop
        self.dnd_canvas.tag_bind('source', '<Button-1>', self.on_dnd_press)
        self.dnd_canvas.tag_bind('source', '<B1-Motion>', self.on_dnd_drag)
        self.dnd_canvas.tag_bind('source', '<ButtonRelease-1>', self.on_dnd_release)
        
        # Drawing
        self.draw_canvas.bind('<Button-1>', self.on_draw_press)
        self.draw_canvas.bind('<B1-Motion>', self.on_draw_drag)
        self.draw_canvas.bind('<ButtonRelease-1>', self.on_draw_release)
        
        self.drag_data = {'x': 0, 'y': 0, 'item': None}
        
    def on_slider_press(self, event):
        """Handle slider press"""
        self.drag_data['x'] = event.x
        self.drag_data['item'] = self.slider_handle
        
    def on_slider_drag(self, event):
        """Handle slider drag"""
        dx = event.x - self.drag_data['x']
        coords = self.slider_canvas.coords(self.slider_handle)
        
        # Constrain to track
        new_x = coords[0] + dx
        if 50 <= new_x <= 320:
            self.slider_canvas.move(self.slider_handle, dx, 0)
            self.drag_data['x'] = event.x
            
            # Check if completed
            if new_x >= 270:
                self.slider_status.config(text="✓ Slider verification completed!")
                
    def on_slider_release(self, event):
        """Handle slider release"""
        pass
        
    def on_dnd_press(self, event):
        """Handle DnD press"""
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self.drag_data['item'] = self.source_box
        
    def on_dnd_drag(self, event):
        """Handle DnD drag"""
        dx = event.x - self.drag_data['x']
        dy = event.y - self.drag_data['y']
        self.dnd_canvas.move(self.source_box, dx, dy)
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        
    def on_dnd_release(self, event):
        """Handle DnD release"""
        # Check if in target area
        coords = self.dnd_canvas.coords(self.source_box)
        if coords[0] >= 450 and coords[2] <= 550:
            self.dnd_status.config(text="✓ Drag and drop completed!")
            
    def on_draw_press(self, event):
        """Handle draw press"""
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        
    def on_draw_drag(self, event):
        """Handle draw drag"""
        self.draw_canvas.create_line(
            self.drag_data['x'], self.drag_data['y'],
            event.x, event.y,
            fill='blue', width=2
        )
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        
    def on_draw_release(self, event):
        """Handle draw release"""
        self.draw_status.config(text="✓ Drawing completed!")
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        timestamp = time.strftime('%H:%M:%S')
        status = "PASS" if success else "FAIL"
        msg = f"[{timestamp}] {test_name}: {status}"
        if details:
            msg += f" - {details}"
        msg += "\n"
        
        self.results_text.insert('end', msg)
        self.results_text.see('end')
        self.root.update()
        
    def test_slider(self):
        """Test slider drag using Win32 API"""
        self.log_result("Slider Test", True, "Starting automated drag...")
        
        # Get window position
        win32 = Win32Backend()
        
        # Get canvas position relative to screen
        canvas_x = self.slider_canvas.winfo_rootx()
        canvas_y = self.slider_canvas.winfo_rooty()
        
        # Calculate drag positions
        start_x = canvas_x + 65  # Center of slider handle
        start_y = canvas_y + 40
        end_x = canvas_x + 300   # Near end of track
        end_y = start_y
        
        # Perform drag
        self.log_result("Slider Test", True, f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        
        def do_drag():
            time.sleep(0.5)  # Let UI settle
            success = win32.mouse_drag(start_x, start_y, end_x, end_y, duration=1.5)
            self.log_result("Slider Test", success, "Drag completed" if success else "Drag failed")
            
        threading.Thread(target=do_drag).start()
        
    def test_dnd(self):
        """Test drag and drop using Win32 API"""
        self.log_result("Drag & Drop Test", True, "Starting automated drag...")
        
        win32 = Win32Backend()
        
        # Get canvas position
        canvas_x = self.dnd_canvas.winfo_rootx()
        canvas_y = self.dnd_canvas.winfo_rooty()
        
        # Calculate positions
        start_x = canvas_x + 100  # Center of source box
        start_y = canvas_y + 75
        end_x = canvas_x + 500    # Center of target area
        end_y = canvas_y + 75
        
        def do_drag():
            time.sleep(0.5)
            success = win32.mouse_drag(start_x, start_y, end_x, end_y, duration=2.0, humanize=True)
            self.log_result("Drag & Drop Test", success, "Drag completed" if success else "Drag failed")
            
        threading.Thread(target=do_drag).start()
        
    def test_drawing(self):
        """Test drawing gesture using Win32 API"""
        self.log_result("Drawing Test", True, "Starting automated drawing...")
        
        win32 = Win32Backend()
        
        # Get canvas position
        canvas_x = self.draw_canvas.winfo_rootx()
        canvas_y = self.draw_canvas.winfo_rooty()
        
        def do_drawing():
            time.sleep(0.5)
            
            # Draw a simple pattern (zigzag)
            points = [
                (100, 75),
                (200, 25),
                (300, 125),
                (400, 25),
                (500, 75)
            ]
            
            for i in range(len(points) - 1):
                start_x = canvas_x + points[i][0]
                start_y = canvas_y + points[i][1]
                end_x = canvas_x + points[i+1][0]
                end_y = canvas_y + points[i+1][1]
                
                success = win32.mouse_drag(start_x, start_y, end_x, end_y, duration=0.5)
                if not success:
                    self.log_result("Drawing Test", False, f"Failed at segment {i+1}")
                    return
                    
                time.sleep(0.1)
                
            self.log_result("Drawing Test", True, "Drawing pattern completed")
            
        threading.Thread(target=do_drawing).start()
        
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log_result("Test Suite", True, "Starting all tests...")
        
        def run_tests():
            self.test_slider()
            time.sleep(3)
            
            self.reset_all()
            time.sleep(1)
            
            self.test_dnd()
            time.sleep(3)
            
            self.test_drawing()
            time.sleep(2)
            
            self.log_result("Test Suite", True, "All tests completed!")
            
        threading.Thread(target=run_tests).start()
        
    def reset_all(self):
        """Reset all test elements"""
        # Reset slider
        self.slider_canvas.coords(self.slider_handle, 50, 20, 80, 60)
        self.slider_status.config(text="Drag the blue slider to the right")
        
        # Reset DnD
        self.dnd_canvas.coords(self.source_box, 50, 50, 150, 100)
        self.dnd_status.config(text="Drag green box to red area")
        
        # Clear drawing
        self.draw_canvas.delete('all')
        self.draw_status.config(text="Draw a pattern by dragging")
        
        self.log_result("Reset", True, "All elements reset")


def test_drag_api():
    """Test the drag API directly"""
    print("Testing Win32 Drag API...")
    
    win32 = Win32Backend()
    
    # Test 1: Simple drag
    print("\n1. Testing simple drag:")
    success = win32.mouse_drag(100, 100, 500, 100, duration=1.0)
    print(f"   Simple drag: {'Success' if success else 'Failed'}")
    
    # Test 2: Humanized drag
    print("\n2. Testing humanized drag:")
    success = win32.mouse_drag(100, 200, 500, 200, duration=2.0, humanize=True)
    print(f"   Humanized drag: {'Success' if success else 'Failed'}")
    
    # Test 3: Right button drag
    print("\n3. Testing right button drag:")
    success = win32.mouse_drag(100, 300, 500, 300, duration=1.0, button='right')
    print(f"   Right button drag: {'Success' if success else 'Failed'}")
    
    print("\nDrag API tests completed")


def main():
    """Main test function"""
    print("CyberCorp Mouse Drag Test")
    print("=" * 50)
    
    # Test API first
    test_drag_api()
    
    print("\nStarting GUI test application...")
    print("Use the buttons to test automated drag operations")
    print("Or manually drag elements to test functionality")
    
    # Create GUI
    root = tk.Tk()
    app = DragTestApp(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()