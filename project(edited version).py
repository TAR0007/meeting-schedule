import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict


# ---------- Core Scheduler Logic ----------
def parse_time(t):
    return datetime.strptime(t, "%H:%M").time()

def read_schedules(csv_file):
    df = pd.read_csv(csv_file)
    schedules = defaultdict(list)
    for _, row in df.iterrows():
        schedules[(row["member_name"], row["day_of_week"].capitalize())].append(
            (parse_time(row["start_time_24h"]), parse_time(row["end_time_24h"]))
        )
    return schedules

def intersect_intervals(intervals_list):
    if not intervals_list:
        return []
    common = intervals_list[0]
    for intervals in intervals_list[1:]:
        new_common = []
        for s1, e1 in common:
            for s2, e2 in intervals:
                start = max(s1, s2)
                end = min(e1, e2)
                if start < end:
                    new_common.append((start, end))
        common = new_common
        if not common:
            return []
    return common

def generate_slots(intervals, duration_minutes):
    slots = []
    delta = timedelta(minutes=duration_minutes)
    for start, end in intervals:
        start_dt = datetime.combine(datetime.today(), start)
        end_dt = datetime.combine(datetime.today(), end)
        while start_dt + delta <= end_dt:
            slots.append((start_dt.time().strftime("%H:%M"),
                          (start_dt + delta).time().strftime("%H:%M")))
            start_dt += delta
    return slots

def find_meeting_slots(csv_file, duration_minutes):
    schedules = read_schedules(csv_file)
    days = {day for _, day in schedules.keys()}
    members = {m for m, _ in schedules.keys()}
    results = {}
    for day in days:
        member_intervals = []
        for m in members:
            if (m, day) not in schedules:
                break
            member_intervals.append(schedules[(m, day)])
        else:
            common = intersect_intervals(member_intervals)
            slots = generate_slots(common, duration_minutes)
            if slots:
                results[day] = slots
    return results


# ---------- Tkinter UI ----------
class MeetingSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IEEE TEMS Meeting Scheduler")
        self.root.geometry("600x400")

        # File path variable
        self.csv_path = tk.StringVar()

        # File input
        tk.Label(root, text="CSV File:").pack(pady=5)
        file_frame = tk.Frame(root)
        file_frame.pack(pady=5)
        self.file_entry = tk.Entry(file_frame, textvariable=self.csv_path, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        # Meeting duration
        tk.Label(root, text="Meeting Duration (minutes):").pack(pady=5)
        self.duration_entry = tk.Entry(root)
        self.duration_entry.insert(0, "60")
        self.duration_entry.pack(pady=5)

        # Run button
        tk.Button(root, text="Find Slots", command=self.run_scheduler).pack(pady=10)

        # Results box
        self.result_box = tk.Text(root, wrap="word", height=15, width=70)
        self.result_box.pack(pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv_path.set(file_path)

    def run_scheduler(self):
        csv_file = self.csv_path.get()
        if not csv_file:
            messagebox.showerror("Error", "Please select a CSV file.")
            return
        try:
            duration = int(self.duration_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Meeting duration must be an integer.")
            return
        try:
            slots = find_meeting_slots(csv_file, duration)
            self.result_box.delete(1.0, tk.END)
            if not slots:
                self.result_box.insert(tk.END, "No common slots found.\n")
            else:
                for day, times in slots.items():
                    self.result_box.insert(tk.END, f"{day}:\n")
                    for s, e in times:
                        self.result_box.insert(tk.END, f"  {s} - {e}\n")
                    self.result_box.insert(tk.END, "\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = MeetingSchedulerApp(root)
    root.mainloop()
