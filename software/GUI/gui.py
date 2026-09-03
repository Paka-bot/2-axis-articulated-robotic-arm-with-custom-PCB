import tkinter as tk
from tkinter import messagebox, scrolledtext
import serial
import time
import math

class MotorDebugger:
    def __init__(self, root):
        self.root = root
        self.root.title("2-Axis SCARA Arm Control GUI")
        self.root.geometry("500x900")
        
        self.serial_port = None
        self.is_stopped = False
        self.setup_ui()

    def setup_ui(self):
        f_conn = tk.Frame(self.root)
        f_conn.pack(pady=5)
        tk.Label(f_conn, text="COM Port:").pack(side="left")
        self.port_entry = tk.Entry(f_conn, width=10)
        self.port_entry.insert(0, "COM3")
        self.port_entry.pack(side="left", padx=5)
        tk.Button(f_conn, text="Connect", command=self.connect, bg="#3498DB", fg="white").pack(side="left")

        self.create_motor_frame("Motor 1 control", "M1")
        self.create_motor_frame("Motor 2 control", "M2")

        f_sync = tk.LabelFrame(self.root, text="Multiple motor control", font=("Arial", 10, "bold"))
        f_sync.pack(fill="x", padx=10, pady=5)
        
        combos = [
            ("M1 +180, M2 -180", "M1 180 M2 -180"), ("M1 -180, M2 +180", "M1 -180 M2 180"),
            ("M1 +90, M2 -90", "M1 90 M2 -90"),     ("M1 -90, M2 +90", "M1 -90 M2 90"),
            ("M1 +45, M2 -45", "M1 45 M2 -45"),     ("M1 -45, M2 +45", "M1 -45 M2 45"),
            ("M1 +10, M2 -10", "M1 10 M2 -10"),     ("M1 -10, M2 +10", "M1 -10 M2 10")
        ]
        
        for i, (text, cmd) in enumerate(combos):
            row = i // 2
            col = i % 2
            tk.Button(f_sync, text=text, command=lambda c=cmd: self.send_cmd(c)).grid(row=row, column=col, padx=5, pady=2, sticky="ew")
        
        f_sync.grid_columnconfigure(0, weight=1)
        f_sync.grid_columnconfigure(1, weight=1)

        f_power = tk.Frame(self.root)
        f_power.pack(pady=5)
        tk.Button(f_power, text="Motor ON", command=lambda: self.send_cmd("M6"), bg="#2ECC71", width=15).pack(side="left", padx=5)
        tk.Button(f_power, text="Motor OFF", command=lambda: self.send_cmd("M2"), bg="#E74C3C", fg="white", width=15).pack(side="left", padx=5)

        f_draw = tk.LabelFrame(self.root, text="Drawing a Line", font=("Arial", 10, "bold"))
        f_draw.pack(fill="x", padx=10, pady=5)
        
        tk.Label(f_draw, text="Length (inches):").grid(row=0, column=0, padx=5, pady=5)
        self.line_entry = tk.Entry(f_draw, width=8)
        self.line_entry.insert(0, "4")
        self.line_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(f_draw, text="Draw clockwise", command=lambda: self.draw_line("left"), bg="#E67E22", fg="white").grid(row=0, column=2, padx=5)
        tk.Button(f_draw, text="Draw counterclockwise", command=lambda: self.draw_line("right"), bg="#9B59B6", fg="white").grid(row=0, column=3, padx=5)

        f_log = tk.LabelFrame(self.root, text="G-code Command Log ", font=("Arial", 10, "bold"))
        f_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_box = scrolledtext.ScrolledText(f_log, height=5, bg="black", fg="lime")
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_box.config(state='disabled')

    def create_motor_frame(self, title, motor_id):
        frame = tk.LabelFrame(self.root, text=title, font=("Arial", 10, "bold"))
        frame.pack(fill="x", padx=10, pady=5)
        vals_neg = [-180, -90, -45, -10, -1]
        vals_pos = [1, 10, 45, 90, 180]
        
        for i, val in enumerate(vals_neg):
            tk.Button(frame, text=f"{val}°", width=6, command=lambda v=val: self.move(motor_id, v)).grid(row=0, column=i, padx=2, pady=2)
        for i, val in enumerate(vals_pos):
            tk.Button(frame, text=f"+{val}°", width=6, command=lambda v=val: self.move(motor_id, v)).grid(row=1, column=i, padx=2, pady=2)

    def connect(self):
        try:
            self.serial_port = serial.Serial(self.port_entry.get().upper(), 115200, timeout=1)
            time.sleep(2)
            messagebox.showinfo("Connection successful. Connected via the ESP32 and COM3 port.")
        except Exception as e:
            messagebox.showerror("Error", f"Connection Failed: {e}")

    def send_cmd(self, cmd):
        if "M2" in cmd and "M1" not in cmd:
            self.is_stopped = True
        elif "M6" in cmd:
            self.is_stopped = False

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.reset_input_buffer()
            self.serial_port.write((cmd + '\n').encode())
            
            self.log_box.config(state='normal')
            self.log_box.insert(tk.END, f"Sent ➡️ {cmd}\n")
            self.log_box.see(tk.END)
            self.log_box.config(state='disabled')

    def move(self, motor, angle):
        if motor == "M1":
            cmd = f"M1 {angle} M2 0"
        else:
            cmd = f"M1 0 M2 {angle}"
        self.send_cmd(cmd)

    def calc_angles(self, x, y):
        L1, L2 = 150.0, 120.0
        cos_t2 = (x**2 + y**2 - L1**2 - L2**2) / (2 * L1 * L2)
        cos_t2 = max(-1.0, min(1.0, cos_t2))
        t2 = -math.acos(cos_t2)
        alpha = math.atan2(y, x)
        B = math.atan2(L2 * math.sin(t2), L1 + L2 * math.cos(t2))
        t1 = alpha - B
        return math.degrees(t1), math.degrees(t2)

    def draw_line(self, direction):
        if not self.serial_port or not self.serial_port.is_open:
            return

        try: length_in = float(self.line_entry.get())
        except ValueError: return

        start_x = 150.0
        start_y = 150.0
        length_mm = length_in * 25.4
        
        segments = int(length_mm * 2) 
        if segments < 10: segments = 10

        self.is_stopped = False

        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, f"=== {length_in}인치 {direction} Start drawing a straight line. ===\n")
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

        prev_t1, prev_t2 = self.calc_angles(start_x, start_y)
        current_step1 = round(prev_t1 * (1600.0 / 360.0))
        current_step2 = round(prev_t2 * (1600.0 / 360.0))

        for i in range(1, segments + 1):
            if self.is_stopped:
                self.log_box.config(state='normal')
                self.log_box.insert(tk.END, "The emergency stop button has been pressed by the user.\n")
                self.log_box.see(tk.END)
                self.log_box.config(state='disabled')
                break

            if direction == "right":
                target_x = start_x + (length_mm * i / segments)
            else:
                target_x = start_x - (length_mm * i / segments) 
                
            target_y = start_y 

            new_t1, new_t2 = self.calc_angles(target_x, target_y)

            target_step1 = round(new_t1 * (1600.0 / 360.0))
            target_step2 = round(new_t2 * (1600.0 / 360.0))

            d_step1 = target_step1 - current_step1
            d_step2 = target_step2 - current_step2

            if d_step1 == 0 and d_step2 == 0:
                continue

            d_t1 = d_step1 * (360.0 / 1600.0)
            d_t2 = d_step2 * (360.0 / 1600.0)

            cmd = f"M1 {d_t1:.4f} M2 {d_t2:.4f}"
            
            self.serial_port.reset_input_buffer()
            self.serial_port.write((cmd + '\n').encode())

            self.log_box.config(state='normal')
            self.log_box.insert(tk.END, f"Straight line drawing coordinates ➡️ {cmd}\n")
            self.log_box.see(tk.END)
            self.log_box.config(state='disabled')

            while True:
                if self.is_stopped:
                    break
                if self.serial_port.in_waiting > 0:
                    resp = self.serial_port.readline().decode('utf-8').strip()
                    if resp in ["OK", "ON", "OFF"]:
                        break
                self.root.update() 
                time.sleep(0.001)

            current_step1 = target_step1
            current_step2 = target_step2

        if not self.is_stopped:
            self.log_box.config(state='normal')
            self.log_box.insert(tk.END, "=== Line drawing complete===\n")
            self.log_box.see(tk.END)
            self.log_box.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorDebugger(root)
    root.mainloop()