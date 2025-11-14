import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
import heapq
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab
import os
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class Node:
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label
        self.distance = float('inf')
        self.visited = False
        self.previous = None

class Edge:
    def __init__(self, node1, node2, weight, directed=True):
        self.node1 = node1
        self.node2 = node2
        self.weight = weight
        self.directed = directed

class DijkstraVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Dijkstra Algorithm Visualizer")
        self.root.geometry("1400x800")
        
        self.nodes = []
        self.edges = []
        self.node_radius = 20
        self.selected_node = None
        self.start_node = None
        self.mode = "add_node"
        self.edge_start = None
        self.arrow_size = 10
        self.is_directed = tk.BooleanVar(value=True)
        
        # History for undo
        self.history = []
        
        # For moving and renaming nodes
        self.dragging_node = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Sidebar state
        self.sidebar_open = False
        self.sidebar_frame = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top Control Panel - Redesigned
        control_frame = tk.Frame(self.root, bg="#2c3e50")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Row 1: Title and Speed Control
        title_row = tk.Frame(control_frame, bg="#2c3e50", pady=10)
        title_row.pack(fill=tk.X)
        
        title = tk.Label(title_row, text="Dijkstra Algorithm Visualizer", 
                        font=("Arial", 16, "bold"), bg="#2c3e50", fg="white")
        title.pack(side=tk.LEFT, padx=20)
        
        # Speed Control on the right
        speed_frame = tk.Frame(title_row, bg="#2c3e50")
        speed_frame.pack(side=tk.RIGHT, padx=20)
        
        speed_label = tk.Label(speed_frame, text="Animation Speed:", 
                              font=("Arial", 10), bg="#2c3e50", fg="white")
        speed_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.IntVar(value=500)
        speed_scale = tk.Scale(speed_frame, from_=100, to=1000, 
                              orient=tk.HORIZONTAL, variable=self.speed_var,
                              bg="#2c3e50", fg="white", highlightthickness=0,
                              length=120, showvalue=0)
        speed_scale.pack(side=tk.LEFT, padx=5)
        
        tk.Label(speed_frame, text="Fast", font=("Arial", 8), 
                bg="#2c3e50", fg="#95a5a6").pack(side=tk.LEFT)
        
        # Separator
        tk.Frame(control_frame, bg="#34495e", height=2).pack(fill=tk.X)
        
        # Row 2: All Control Buttons
        buttons_row = tk.Frame(control_frame, bg="#2c3e50", pady=12)
        buttons_row.pack(fill=tk.X)
        
        # Left section: Mode buttons
        mode_frame = tk.Frame(buttons_row, bg="#2c3e50")
        mode_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(mode_frame, text="GRAPH CREATION", 
                font=("Arial", 8, "bold"), bg="#2c3e50", fg="#95a5a6").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,5))
        
        self.add_node_btn = tk.Button(mode_frame, text="Add Node", 
                                      command=lambda: self.set_mode("add_node"),
                                      bg="#3498db", fg="white", width=10,
                                      font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.add_node_btn.grid(row=1, column=0, padx=3)
        
        self.add_edge_btn = tk.Button(mode_frame, text="Add Edge", 
                                      command=lambda: self.set_mode("add_edge"),
                                      bg="#95a5a6", fg="white", width=10,
                                      font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.add_edge_btn.grid(row=1, column=1, padx=3)
        
        self.set_start_btn = tk.Button(mode_frame, text="Set Source", 
                                       command=lambda: self.set_mode("set_start"),
                                       bg="#95a5a6", fg="white", width=10,
                                       font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.set_start_btn.grid(row=1, column=2, padx=3)
        
        self.move_node_btn = tk.Button(mode_frame, text="Move Node", 
                                       command=lambda: self.set_mode("move_node"),
                                       bg="#95a5a6", fg="white", width=10,
                                       font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.move_node_btn.grid(row=1, column=3, padx=3)
        
        self.rename_node_btn = tk.Button(mode_frame, text="Rename Node", 
                                         command=lambda: self.set_mode("rename_node"),
                                         bg="#95a5a6", fg="white", width=10,
                                         font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.rename_node_btn.grid(row=1, column=4, padx=3)
        
        # Center-left: Graph Type
        graph_type_frame = tk.Frame(buttons_row, bg="#2c3e50")
        graph_type_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(graph_type_frame, text="GRAPH TYPE", 
                font=("Arial", 8, "bold"), bg="#2c3e50", fg="#95a5a6").pack(anchor=tk.W, pady=(0,5))
        
        self.directed_check = tk.Checkbutton(graph_type_frame, 
                                            text="Directed Graph", 
                                            variable=self.is_directed,
                                            command=self.toggle_direction,
                                            bg="#2c3e50", fg="white",
                                            selectcolor="#34495e",
                                            font=("Arial", 9, "bold"),
                                            activebackground="#2c3e50",
                                            activeforeground="white",
                                            cursor="hand2")
        self.directed_check.pack(anchor=tk.W)
        
        # Center: Algorithm Controls
        algo_frame = tk.Frame(buttons_row, bg="#2c3e50")
        algo_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(algo_frame, text="ALGORITHM", 
                font=("Arial", 8, "bold"), bg="#2c3e50", fg="#95a5a6").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0,5))
        
        self.run_btn = tk.Button(algo_frame, text="▶ Run", 
                                command=self.run_dijkstra,
                                bg="#27ae60", fg="white", width=11,
                                font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.run_btn.grid(row=1, column=0, padx=3)
        
        self.report_btn = tk.Button(algo_frame, text="📊 Report", 
                                    command=self.show_report,
                                    bg="#9b59b6", fg="white", width=11,
                                    font=("Arial", 9, "bold"), pady=5,
                                    state=tk.DISABLED, cursor="hand2")
        self.report_btn.grid(row=1, column=1, padx=3)
        
        # Center-right: Edit Controls
        edit_frame = tk.Frame(buttons_row, bg="#2c3e50")
        edit_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(edit_frame, text="EDIT", 
                font=("Arial", 8, "bold"), bg="#2c3e50", fg="#95a5a6").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,5))
        
        self.undo_btn = tk.Button(edit_frame, text="↶ Undo", 
                                   command=self.undo,
                                   bg="#f39c12", fg="white", width=9,
                                   font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.undo_btn.grid(row=1, column=0, padx=3)
        
        self.reset_btn = tk.Button(edit_frame, text="Reset", 
                                   command=self.reset_algorithm,
                                   bg="#e67e22", fg="white", width=9,
                                   font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.reset_btn.grid(row=1, column=1, padx=3)
        
        self.clear_btn = tk.Button(edit_frame, text="Clear All", 
                                   command=self.clear_all,
                                   bg="#e74c3c", fg="white", width=9,
                                   font=("Arial", 9, "bold"), pady=5, cursor="hand2")
        self.clear_btn.grid(row=1, column=2, padx=3)
        
        # Right: Info Buttons
        info_frame = tk.Frame(buttons_row, bg="#2c3e50")
        info_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(info_frame, text="INFORMATION", 
                font=("Arial", 8, "bold"), bg="#2c3e50", fg="#95a5a6").grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0,5))
        
        button_info = [
            ("📚 Learn", self.show_learn, "#9b59b6"),
            ("👥 Team", self.show_developed_by, "#3498db"),
            ("❓ Help", self.show_help, "#16a085"),
            ("💾 Save", self.download_report, "#27ae60")
        ]
        
        for idx, (text, command, color) in enumerate(button_info):
            btn = tk.Button(info_frame, text=text, command=command,
                          bg=color, fg="white", width=8,
                          font=("Arial", 8, "bold"), pady=5, cursor="hand2")
            btn.grid(row=1, column=idx, padx=2)
        
        # Info Panel
        info_frame = tk.Frame(self.root, bg="#34495e", padx=15, pady=10)
        info_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.info_label = tk.Label(info_frame, 
                                   text="Click 'Add Node' and click on canvas to add nodes | "
                                        "Toggle 'Directed Graph' to switch between directed/undirected edges | "
                                        "Set a source node and run Dijkstra to find shortest paths",
                                   font=("Arial", 10), bg="#34495e", fg="white",
                                   justify=tk.LEFT)
        self.info_label.pack(side=tk.LEFT)
        
        # Main container for canvas and sidebar
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Canvas
        self.canvas = tk.Canvas(self.main_container, bg="white", cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        
        self.algorithm_complete = False
        
    def save_state(self):
        """Save current state for undo"""
        state = {
            'nodes': [(n.x, n.y, n.label) for n in self.nodes],
            'edges': [(self.nodes.index(e.node1), self.nodes.index(e.node2), e.weight, e.directed) for e in self.edges],
            'start_node': self.nodes.index(self.start_node) if self.start_node else None
        }
        self.history.append(state)
        if len(self.history) > 20:  # Keep only last 20 states
            self.history.pop(0)
    
    def undo(self):
        """Undo last action"""
        if not self.history:
            messagebox.showinfo("Undo", "Nothing to undo")
            return
        
        state = self.history.pop()
        
        # Restore nodes
        self.nodes = []
        for x, y, label in state['nodes']:
            node = Node(x, y, label)
            self.nodes.append(node)
        
        # Restore edges
        self.edges = []
        for n1_idx, n2_idx, weight, directed in state['edges']:
            edge = Edge(self.nodes[n1_idx], self.nodes[n2_idx], weight, directed)
            self.edges.append(edge)
        
        # Restore start node
        self.start_node = self.nodes[state['start_node']] if state['start_node'] is not None else None
        
        self.reset_algorithm()
        self.info_label.config(text="Undo completed")
        
    def toggle_sidebar(self):
        """Toggle the info sidebar"""
        if self.sidebar_open:
            self.close_sidebar()
        else:
            self.open_sidebar()
    
    def open_sidebar(self):
        """Open the info sidebar - kept for backward compatibility"""
        # This function is now optional since buttons are in top bar
        pass
    
    def close_sidebar(self):
        """Close the info sidebar - kept for backward compatibility"""
        # This function is now optional since buttons are in top bar
        pass
    
    def show_learn(self):
        """Show learning materials"""
        learn_window = tk.Toplevel(self.root)
        learn_window.title("Learn - Dijkstra's Algorithm")
        learn_window.geometry("700x600")
        learn_window.transient(self.root)
        
        # Header
        header = tk.Frame(learn_window, bg="#2c3e50", pady=15)
        header.pack(fill=tk.X)
        tk.Label(header, text="Learn Dijkstra's Algorithm", 
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack()
        
        # Content
        content = scrolledtext.ScrolledText(learn_window, wrap=tk.WORD, 
                                           font=("Arial", 10), padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- MODIFIED: Improved Learn Section ---
        learn_text = """
DIJKSTRA'S ALGORITHM - A DETAILED GUIDE

═══════════════════════════════════════════════════════════════════

1. WHAT IS DIJKSTRA'S ALGORITHM?

Dijkstra's Algorithm is a **greedy algorithm** used to find the shortest paths 
from a single source node to all other nodes in a weighted graph. 

Key Properties:
• **Single Source:** It computes shortest paths from one specific node (the "source").
• **Weighted Graph:** The edges must have numerical weights.
• **Non-Negative Weights:** The algorithm *only* works correctly if all edge 
  weights are non-negative (zero or positive).
• **Greedy Approach:** At each step, it visits the "closest" unvisited node 
  from the source.

The algorithm builds a "shortest-path tree" where the path from the source 
to any other node in the tree is the shortest possible path.

Time Complexity: O((V + E) log V) with a priority queue (like this visualizer uses).
  - V = number of vertices (nodes)
  - E = number of edges

═══════════════════════════════════════════════════════════════════

2. HOW THE ALGORITHM WORKS (STEP-BY-STEP)

The algorithm maintains a set of visited nodes and the current shortest 
distance from the source to every other node.

Initialization:
1.  **Distances:** Create a list of distances for all nodes. Set the distance 
    of the **source node to 0** and all other nodes to **infinity (∞)**.
2.  **Visited Set:** Create an empty set to store nodes that have been visited.
3.  **Priority Queue:** Create a priority queue (min-heap) and add the source 
    node to it with a priority of 0.

The Loop:
The algorithm runs as long as the priority queue is not empty.

1.  **Extract Min:** Select the node `U` from the priority queue that has the 
    smallest distance.
2.  **Visit Node:** Mark node `U` as visited. (This means we have now found 
    the *final* shortest path to `U`).
3.  **Check Neighbors:** For each neighbor `V` of the current node `U`:
    a.  **Calculate New Distance:** Calculate the distance to `V` *through* `U`:
        `new_distance = distance[U] + weight(U, V)`
    b.  **Relaxation:** Compare this `new_distance` with the currently known 
        `distance[V]`.
        If `new_distance < distance[V]`:
        •   Update `distance[V]` to `new_distance`.
        •   Set the "previous" node for `V` to be `U` (to track the path).
        •   Add `V` to the priority queue with its new, smaller distance.

The loop finishes when the priority queue is empty, at which point the 
distance list contains the shortest path distances from the source to all 
reachable nodes.

═══════════════════════════════════════════════════════════════════

3. A STEP-BY-STEP EXAMPLE

Let's use a simple graph:
• Nodes: A, B, C
• Source Node: A
• Edges:
  - A → B (Weight: 1)
  - A → C (Weight: 4)
  - B → C (Weight: 2)

Initialization:
• Distances: { A: 0, B: ∞, C: ∞ }
• Priority Queue: [ (0, A) ]
• Visited: { }

---
STEP 1:
• Pop `(0, A)` from Priority Queue.
• Current Node: A (Distance 0)
• Mark A as Visited.
• Neighbors of A are B and C.

• Check Neighbor B:
  - `new_distance = distance[A] + weight(A, B)` = 0 + 1 = 1
  - 1 < ∞ (current `distance[B]`)
  - Update `distance[B]` = 1
  - Add `(1, B)` to Priority Queue.

• Check Neighbor C:
  - `new_distance = distance[A] + weight(A, C)` = 0 + 4 = 4
  - 4 < ∞ (current `distance[C]`)
  - Update `distance[C]` = 4
  - Add `(4, C)` to Priority Queue.

• State after Step 1:
  - Distances: { A: 0, B: 1, C: 4 }
  - Priority Queue: [ (1, B), (4, C) ]
  - Visited: { A }

---
STEP 2:
• Pop `(1, B)` (smallest distance) from Priority Queue.
• Current Node: B (Distance 1)
• Mark B as Visited.
• Neighbors of B is C.

• Check Neighbor C:
  - `new_distance = distance[B] + weight(B, C)` = 1 + 2 = 3
  - 3 < 4 (current `distance[C]`)
  - Update `distance[C]` = 3
  - Add `(3, C)` to Priority Queue.

• State after Step 2:
  - Distances: { A: 0, B: 1, C: 3 }
  - Priority Queue: [ (3, C), (4, C) ]  (Note: (4,C) is now stale)
  - Visited: { A, B }

---
STEP 3:
• Pop `(3, C)` from Priority Queue.
• Current Node: C (Distance 3)
• Mark C as Visited.
• C has no unvisited neighbors.

• State after Step 3:
  - Distances: { A: 0, B: 1, C: 3 }
  - Priority Queue: [ (4, C) ]
  - Visited: { A, B, C }

---
STEP 4:
• Pop `(4, C)` from Priority Queue.
• Current Node: C
• C is already in Visited set. We ignore it.

---
FINAL:
The queue is empty. The algorithm terminates.

Final Shortest Distances from A:
• To A: 0 (Path: A)
• To B: 1 (Path: A → B)
• To C: 3 (Path: A → B → C)

Notice how the path A → C (Weight 4) was *not* the shortest. The algorithm 
correctly found the path A → B → C (Weight 1 + 2 = 3).

═══════════════════════════════════════════════════════════════════

4. REFERENCES

Books:
• Introduction to Algorithms by Cormen, Leiserson, Rivest, and Stein (CLRS)
• Algorithm Design by Kleinberg and Tardos
• Data Structures and Algorithms in Python by Goodrich, Tamassia, Goldwasser

Online Resources:
• https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
• GeeksforGeeks - Dijkstra's Algorithm Tutorial
• Visualgo.net - Algorithm Visualizations

Video Tutorials:
• Dijkstra's Algorithm Visualization:
  https://www.youtube.com/watch?v=EFg3u_E6eHU
• Dijkstra's Shortest Path Algorithm Explained:
  https://www.youtube.com/watch?v=msttfIHHkak

═══════════════════════════════════════════════════════════════════

5. PROJECT IMPLEMENTATION

This visualizer is built using:
• Python 3.x
• Tkinter for GUI
• Priority Queue (heapq) for algorithm implementation
• Object-oriented design for nodes and edges

Features:
• Interactive graph creation
• Step-by-step algorithm visualization
• Support for directed and undirected graphs
• Detailed reports with shortest paths
• Undo functionality for easy corrections
"""
        # --- END MODIFICATION ---
        
        content.insert(tk.END, learn_text)
        content.config(state=tk.DISABLED)
        
        tk.Button(learn_window, text="Close", command=learn_window.destroy,
                 bg="#e74c3c", fg="white", font=("Arial", 11), pady=5).pack(pady=10)
    
    def load_photo(self, image_path, size=(120, 120)):
        """Load and resize photo, return PhotoImage or None"""
        try:
            if os.path.exists(image_path):
                img = Image.open(image_path)
                img = img.resize(size, Image.Resampling.LANCZOS)
                # Make circular (optional)
                return ImageTk.PhotoImage(img)
            else:
                return None
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def show_developed_by(self):
        """Show developer information"""
        dev_window = tk.Toplevel(self.root)
        dev_window.title("Developed By")
        
        # --- MODIFIED: Set window to 85% of screen height and centered ---
        screen_height = self.root.winfo_screenheight()
        screen_width = self.root.winfo_screenwidth()
        width = 600
        height = int(screen_height * 0.85) # 85% of screen height
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        dev_window.geometry(f"{width}x{height}+{x}+{y}")
        # --- END MODIFICATION ---
        
        dev_window.transient(self.root)
        
        # Header
        header = tk.Frame(dev_window, bg="#2c3e50", pady=15)
        header.pack(fill=tk.X)
        tk.Label(header, text="Developed By", 
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack()
        
        # Content
        content_frame = tk.Frame(dev_window, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # --- MODIFIED: Developer Section is now FIRST ---
        tk.Label(content_frame, text="DEVELOPED BY", 
                font=("Arial", 10, "bold"), bg="white", fg="#7f8c8d").pack(pady=(10, 10))
        
        # Developer 1
        dev1_frame = tk.Frame(content_frame, bg="white", relief=tk.RAISED, borderwidth=2)
        dev1_frame.pack(fill=tk.X, pady=10)
        
        # Try to load student photo
        student_photo = self.load_photo("student.png")
        if not student_photo:
            student_photo = self.load_photo("student.jpg")
        
        if student_photo:
            photo_label = tk.Label(dev1_frame, image=student_photo, bg="white")
            photo_label.image = student_photo  # Keep reference
            photo_label.pack(pady=10)
        else:
            tk.Label(dev1_frame, text="👤", font=("Arial", 40), bg="white").pack(pady=10)
        tk.Label(dev1_frame, text="Mayank Srivastava (24BCE5145)", 
                font=("Arial", 14, "bold"), bg="white").pack()
        tk.Label(dev1_frame, text="Lead Developer", 
                font=("Arial", 9, "italic"), bg="white", fg="#7f8c8d").pack(pady=(0, 10))
        
        # --- MODIFIED: Guided By Section is now SECOND ---
        guided_frame = tk.Frame(content_frame, bg="#ecf0f1", relief=tk.RAISED, borderwidth=2)
        guided_frame.pack(fill=tk.X, pady=(20, 15)) # Added padding-top
        
        tk.Label(guided_frame, text="GUIDED BY", 
                font=("Arial", 10, "bold"), bg="#ecf0f1", fg="#7f8c8d").pack(pady=(10, 5))
        
        # Try to load teacher photo
        teacher_photo = self.load_photo("teacher.png")
        if not teacher_photo:
            teacher_photo = self.load_photo("teacher.jpg")
        
        if teacher_photo:
            photo_label = tk.Label(guided_frame, image=teacher_photo, bg="#ecf0f1")
            photo_label.image = teacher_photo  # Keep reference
            photo_label.pack(pady=10)
        else:
            tk.Label(guided_frame, text="👨‍🏫", font=("Arial", 50), bg="#ecf0f1").pack(pady=10)
        
        tk.Label(guided_frame, text="Dr. Swaminathan Annadurai", 
                font=("Arial", 14, "bold"), bg="#ecf0f1").pack()
        tk.Label(guided_frame, text="Faculty Guide", 
                font=("Arial", 10, "italic"), bg="#ecf0f1", fg="#7f8c8d").pack(pady=(0, 15))
        # --- END MODIFICATION ---

        tk.Button(dev_window, text="Close", command=dev_window.destroy,
                 bg="#e74c3c", fg="white", font=("Arial", 11), pady=5).pack(pady=10)
    
    def show_help(self):
        """Show help information"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - How to Use")
        help_window.geometry("700x600")
        help_window.transient(self.root)
        
        # Header
        header = tk.Frame(help_window, bg="#2c3e50", pady=15)
        header.pack(fill=tk.X)
        tk.Label(header, text="How to Use This Visualizer", 
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack()
        
        # Content
        content = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, 
                                           font=("Arial", 10), padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_text = """
DIJKSTRA ALGORITHM VISUALIZER - USER GUIDE

═══════════════════════════════════════════════════════════════════

STEP 1: CREATE YOUR GRAPH

Adding Nodes:
1. Click the "Add Node" button (it will turn blue)
2. Click anywhere on the white canvas to place a node
3. Nodes are automatically labeled A, B, C, D, etc.
4. You can add up to 26 nodes

Adding Edges:
1. Click the "Add Edge" button
2. Click on the first node (starting point)
3. Click on the second node (ending point)
4. Enter the weight/distance in the popup dialog
5. The edge will be created with the specified weight

═══════════════════════════════════════════════════════════════════

STEP 2: CONFIGURE GRAPH TYPE

Directed vs Undirected:
• Check "Directed Graph" for one-way connections (arrows shown)
• Uncheck for two-way connections (no arrows)
• You can toggle this at any time - all edges will update

═══════════════════════════════════════════════════════════════════

STEP 3: SET SOURCE NODE

1. Click the "Set Source" button
2. Click on any node to mark it as the starting point
3. The source node will turn green

═══════════════════════════════════════════════════════════════════

STEP 4: RUN THE ALGORITHM

1. Click "Run Dijkstra" button
2. Watch the algorithm process each node:
   • Orange nodes = being processed
   • Purple edges = shortest path found
   • Distance labels appear above nodes
3. A summary popup will show results

═══════════════════════════════════════════════════════════════════

STEP 5: ANALYZE RESULTS

View Report:
• Click "Show Report" button (enabled after running algorithm)
• See detailed table with all shortest paths
• View unreachable nodes (if any)
• Check the complete path from source to each destination

═══════════════════════════════════════════════════════════════════

ADDITIONAL FEATURES

Undo: Revert your last action (up to 20 steps)
Reset: Clear algorithm results but keep your graph
Clear All: Delete everything and start fresh
Speed Control: Adjust animation speed with the slider
Download: Save a detailed report of your results

═══════════════════════════════════════════════════════════════════

TIPS FOR BEST RESULTS

✓ Plan your graph layout before adding many nodes
✓ Use meaningful weights that represent real distances
✓ Try both directed and undirected modes to compare
✓ Start with simple graphs to understand the algorithm
✓ Use Undo if you make a mistake
✓ Check the report for detailed path information

═══════════════════════════════════════════════════════════════════

TROUBLESHOOTING

Problem: Some nodes show as unreachable
Solution: Check if there's a path of edges connecting them to source

Problem: Algorithm not working
Solution: Ensure you've set a source node first

Problem: Can't see all nodes
Solution: Try Reset or Clear All to restart
"""
        
        content.insert(tk.END, help_text)
        content.config(state=tk.DISABLED)
        
        tk.Button(help_window, text="Close", command=help_window.destroy,
                 bg="#e74c3c", fg="white", font=("Arial", 11), pady=5).pack(pady=10)
    
    def download_report(self):
        """Download detailed report with canvas screenshot as PDF"""
        if not self.algorithm_complete:
            messagebox.showwarning("Warning", "Please run Dijkstra's algorithm first before generating report")
            return
        
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Missing Library", 
                               "ReportLab is required to generate PDF reports.\n\n"
                               "Please install it using:\npip install reportlab")
            return
        
        try:
            # Generate filename
            filename = f"dijkstra_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Take screenshot of canvas
            screenshot_path = self.capture_canvas()
            
            if not screenshot_path:
                messagebox.showerror("Error", "Failed to capture canvas screenshot")
                return
            
            # Create PDF
            doc = SimpleDocTemplate(filename, pagesize=A4,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor='#2c3e50',
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor='#2c3e50',
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            )
            
            subheading_style = ParagraphStyle(
                'SubHeading',
                parent=styles['Normal'],
                fontSize=12,
                textColor='#34495e',
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
            
            # Title
            story.append(Paragraph("Dijkstra's Algorithm Visualizer", title_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", 
                                 styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Canvas Screenshot with maintained aspect ratio
            story.append(Paragraph("Graph Visualization", heading_style))
            
            # Load image and calculate proper dimensions
            img_obj = Image.open(screenshot_path)
            img_width, img_height = img_obj.size
            aspect_ratio = img_height / img_width
            
            # Set max width to 6.5 inches (fits A4 with margins)
            max_width = 6.5 * inch
            final_width = min(max_width, img_width)
            final_height = final_width * aspect_ratio
            
            # If height is too large, scale down
            max_height = 5 * inch
            if final_height > max_height:
                final_height = max_height
                final_width = final_height / aspect_ratio
            
            img = RLImage(screenshot_path, width=final_width, height=final_height)
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
            
            # Graph Information Section
            story.append(Paragraph("Graph Configuration", heading_style))
            graph_info = f"""
            <b>Source Node:</b> {self.start_node.label}<br/>
            <b>Total Nodes:</b> {len(self.nodes)}<br/>
            <b>Total Edges:</b> {len(self.edges)}<br/>
            <b>Graph Type:</b> {'Directed' if self.is_directed.get() else 'Undirected'}<br/>
            <b>Algorithm:</b> Dijkstra's Shortest Path Algorithm
            """
            story.append(Paragraph(graph_info, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Detailed Edge Information
            story.append(Paragraph("Edge Connections", heading_style))
            story.append(Paragraph("The following edges define the graph structure:", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            for idx, edge in enumerate(self.edges, 1):
                edge_type = "Directed" if edge.directed else "Undirected"
                arrow = "→" if edge.directed else "↔"
                edge_detail = f"""
                <b>Edge {idx}:</b> {edge.node1.label} {arrow} {edge.node2.label}<br/>
                &nbsp;&nbsp;&nbsp;&nbsp;Weight: {edge.weight:.1f} | Type: {edge_type}
                """
                story.append(Paragraph(edge_detail, styles['Normal']))
                story.append(Spacer(1, 0.08*inch))
            
            # Page break before results
            story.append(PageBreak())
            
            # Algorithm Execution Details
            story.append(Paragraph("Algorithm Execution Report", heading_style))
            story.append(Paragraph(f"Source Node: <b>{self.start_node.label}</b>", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Get results
            reachable = []
            unreachable = []
            
            for node in self.nodes:
                if node == self.start_node:
                    continue
                if node.distance == float('inf'):
                    unreachable.append(node)
                else:
                    reachable.append(node)
            
            reachable.sort(key=lambda x: x.distance)
            
            # Reachable nodes with detailed paths
            if reachable:
                story.append(Paragraph("Shortest Paths to Reachable Nodes", subheading_style))
                story.append(Paragraph(f"Successfully found shortest paths to {len(reachable)} node(s):", 
                                     styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
                
                for idx, node in enumerate(reachable, 1):
                    # Reconstruct path
                    path = []
                    path_nodes = []
                    current = node
                    while current:
                        path_nodes.append(current)
                        path.append(current.label)
                        current = current.previous
                    path.reverse()
                    path_nodes.reverse()
                    path_str = " → ".join(path)
                    
                    # Calculate step-by-step distances
                    step_details = []
                    cumulative_dist = 0
                    for i in range(1, len(path_nodes)):
                        prev_node = path_nodes[i-1]
                        curr_node = path_nodes[i]
                        # Find edge weight
                        edge_weight = 0
                        for edge in self.edges:
                            if (edge.node1 == prev_node and edge.node2 == curr_node):
                                edge_weight = edge.weight
                                break
                            elif not edge.directed and (edge.node2 == prev_node and edge.node1 == curr_node):
                                edge_weight = edge.weight
                                break
                        cumulative_dist += edge_weight
                        step_details.append(f"{prev_node.label}→{curr_node.label} (+{edge_weight:.1f})")
                    
                    node_report = f"""
                    <b>Destination {idx}: Node {node.label}</b><br/>
                    &nbsp;&nbsp;&nbsp;&nbsp;Total Distance: <b>{node.distance:.1f}</b><br/>
                    &nbsp;&nbsp;&nbsp;&nbsp;Complete Path: {path_str}<br/>
                    &nbsp;&nbsp;&nbsp;&nbsp;Path Breakdown: {" → ".join(step_details)}
                    """
                    story.append(Paragraph(node_report, styles['Normal']))
                    story.append(Spacer(1, 0.12*inch))
            
            # Unreachable nodes
            if unreachable:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Unreachable Nodes", subheading_style))
                unreachable_list = ", ".join([node.label for node in unreachable])
                story.append(Paragraph(
                    f"<b>Count:</b> {len(unreachable)} node(s)<br/>"
                    f"<b>Nodes:</b> {unreachable_list}", 
                    styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                reason_text = """
                <b>Explanation:</b> These nodes cannot be reached from the source node. 
                This indicates that there is no sequence of edges connecting the source to these nodes.
                """
                if self.is_directed.get():
                    reason_text += """
                    In a directed graph, this means no directed path exists from the source. 
                    Consider adding edges pointing toward these nodes or changing the graph to undirected.
                    """
                else:
                    reason_text += """
                    In an undirected graph, this indicates these nodes belong to a separate 
                    connected component of the graph.
                    """
                story.append(Paragraph(reason_text, styles['Italic']))
            
            # Summary Statistics
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("Summary Statistics", heading_style))
            
            summary = f"""
            <b>Total Nodes Analyzed:</b> {len(self.nodes)}<br/>
            <b>Reachable from Source:</b> {len(reachable)} ({len(reachable)*100//max(len(self.nodes)-1,1)}%)<br/>
            <b>Unreachable from Source:</b> {len(unreachable)}<br/>
            """
            
            if reachable:
                min_dist_node = min(reachable, key=lambda n: n.distance)
                max_dist_node = max(reachable, key=lambda n: n.distance)
                avg_dist = sum(n.distance for n in reachable) / len(reachable)
                summary += f"""
                <b>Shortest Distance:</b> {min_dist_node.distance:.1f} (to node {min_dist_node.label})<br/>
                <b>Longest Distance:</b> {max_dist_node.distance:.1f} (to node {max_dist_node.label})<br/>
                <b>Average Distance:</b> {avg_dist:.2f}
                """
            
            story.append(Paragraph(summary, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Clean up screenshot with proper error handling
            try:
                if os.path.exists(screenshot_path):
                    # Small delay to ensure PDF is closed
                    import time
                    time.sleep(0.1)
                    os.remove(screenshot_path)
            except Exception as cleanup_error:
                # If cleanup fails, just log it - PDF was still created successfully
                print(f"Note: Temporary file cleanup skipped: {cleanup_error}")
            
            messagebox.showinfo("Success", 
                              f"PDF report generated successfully!\n\n"
                              f"Saved as: {filename}\n\n"
                              f"The report includes:\n"
                              f"• Canvas screenshot\n"
                              f"• Detailed edge connections\n"
                              f"• Step-by-step path analysis\n"
                              f"• Summary statistics")
            self.info_label.config(text=f"PDF report saved: {filename}")
            
        except Exception as e:
            # Try to clean up on error
            try:
                if 'screenshot_path' in locals() and os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
            except:
                pass
            messagebox.showerror("Error", f"Failed to generate PDF report:\n{str(e)}")
    
    def capture_canvas(self):
        """Capture screenshot of the canvas"""
        try:
            # Update canvas to ensure everything is drawn
            self.canvas.update()
            
            # Get canvas position and size
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # Capture screenshot
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # Use unique filename with timestamp to avoid conflicts
            temp_path = f"temp_canvas_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            screenshot.save(temp_path)
            
            return temp_path
        except Exception as e:
            print(f"Error capturing canvas: {e}")
            return None
    
    def generate_detailed_report(self):
        """Generate detailed step-by-step report"""
        report = "=" * 80 + "\n"
        report += "DIJKSTRA'S SHORTEST PATH ALGORITHM - DETAILED REPORT\n"
        report += "=" * 80 + "\n\n"
        
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Input Information
        report += "STEP 1: INPUT INFORMATION\n"
        report += "-" * 80 + "\n"
        report += f"Source Node: {self.start_node.label}\n"
        report += f"Total Nodes: {len(self.nodes)}\n"
        report += f"Total Edges: {len(self.edges)}\n"
        report += f"Graph Type: {'Directed' if self.is_directed.get() else 'Undirected'}\n"
        report += f"\nNodes in Graph: {', '.join([n.label for n in self.nodes])}\n"
        report += "\n" + "=" * 80 + "\n\n"
        
        # Edge List
        report += "STEP 2: EDGE INFORMATION\n"
        report += "-" * 80 + "\n"
        report += f"{'From':<10} {'To':<10} {'Weight':<10} {'Type':<15}\n"
        report += "-" * 80 + "\n"
        for edge in self.edges:
            edge_type = "Directed" if edge.directed else "Undirected"
            report += f"{edge.node1.label:<10} {edge.node2.label:<10} {edge.weight:<10.1f} {edge_type:<15}\n"
        report += "\n" + "=" * 80 + "\n\n"
        
        # Algorithm Execution
        report += "STEP 3: ALGORITHM EXECUTION\n"
        report += "-" * 80 + "\n"
        report += f"Starting from source node: {self.start_node.label}\n"
        report += f"Initial distance to source: 0\n"
        report += f"Initial distance to all other nodes: ∞ (infinity)\n\n"
        report += "The algorithm processes nodes in order of increasing distance from source,\n"
        report += "updating distances to neighbors and building the shortest path tree.\n"
        report += "\n" + "=" * 80 + "\n\n"
        
        # Results
        reachable = []
        unreachable = []
        
        for node in self.nodes:
            if node == self.start_node:
                continue
            if node.distance == float('inf'):
                unreachable.append(node)
            else:
                reachable.append(node)
        
        reachable.sort(key=lambda x: x.distance)
        
        report += "STEP 4: SHORTEST DISTANCES FROM SOURCE\n"
        report += "-" * 80 + "\n\n"
        
        if reachable:
            report += f"{'Destination':<15} {'Distance':<15} {'Path':<50}\n"
            report += "-" * 80 + "\n"
            
            for node in reachable:
                # Reconstruct path
                path = []
                current = node
                while current:
                    path.append(current.label)
                    current = current.previous
                path.reverse()
                path_str = " → ".join(path)
                
                report += f"{node.label:<15} {node.distance:<15.1f} {path_str:<50}\n"
                
                # Detailed explanation
                report += f"  Explanation: To reach {node.label}, follow path {path_str}\n"
                report += f"  Total cost: {node.distance:.1f}\n\n"
        else:
            report += "No reachable nodes found from the source.\n"
        
        report += "\n" + "=" * 80 + "\n\n"
        
        # Unreachable nodes
        if unreachable:
            report += "STEP 5: UNREACHABLE NODES ANALYSIS\n"
            report += "-" * 80 + "\n"
            report += "The following nodes cannot be reached from the source node:\n"
            report += ", ".join([node.label for node in unreachable]) + "\n\n"
            report += "Reason: No valid path exists from the source node to these nodes.\n"
            if self.is_directed.get():
                report += "Note: In a directed graph, this means no sequence of directed edges\n"
                report += "leads from the source to these nodes. Check edge directions.\n"
            else:
                report += "Note: These nodes are in a separate connected component of the graph.\n"
        else:
            report += "STEP 5: GRAPH CONNECTIVITY\n"
            report += "-" * 80 + "\n\n"
            report += "SUCCESS: All nodes in the graph are reachable from the source node!\n"
            report += "This indicates a well-connected graph structure.\n"
        
        report += "\n" + "=" * 80 + "\n\n"
        
        # Summary
        report += "STEP 6: SUMMARY\n"
        report += "-" * 80 + "\n"
        report += f"• Source Node: {self.start_node.label}\n"
        report += f"• Reachable Nodes: {len(reachable)}\n"
        report += f"• Unreachable Nodes: {len(unreachable)}\n"
        if reachable:
            report += f"• Shortest Distance: {min(n.distance for n in reachable):.1f} (to node {min(reachable, key=lambda n: n.distance).label})\n"
            report += f"• Longest Distance: {max(n.distance for n in reachable):.1f} (to node {max(reachable, key=lambda n: n.distance).label})\n"
        
        report += "\n" + "=" * 80 + "\n"
        report += "END OF REPORT\n"
        report += "=" * 80 + "\n"
        
        return report
        
    def toggle_direction(self):
        # Update all existing edges
        for edge in self.edges:
            edge.directed = self.is_directed.get()
        self.draw_graph()
        
        if self.is_directed.get():
            self.info_label.config(text="Switched to DIRECTED graph - Edges have direction")
        else:
            self.info_label.config(text="Switched to UNDIRECTED graph - Edges work both ways")
        
    def set_mode(self, mode):
        self.mode = mode
        self.edge_start = None
        
        # Update button colors
        self.add_node_btn.config(bg="#95a5a6")
        self.add_edge_btn.config(bg="#95a5a6")
        self.set_start_btn.config(bg="#95a5a6")
        self.move_node_btn.config(bg="#95a5a6")
        self.rename_node_btn.config(bg="#95a5a6")
        
        if mode == "add_node":
            self.add_node_btn.config(bg="#3498db")
            self.info_label.config(text="Mode: Add Node - Click on canvas to place a new node")
            self.canvas.config(cursor="crosshair")
        elif mode == "add_edge":
            self.add_edge_btn.config(bg="#3498db")
            edge_type = "directed" if self.is_directed.get() else "undirected"
            self.info_label.config(text=f"Mode: Add Edge ({edge_type}) - Click two nodes to create an edge")
            self.canvas.config(cursor="hand2")
        elif mode == "set_start":
            self.set_start_btn.config(bg="#3498db")
            self.info_label.config(text="Mode: Set Source - Click a node to set it as the source node")
            self.canvas.config(cursor="hand2")
        elif mode == "move_node":
            self.move_node_btn.config(bg="#3498db")
            self.info_label.config(text="Mode: Move Node - Click and drag a node to move it")
            self.canvas.config(cursor="fleur")
        elif mode == "rename_node":
            self.rename_node_btn.config(bg="#3498db")
            self.info_label.config(text="Mode: Rename Node - Click a node to rename it")
            self.canvas.config(cursor="hand2")
    
    def canvas_click(self, event):
        if self.mode == "add_node":
            self.add_node(event.x, event.y)
        elif self.mode == "add_edge":
            self.select_for_edge(event.x, event.y)
        elif self.mode == "set_start":
            self.set_start_node(event.x, event.y)
        elif self.mode == "move_node":
            self.start_move_node(event.x, event.y)
        elif self.mode == "rename_node":
            self.rename_node(event.x, event.y)
    
    def canvas_drag(self, event):
        if self.mode == "move_node" and self.dragging_node:
            self.dragging_node.x = event.x
            self.dragging_node.y = event.y
            self.draw_graph()
    
    def canvas_release(self, event):
        if self.mode == "move_node" and self.dragging_node:
            self.dragging_node = None
            self.info_label.config(text="Node moved - Click and drag another node to move it")
    
    def add_node(self, x, y):
        self.save_state()
        label = chr(65 + len(self.nodes))  # A, B, C, ...
        if len(self.nodes) >= 26:
            messagebox.showwarning("Limit", "Maximum 26 nodes allowed")
            return
        
        node = Node(x, y, label)
        self.nodes.append(node)
        self.draw_graph()
    
    def select_for_edge(self, x, y):
        clicked_node = self.get_node_at(x, y)
        if clicked_node:
            if self.edge_start is None:
                self.edge_start = clicked_node
                self.info_label.config(text=f"Selected {clicked_node.label} - Now click destination node")
                self.draw_graph()
            else:
                if self.edge_start != clicked_node:
                    weight = self.get_edge_weight()
                    if weight is not None:
                        self.save_state()
                        edge = Edge(self.edge_start, clicked_node, weight, directed=self.is_directed.get())
                        self.edges.append(edge)
                        edge_type = "→" if self.is_directed.get() else "↔"
                        self.info_label.config(text=f"Edge created: {self.edge_start.label} {edge_type} {clicked_node.label} (weight: {weight})")
                else:
                    self.info_label.config(text="Cannot create edge to same node - Select different node")
                self.edge_start = None
                self.draw_graph()
    
    def get_edge_weight(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edge Weight")
        dialog.geometry("300x120")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter edge weight:", font=("Arial", 11)).pack(pady=10)
        weight_var = tk.StringVar(value="1")
        entry = tk.Entry(dialog, textvariable=weight_var, font=("Arial", 12), width=15)
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, tk.END)
        
        result = [None]
        
        def ok():
            try:
                val = float(weight_var.get())
                if val <= 0:
                    messagebox.showerror("Error", "Weight must be positive")
                    return
                result[0] = val
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
        entry.bind("<Return>", lambda e: ok())
        
        dialog.wait_window()
        return result[0]
    
    def set_start_node(self, x, y):
        node = self.get_node_at(x, y)
        if node:
            self.save_state()
            self.start_node = node
            self.info_label.config(text=f"Source node set to: {node.label}")
            self.draw_graph()
    
    def start_move_node(self, x, y):
        node = self.get_node_at(x, y)
        if node:
            self.save_state()
            self.dragging_node = node
            self.drag_start_x = x
            self.drag_start_y = y
            self.info_label.config(text=f"Moving node {node.label} - Drag to new position")
    
    def rename_node(self, x, y):
        node = self.get_node_at(x, y)
        if node:
            dialog = tk.Toplevel(self.root)
            dialog.title("Rename Node")
            dialog.geometry("300x120")
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text=f"Rename node {node.label}:", font=("Arial", 11)).pack(pady=10)
            name_var = tk.StringVar(value=node.label)
            entry = tk.Entry(dialog, textvariable=name_var, font=("Arial", 12), width=15)
            entry.pack(pady=5)
            entry.focus()
            entry.select_range(0, tk.END)
            
            def ok():
                new_name = name_var.get().strip().upper()
                if not new_name:
                    messagebox.showerror("Error", "Node name cannot be empty")
                    return
                if len(new_name) > 3:
                    messagebox.showerror("Error", "Node name must be 3 characters or less")
                    return
                # Check if name already exists
                if any(n.label == new_name and n != node for n in self.nodes):
                    messagebox.showerror("Error", f"Node '{new_name}' already exists")
                    return
                
                self.save_state()
                old_name = node.label
                node.label = new_name
                self.info_label.config(text=f"Node renamed: {old_name} → {new_name}")
                self.draw_graph()
                dialog.destroy()
            
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=10)
            tk.Button(btn_frame, text="OK", command=ok, width=10).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
            entry.bind("<Return>", lambda e: ok())
    
    def get_node_at(self, x, y):
        for node in self.nodes:
            dist = math.sqrt((node.x - x)**2 + (node.y - y)**2)
            if dist <= self.node_radius:
                return node
        return None
    
    # --- MODIFIED: draw_arrow now curves ALL directed edges ---
    def draw_arrow(self, x1, y1, x2, y2, color="#bdc3c7", width=2, is_shortest_path=False):
        # Calculate direction and length
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return (x1, y1) # Return midpoint if no length
        
        # Normalize
        udx = dx / length
        udy = dy / length
        
        # Perpendicular vector (normalized)
        unx = -udy
        uny = udx
        
        # --- REVERSED CURVE LOGIC ---
        should_curve = False
        # Curve if it's a directed edge (and not part of the final shortest path)
        if self.is_directed.get() and not is_shortest_path:
            should_curve = True
        # --- END REVERSED CURVE LOGIC ---
            
        if should_curve:
            # DRAW CURVED LINE
            
            # Offset distance for control point
            offset = min(length * 0.2, 50)
            
            # Shorten the line to not overlap node circles
            start_x = x1 + udx * self.node_radius
            start_y = y1 + udy * self.node_radius
            end_x = x2 - udx * self.node_radius
            end_y = y2 - udy * self.node_radius
            
            # Control point
            ctrl_x = (start_x + end_x) / 2 + offset * unx
            ctrl_y = (start_y + end_y) / 2 + offset * uny

            line_coords = (start_x, start_y, ctrl_x, ctrl_y, end_x, end_y)
            
            # We know it's directed, so always draw arrow
            self.canvas.create_line(line_coords, fill=color, width=width, smooth=True,
                                   arrow=tk.LAST, arrowshape=(self.arrow_size, self.arrow_size+2, self.arrow_size-2))

            # Weight position: slightly further than control point
            wx = (x1 + x2) / 2 + (offset + 20) * unx
            wy = (y1 + y2) / 2 + (offset + 20) * uny
            return (wx, wy)
        
        else:
            # DRAW STRAIGHT LINE
            # (This block now handles UNDIRECTED edges and shortest path edges)
            
            # Shorten line to not overlap with node circles
            start_x = x1 + udx * self.node_radius
            start_y = y1 + udy * self.node_radius
            end_x = x2 - udx * self.node_radius
            end_y = y2 - udy * self.node_radius
            
            # Arrow logic
            # Show arrow if it's a shortest path (which is always directed)
            # or if the graph is directed (which it isn't, in this 'else' block, unless it's a shortest path)
            show_arrow = is_shortest_path
            
            # Handle the case for undirected, non-shortest-path
            if not self.is_directed.get() and not is_shortest_path:
                 show_arrow = False
            
            # Handle the case for shortest path on directed graph
            if self.is_directed.get() and is_shortest_path:
                show_arrow = True

            if show_arrow:
                self.canvas.create_line(start_x, start_y, end_x, end_y, 
                                       fill=color, width=width, arrow=tk.LAST,
                                       arrowshape=(self.arrow_size, self.arrow_size+2, self.arrow_size-2))
            else:
                # This will be for undirected, non-shortest-path lines
                self.canvas.create_line(start_x, start_y, end_x, end_y, 
                                       fill=color, width=width)
            
            # Weight position: midpoint of straight line, offset slightly
            mx = (x1 + x2) / 2 + 15 * unx
            my = (y1 + y2) / 2 + 15 * uny
            return (mx, my)
    # --- END MODIFICATION ---

    # --- MODIFIED: draw_graph now removes bidirectional check ---
    def draw_graph(self):
        self.canvas.delete("all")
        
        # Draw edges
        for edge in self.edges:
            x1, y1 = edge.node1.x, edge.node1.y
            x2, y2 = edge.node2.x, edge.node2.y
            
            color = "#bdc3c7"
            width = 2
            
            # Check if this edge is part of shortest path
            is_shortest_path = False
            if edge.node2.previous == edge.node1 and edge.node2.visited:
                is_shortest_path = True
                color = "#8e44ad"
                width = 4
            elif not edge.directed and edge.node1.previous == edge.node2 and edge.node1.visited:
                is_shortest_path = True
                color = "#8e44ad"
                width = 4
            
            # --- REMOVED BIDIRECTIONAL LOGIC ---

            # Draw arrow/curve and get weight position
            wx, wy = self.draw_arrow(x1, y1, x2, y2, color, width, is_shortest_path)
            
            # Draw weight
            self.canvas.create_oval(wx-15, wy-15, wx+15, wy+15, 
                                   fill="white", outline=color, width=2)
            self.canvas.create_text(wx, wy, text=str(int(edge.weight)), 
                                   font=("Arial", 10, "bold"))
        
        # Draw nodes
        for node in self.nodes:
            color = "#3498db"
            outline = "#2980b9"
            
            if node == self.start_node:
                color = "#27ae60"
                outline = "#229954"
            elif node.visited:
                color = "#f39c12"
                outline = "#d68910"
            
            if node == self.edge_start:
                outline = "#8e44ad"
                width = 4
            else:
                width = 3
            
            self.canvas.create_oval(node.x - self.node_radius, 
                                   node.y - self.node_radius,
                                   node.x + self.node_radius, 
                                   node.y + self.node_radius,
                                   fill=color, outline=outline, width=width)
            
            self.canvas.create_text(node.x, node.y, text=node.label, 
                                   font=("Arial", 14, "bold"), fill="white")
            
            # Display distance if calculated
            if node.distance != float('inf') and node != self.start_node:
                self.canvas.create_text(node.x, node.y - self.node_radius - 15, 
                                       text=f"d={node.distance:.1f}", 
                                       font=("Arial", 9, "bold"), fill="#e74c3c")
            elif node == self.start_node and node.distance == 0:
                self.canvas.create_text(node.x, node.y - self.node_radius - 15, 
                                       text="d=0", 
                                       font=("Arial", 9, "bold"), fill="#27ae60")
    # --- END MODIFICATION ---
    
    def run_dijkstra(self):
        if not self.start_node:
            messagebox.showwarning("Warning", "Please set a source node first")
            return
        
        if not self.nodes:
            messagebox.showwarning("Warning", "Please add some nodes first")
            return
        
        self.reset_algorithm()
        self.start_node.distance = 0
        self.algorithm_complete = False
        
        pq = [(0, id(self.start_node), self.start_node)]
        
        def step():
            if not pq:
                self.algorithm_complete = True
                self.report_btn.config(state=tk.NORMAL)
                self.show_results()
                return
            
            current_dist, _, current = heapq.heappop(pq)
            
            if current.visited:
                self.root.after(self.speed_var.get(), step)
                return
            
            current.visited = True
            self.info_label.config(text=f"Processing node {current.label} (distance: {current.distance:.1f})")
            self.draw_graph()
            
            # Get neighbors based on graph type
            neighbors = []
            for edge in self.edges:
                if edge.directed:
                    # Directed: only follow edges from current node
                    if edge.node1 == current:
                        neighbors.append((edge.node2, edge.weight))
                else:
                    # Undirected: follow edges in both directions
                    if edge.node1 == current:
                        neighbors.append((edge.node2, edge.weight))
                    elif edge.node2 == current:
                        neighbors.append((edge.node1, edge.weight))
            
            for neighbor, weight in neighbors:
                if not neighbor.visited:
                    new_dist = current.distance + weight
                    if new_dist < neighbor.distance:
                        neighbor.distance = new_dist
                        neighbor.previous = current
                        heapq.heappush(pq, (new_dist, id(neighbor), neighbor))
            
            self.root.after(self.speed_var.get(), step)
        
        step()
    
    def show_results(self):
        reachable = []
        unreachable = []
        
        for node in self.nodes:
            if node == self.start_node:
                continue
            if node.distance == float('inf'):
                unreachable.append(node.label)
            else:
                reachable.append((node.label, node.distance))
        
        # Sort by distance
        reachable.sort(key=lambda x: x[1])
        
        result_msg = f"Dijkstra's Algorithm Complete!\n\n"
        result_msg += f"Source Node: {self.start_node.label}\n"
        result_msg += f"Graph Type: {'Directed' if self.is_directed.get() else 'Undirected'}\n\n"
        
        if reachable:
            result_msg += "✓ Reachable Nodes:\n"
            for label, dist in reachable:
                result_msg += f"  {self.start_node.label} → {label}: {dist:.1f}\n"
        
        if unreachable:
            result_msg += f"\n✗ Unreachable Nodes: {', '.join(unreachable)}\n"
            result_msg += "  (No path exists from source to these nodes)"
        
        self.info_label.config(text="Algorithm complete! Click 'Show Report' for detailed analysis.")
        messagebox.showinfo("Dijkstra Results", result_msg)
    
    def show_report(self):
        if not self.algorithm_complete:
            messagebox.showwarning("Warning", "Please run Dijkstra's algorithm first")
            return
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Dijkstra Algorithm - Detailed Report")
        report_window.geometry("700x600")
        report_window.transient(self.root)
        
        # Header
        header_frame = tk.Frame(report_window, bg="#2c3e50", pady=15)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="Shortest Path Report", 
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack()
        tk.Label(header_frame, text=f"Source Node: {self.start_node.label} | "
                                   f"Graph Type: {'Directed' if self.is_directed.get() else 'Undirected'}",
                font=("Arial", 11), bg="#2c3e50", fg="white").pack(pady=5)
        
        # Report content
        report_frame = tk.Frame(report_window)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrolled text widget
        report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, 
                                               font=("Courier", 10), padx=10, pady=10)
        report_text.pack(fill=tk.BOTH, expand=True)
        
        # Generate report content
        report = self.generate_report()
        report_text.insert(tk.END, report)
        report_text.config(state=tk.DISABLED)
        
        # Close button
        tk.Button(report_window, text="Close", command=report_window.destroy,
                 bg="#e74c3c", fg="white", font=("Arial", 11), padx=20, pady=5).pack(pady=10)
    
    def generate_report(self):
        report = "=" * 70 + "\n"
        report += "DIJKSTRA'S SHORTEST PATH ALGORITHM - ANALYSIS REPORT\n"
        report += "=" * 70 + "\n\n"
        
        report += f"Source Node: {self.start_node.label}\n"
        report += f"Total Nodes: {len(self.nodes)}\n"
        report += f"Total Edges: {len(self.edges)}\n"
        report += f"Graph Type: {'Directed' if self.is_directed.get() else 'Undirected'}\n"
        report += "\n" + "-" * 70 + "\n\n"
        
        # Reachable nodes
        reachable = []
        unreachable = []
        
        for node in self.nodes:
            if node == self.start_node:
                continue
            if node.distance == float('inf'):
                unreachable.append(node)
            else:
                reachable.append(node)
        
        reachable.sort(key=lambda x: x.distance)
        
        report += "SHORTEST DISTANCES FROM SOURCE\n"
        report += "-" * 70 + "\n\n"
        
        if reachable:
            report += f"{'Destination':<15} {'Distance':<15} {'Path':<40}\n"
            report += "-" * 70 + "\n"
            
            for node in reachable:
                # Reconstruct path
                path = []
                current = node
                while current:
                    path.append(current.label)
                    current = current.previous
                path.reverse()
                path_str = " → ".join(path)
                
                report += f"{node.label:<15} {node.distance:<15.1f} {path_str:<40}\n"
        else:
            report += "No reachable nodes found.\n"
        
        report += "\n" + "-" * 70 + "\n\n"
        
        # Unreachable nodes
        if unreachable:
            report += "UNREACHABLE NODES\n"
            report += "-" * 70 + "\n\n"
            report += "The following nodes cannot be reached from the source node:\n"
            report += ", ".join([node.label for node in unreachable]) + "\n\n"
            report += "Reason: No valid path exists from source to these nodes.\n"
            if self.is_directed.get():
                report += "Note: In a directed graph, check if edges point toward these nodes.\n"
        else:
            report += "ALL NODES ARE REACHABLE\n"
            report += "-" * 70 + "\n\n"
            report += "All nodes in the graph can be reached from the source node.\n"
        
        report += "\n" + "=" * 70 + "\n"
        report += "END OF REPORT\n"
        report += "=" * 70 + "\n"
        
        return report
    
    def reset_algorithm(self):
        for node in self.nodes:
            node.distance = float('inf')
            node.visited = False
            node.previous = None
        self.algorithm_complete = False
        self.report_btn.config(state=tk.DISABLED)
        self.info_label.config(text="Algorithm reset - Ready to run again")
        self.draw_graph()
    
    def clear_all(self):
        self.save_state()
        self.nodes = []
        self.edges = []
        self.start_node = None
        self.edge_start = None
        self.algorithm_complete = False
        self.report_btn.config(state=tk.DISABLED)
        self.info_label.config(text="Canvas cleared - Start adding nodes")
        self.draw_graph()

if __name__ == "__main__":
    root = tk.Tk()
    app = DijkstraVisualizer(root)
    root.mainloop()