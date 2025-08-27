import tkinter as tk
from app import BboxCoordinatesPicker

if __name__ == "__main__":
    root = tk.Tk()
    app = BboxCoordinatesPicker(root)
    root.mainloop()