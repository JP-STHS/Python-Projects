#Finance App - Project Capstone

import tkinter as tk
import os
import sys
from tkinter import ttk
from tkinter import *
from tkinter import messagebox
from pymongo import MongoClient
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
import PlzIgnore


client = MongoClient("localhost", 27017)
db = client.FinanceAppDB
employees = db.Employees
payslips = db.Payslips
reimbursements = db.Reimbursements
logs = db.Logs

#Globals
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
from PIL import ImageGrab
import tempfile
import os

def print_window(root):
    # Get window coordinates
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = x + root.winfo_width()
    h = y + root.winfo_height()

    img_path = os.path.join(tempfile.gettempdir(), "finance_print.png")

    # Screenshot using ImageGrab
    screenshot = ImageGrab.grab(bbox=(x, y, w, h))
    screenshot.save(img_path)

    os.startfile(img_path, "print")



#Email function for reimbursement requests
def authenticate_interactively():
    """
    Run the interactive OAuth flow (opens browser) and write token.json.
    Use: python finance_app.py --auth
    """
    # this will open the browser for the user to sign in
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("Authentication complete: token.json created.")
    return creds

def get_sheets_service():
    """
    Returns a Sheets service with valid credentials.
    If no token.json exists or creds are invalid, automatically opens browser for OAuth.
    """
    creds = None

    # Load token if exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        except Exception:
            creds = None  # failed to refresh

    # If no creds or refresh failed, run interactive OAuth
    if not creds or not creds.valid:
        print("No valid credentials found. Opening browser for authentication...")
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Authentication complete: token.json created.")

    # Build the Sheets API service
    service = build('sheets', 'v4', credentials=creds)
    return service
    """
    Returns a Sheets service if valid credentials exist.
    If no token.json (or un-refreshable expiry) the function will exit the program
    unless allow_interactive is True (in which case it will start the browser flow).
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If creds are not present or not valid, try to refresh (if possible)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # save refreshed token
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Failed to refresh credentials: {e}")
                creds = None

    # No usable creds at this point
    if not creds:
        if allow_interactive:
            # interactive flow (useful when intentionally performing auth)
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            # Exit the program and instruct the operator how to authenticate
            print("No valid Google OAuth token found. The app will exit.")
            print("To authenticate, run this app with the --auth flag to open the browser and create token.json:")
            print("    python finance_app.py --auth")
            sys.exit(1)
    service = build('sheets', 'v4', credentials=creds)
    return service


def add_log(action, details):
	#Add a new log entry to log db
	logs.insert_one({
		"Action": action,
		"Details": details,
		"Timestamp": datetime.now()
	})
def cleanup_old_logs():
	cutoff = datetime.now() - timedelta(days=90)
	logs.delete_many({"Timestamp": {"$lt": cutoff}})
cleanup_old_logs()
def try_parse_timestamp(ts_str):
	from dateutil import parser
	try:
		parser.parse(ts_str)
		return True
	except Exception:
		return False

def refresh_inbox(self):
	"""Fetch the latest form responses from the linked Google Sheet and display them."""
	self.request_list.delete(0, tk.END)

	try:
		# Get data from Google Sheets
		items = fetch_form_responses()
	except Exception as e:
		self.request_list.insert(tk.END, f"Error reading form data: {e}")
		self.after(60000, self.refresh_inbox)  # retry every minute
		return

	if not items:
		self.request_list.insert(tk.END, "No new form responses.")
	else:
		# Show newest first
		for ts, emp, desc, amt, link in reversed(items):
			display_line = f"{ts} | ID: {emp} | {desc} | ${amt if amt else ''}"
			self.request_list.insert(tk.END, display_line)

	self.after(60000, self.refresh_inbox)

def fetch_form_responses():
	"""
	Read responses from linked Google Sheet and insert new reimbursements.
	Returns list of tuples for display: (timestamp_str, emp_id, description, amount, image_link)
	"""
	service = get_sheets_service()
	SPREADSHEET_ID = PlzIgnore.GLOBAL_SPREADSHEET_ID 
	RANGE_NAME = PlzIgnore.GLOBAL_RANGE_NAME

	result = service.spreadsheets().values().get(
		spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME
	).execute()
	rows = result.get('values', [])

	display_items = []

	if not rows or len(rows) <= 1:
		return display_items

	header = rows[0]  # keep for reference
	for idx, row in enumerate(rows[1:], start=2):  # start=2 (row numbers are 1-indexed in Sheets)
		# Defensive indexing
		timestamp = row[0] if len(row) > 0 else None
		emp_id = row[1] if len(row) > 1 else None
		description = row[2] if len(row) > 2 else None
		amount = row[3] if len(row) > 3 else None
		image_link = row[4] if len(row) > 4 else None

		if not (timestamp and emp_id and description):
			# skip incomplete responses
			continue

		# create a deterministic unique key for this response: timestamp + emp_id + description
		unique_key = f"{timestamp}|{emp_id}|{description}"

		# store unique_key on each reimbursements entry so we can detect duplicates
		if reimbursements.find_one({"FormKey": unique_key}):
			# already stored
			continue

		# Insert to DB
		entry = {
			"EmployeeID": int(emp_id) if emp_id.isdigit() else emp_id,
			"Description": description,
			"Amount": amount,
			"ImagePath": image_link,
			"DateReceived": datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S") if try_parse_timestamp(timestamp) else datetime.now(),
			"Status": "Pending",
			"FormKey": unique_key,
			"SheetRow": idx
		}
		reimbursements.insert_one(entry)
		add_log("New Reimbursement (Form)", f"Employee {emp_id} submitted '{description}' (${amount})")

		# prepare display tuple
		display_items.append((timestamp, emp_id, description, amount, image_link))

	return display_items



# Finance App
class FinanceApp(tk.Tk):
	def __init__(self):
		super().__init__()
		
		self.bind("<Control-p>", lambda e: print_window(self))
		
		self.title("Finance Application")
		self.geometry("900x800")

		# Container for all pages
		container = ttk.Frame(self)
		container.pack(fill="both", expand=True)

		self.frames = {}
		for Page in (HomePage, PayslipPage, TransactionPage, EmployeePage, ReimbursementForms):
			frame = Page(container, self)
			self.frames[Page] = frame
			frame.grid(row=0, column=0, sticky="nsew")

		self.show_frame(HomePage)

	def show_frame(self, page_class):
		"""Raise the selected frame to the front."""
		frame = self.frames[page_class]
		frame.tkraise()


# -------------------- Pages --------------------

class HomePage(ttk.Frame):
	def __init__(self, parent, controller):
		super().__init__(parent)
		# Title
		title_label = ttk.Label(
			self,
			text="Finance Application",
			font=("Arial", 40, "bold"),
			anchor="center"
		)
		title_label.pack(pady=10)

		main_frame = ttk.Frame(self, padding=5)
		main_frame.pack(fill="both", expand=True)

		# ---------------- Left Frame ----------------
		left_frame = ttk.Frame(main_frame)
		left_frame.pack(side="left", expand=True, padx=20)

		incoming_btn = tk.Button(
			left_frame,
			text="Incoming Requests",
			bg="dodgerblue",
			fg="white",
			font=("Arial", 12, "bold"),
			width=40, height=3,
			command=lambda: controller.show_frame(ReimbursementForms)
		)
		incoming_btn.pack(pady=5)

		self.request_list = tk.Listbox(
			left_frame,
			width=50,
			height=20,
			font=("Arial", 11),
			fg="black",
			bg="white"
		)
		self.request_list.pack()

		self.request_list.bind("<Double-Button-1>", lambda e: controller.show_frame(ReimbursementForms))
		self._mail_ids = []

		self.refresh_inbox()  # initial fetch

		# ---------------- Right Frame ----------------
		right_frame = ttk.Frame(main_frame)
		right_frame.pack(side="right", expand=True, padx=20)

		payslip_btn = tk.Button(
			right_frame,
			text="View Payslips",
			bg="dodgerblue",
			fg="white",
			font=("Arial", 12, "bold"),
			width=40, height=3,
			command=lambda: controller.show_frame(PayslipPage)
		)
		payslip_btn.pack(pady=20)

		transaction_btn = tk.Button(
			right_frame,
			text="View Logs",
			bg="dodgerblue",
			fg="white",
			font=("Arial", 12, "bold"),
			width=40, height=3,
			command=lambda: controller.show_frame(TransactionPage)
		)
		transaction_btn.pack(pady=20)
		
		employees_btn = tk.Button(
			right_frame,
			text="Manage Employees",
			bg="dodgerblue",
			fg="white",
			font=("Arial", 12, "bold"),
			width=40, height=3,
			command=lambda: controller.show_frame(EmployeePage)
		)
		employees_btn.pack(pady=20)
	def refresh_inbox(self):
		"""Display latest pending reimbursements from DB."""
		self.request_list.delete(0, tk.END)

		pending = list(reimbursements.find({"Status": "Pending"}).sort("DateReceived", -1).limit(10))

		if not pending:
			self.request_list.insert(tk.END, "No pending reimbursement requests.")
		else:
			for r in pending:
				line = f"{r['DateReceived'].strftime('%Y-%m-%d')} | ID {r['EmployeeID']} | {r['Description']} | ${r['Amount']}"
				self.request_list.insert(tk.END, line)

		# Auto-refresh every 60 seconds
		self.after(60000, self.refresh_inbox)




class PayslipPage(ttk.Frame):
	def __init__(self, parent, controller):
		super().__init__(parent)
		self.controller = controller

		label = ttk.Label(self, text="Payslip Page", font=("Arial", 30))
		label.pack(pady=20)

		self.refresh_btn = ttk.Button(self, text="Refresh Payslips", command=self.refresh_payslips)
		self.refresh_btn.pack(pady=10)

		# Scrollable frame setup
		container = ttk.Frame(self)
		container.pack(fill="both", expand=True, padx=20, pady=10)

		canvas = tk.Canvas(container)
		scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
		self.scrollable_frame = ttk.Frame(canvas)

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
		)

		canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)

		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		back_btn = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(HomePage))
		back_btn.pack(pady=10)

		# Schedule updates
		self.after(500, self.auto_generate_and_cleanup)
		self.refresh_payslips()

	def auto_generate_and_cleanup(self):
		"""Generate new payslips and clean old ones."""
		self.generate_payslips()
		self.cleanup_old_payslips()
		self.refresh_payslips()

	def generate_payslips(self):
		"""Generate payslips every 2 weeks for active employees."""
		now = datetime.now()
		for emp in employees.find({"Status": "Active"}):
			last_payslip = payslips.find_one(
				{"EmployeeID": emp["EmployeeID"]},
				sort=[("PayDate", -1)]
			)
			if not last_payslip or (now - last_payslip["PayDate"]).days >= 14:
				new_payslip = {
					"EmployeeID": emp["EmployeeID"],
					"Name": f"{emp['FirstName']} {emp['LastName']}",
					"Department": emp["Department"],
					"JobTitle": emp["JobTitle"],
					"Salary": emp["YearlySalary"],
					"PayDate": now,
				}
				payslips.insert_one(new_payslip)

	def cleanup_old_payslips(self):
		"""Delete payslips older than 6 weeks."""
		cutoff = datetime.now() - timedelta(weeks=6)
		payslips.delete_many({"PayDate": {"$lt": cutoff}})

	def refresh_payslips(self):
		"""Refresh the payslip list in the scrollable frame."""
		for widget in self.scrollable_frame.winfo_children():
			widget.destroy()

		all_payslips = list(payslips.find().sort("PayDate", -1))

		if not all_payslips:
			ttk.Label(self.scrollable_frame, text="No payslips available.").pack()
			return

		for p in all_payslips:
			frame = ttk.Frame(self.scrollable_frame, relief="ridge", padding=10)
			frame.pack(fill="x", pady=5)

			info = f"Employee {p['EmployeeID']} - {p['Name']} | Pay Date: {p['PayDate'].strftime('%Y-%m-%d')}"
			ttk.Label(frame, text=info).pack(side="left", padx=5)

			view_btn = ttk.Button(frame, text="View Payslip", command=lambda pid=p["_id"]: self.open_payslip_window(pid))
			view_btn.pack(side="right", padx=5)

	def open_payslip_window(self, payslip_id):
		"""Placeholder window for viewing a single payslip."""
		payslip = payslips.find_one({"_id": payslip_id})
		if not payslip:
			messagebox.showerror("Error", "Payslip not found.")
			return

		win = tk.Toplevel(self)
		win.title(f"Payslip for {payslip['Name']}")
		win.configure(bg="white")
		win.geometry("700x400")
		
		windfram = tk.Frame(win)
		windfram.grid(row=0,column=0,columnspan=2,sticky=EW)
		windfram.configure(background="#C9FEC0")
		ttk.Label(windfram, text=f"Payslip for {payslip['Name']}", font=("Arial", 20, "bold"),background="#C9FEC0").grid(padx=185, row=0,column=0,columnspan=2, pady=30)
		ttk.Label(win, text=f"Department: {payslip['Department']}", font=("Arial", 15),background="white").grid(padx=30, row=1, column=0)
		ttk.Label(win, text=f"Job Title: {payslip['JobTitle']}",font=("Arial", 15),background="white").grid(padx=30, row=1,column=1)
		ttk.Label(win, text=f"Payment: ${round(int(payslip['Salary'])/26)}",font=("Arial", 15),background="white").grid(row=2,column=0)
		ttk.Label(win, text=f"Pay Date: {payslip['PayDate'].strftime('%Y-%m-%d')}",font=("Arial", 15),background="white").grid(row=2,column=1)

		ttk.Button(win, text="Close", command=win.destroy).grid(pady=100,row=3,column=0,columnspan=2)


class TransactionPage(ttk.Frame):
	def __init__(self, parent, controller):
		super().__init__(parent)
		label = ttk.Label(self, text="Transaction Logs", font=("Arial", 30))
		label.pack(pady=20)

		refresh_btn = ttk.Button(self, text="Refresh Logs", command=self.display_logs)
		refresh_btn.pack(pady=10)

		# Scrollable area
		container = ttk.Frame(self)
		container.pack(fill="both", expand=True, padx=20, pady=10)

		canvas = tk.Canvas(container)
		scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
		self.scrollable_frame = ttk.Frame(canvas)

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
		)

		canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)

		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		back_btn = tk.Button(self, text="Back to Home",
							 command=lambda: controller.show_frame(HomePage))
		back_btn.pack(pady=10)

		self.display_logs()

	def display_logs(self):
		"""Show last 50 actions."""
		for widget in self.scrollable_frame.winfo_children():
			widget.destroy()

		recent_logs = list(logs.find().sort("Timestamp", -1).limit(50))

		if not recent_logs:
			ttk.Label(self.scrollable_frame, text="No logs yet.").pack()
			return

		for log in recent_logs:
			frame = ttk.Frame(self.scrollable_frame, relief="ridge", padding=8)
			frame.pack(fill="x", pady=4)
			text = f"[{log['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] {log['Action']} - {log['Details']}"
			ttk.Label(frame, text=text, wraplength=800, justify="left").pack(anchor="w")


class EmployeePage(ttk.Frame):
	def __init__(self, parent, controller):
		super().__init__(parent)
		label = ttk.Label(self, text="Employee Management Page", font=("Arial", 30))
		label.pack(pady=50)
		main_frame = ttk.Frame(self, padding=5)
		main_frame.pack(fill="both", expand=True)

		# Left side
		left_frame = ttk.Frame(main_frame)
		left_frame.pack(side="left", expand=True, padx=20)
		add_label = ttk.Label(left_frame, text="Add Employee", font=("Arial", 20), padding=4)
		add_label.pack()
		# First Name
		emp_id = ttk.Label(left_frame, text="Enter an ID")
		emp_identry = ttk.Entry(left_frame)
		emp_id.pack(),emp_identry.pack()
		fname_label = ttk.Label(left_frame, text="First Name:")
		fname_entry = ttk.Entry(left_frame)
		fname_label.pack()
		fname_entry.pack()
		lname_label = ttk.Label(left_frame, text="Last Name:")
		lname_entry = ttk.Entry(left_frame)
		lname_label.pack()
		lname_entry.pack()
		dept_label = ttk.Label(left_frame, text="Department:")
		dept_entry = ttk.Entry(left_frame)
		dept_label.pack()
		dept_entry.pack()
		job_label = ttk.Label(left_frame, text="Job Title:")
		job_entry = ttk.Entry(left_frame)
		job_label.pack()
		job_entry.pack()
		email_label = ttk.Label(left_frame, text="Email:")
		email_entry = ttk.Entry(left_frame)
		email_label.pack()
		email_entry.pack()
		phone_label = ttk.Label(left_frame, text="Phone:")
		phone_entry = ttk.Entry(left_frame)
		phone_label.pack()
		phone_entry.pack()
		addr_label = ttk.Label(left_frame, text="Address:")
		addr_entry = ttk.Entry(left_frame)
		addr_label.pack()
		addr_entry.pack()
		emerg_contact_label = ttk.Label(left_frame, text="Emergency Contact:")
		emerg_contact_entry = ttk.Entry(left_frame)
		emerg_contact_label.pack()
		emerg_contact_entry.pack()
		emerg_phone_label = ttk.Label(left_frame, text="Emergency Phone:")
		emerg_phone_entry = ttk.Entry(left_frame)
		emerg_phone_label.pack()
		emerg_phone_entry.pack()
		hire_label = ttk.Label(left_frame, text="Hire Date (YYYY-MM-DD):")
		hire_entry = ttk.Entry(left_frame)
		hire_label.pack()
		hire_entry.pack()
		salary_label = ttk.Label(left_frame, text="Yearly Salary:")
		salary_entry = ttk.Entry(left_frame)
		salary_label.pack()
		salary_entry.pack()
		status_label = ttk.Label(left_frame, text="Status:")
		status_entry = ttk.Entry(left_frame)
		status_label.pack()
		status_entry.pack()
		def save_employee():
			emp_identity = emp_identry.get().strip()
			fname = fname_entry.get().strip()
			lname = lname_entry.get().strip()
			dept = dept_entry.get().strip()
			job = job_entry.get().strip()
			email = email_entry.get().strip()
			phone = phone_entry.get().strip()
			addr = addr_entry.get().strip()
			emerg_contact = emerg_contact_entry.get().strip()
			emerg_phone = emerg_phone_entry.get().strip()
			hire_date = hire_entry.get().strip()
			salary = salary_entry.get().strip()
			status = status_entry.get().strip()

			errors = []
			if not emp_identity or not emp_identity.isdigit():
				errors.append("Please enter a valid ID")
			elif employees.find_one({"EmployeeID": int(emp_identity)}):
				errors.append("Employee with this ID already exists!")

			if not fname:
				errors.append("First name required.")
			if not lname:
				errors.append("Last name required.")
			if not dept:
				errors.append("Department required.")
			if not job:
				errors.append("Job Title required.")
			if not email or "@" not in email:
				errors.append("Invalid email.")
			if not phone or not phone.isdigit():
				errors.append("Phone must be digits only.")
			if not addr:
				errors.append("Address required.")
			if not emerg_contact:
				errors.append("Emergency contact required.")
			if not emerg_phone or not emerg_phone.isdigit():
				errors.append("Emergency phone must be digits only.")
			if not salary or not salary.isdigit():
				errors.append("Salary must be a number.")
			if not status or not (status.lower() in ["active", "terminated", "on leave"]):
				errors.append("Status must be Active, Terminated, or On Leave.")

			# Quick date check
			import datetime
			try:
				datetime.datetime.strptime(hire_date, "%Y-%m-%d")
			except ValueError:
				errors.append("Hire date must be YYYY-MM-DD.")

			if errors:
				messagebox.showerror("Validation Error", "\n".join(errors))
			else:
				employees.insert_one({
					"EmployeeID": int(emp_identity),
					"FirstName": fname,
					"LastName": lname,
					"Department": dept,
					"JobTitle": job,
					"Email": email,
					"Phone": phone,
					"Address": addr,
					"EmergencyContact": emerg_contact,
					"EmergencyPhone": emerg_phone,
					"HireDate": hire_date,
					"YearlySalary": int(salary),
					"Status": status
				})
				add_log("Add Employee", f"Employee {fname} {lname} (ID: {emp_identity}) was added.")
				messagebox.showinfo("Success", f"Employee {fname} {lname} saved!")


		add_btn = tk.Button(
			left_frame, text="Add Employee", command=save_employee)
		add_btn.pack(pady=8)
		#right side
		right_frame = ttk.Frame(main_frame)
		right_frame.pack(side="right", expand=True, padx=20)
		
		add_label2 = ttk.Label(right_frame, text="Configure Employee", font=("Arial", 20), padding=4)
		add_label2.pack()
		# First Name
		emp_id2 = ttk.Label(right_frame, text="Enter an ID")
		emp_identry2 = ttk.Entry(right_frame)
		emp_id2.pack(),emp_identry2.pack()
		fname_label2 = ttk.Label(right_frame, text="Change First Name:")
		fname_entry2 = ttk.Entry(right_frame)
		fname_label2.pack()
		fname_entry2.pack()
		lname_label2 = ttk.Label(right_frame, text="Change Last Name:")
		lname_entry2 = ttk.Entry(right_frame)
		lname_label2.pack()
		lname_entry2.pack()
		dept_label2 = ttk.Label(right_frame, text="Change Department:")
		dept_entry2 = ttk.Entry(right_frame)
		dept_label2.pack()
		dept_entry2.pack()
		job_label2 = ttk.Label(right_frame, text="Change Job Title:")
		job_entry2 = ttk.Entry(right_frame)
		job_label2.pack()
		job_entry2.pack()
		email_label2 = ttk.Label(right_frame, text="Change Email:")
		email_entry2 = ttk.Entry(right_frame)
		email_label2.pack()
		email_entry2.pack()
		phone_label2 = ttk.Label(right_frame, text="Change Phone:")
		phone_entry2 = ttk.Entry(right_frame)
		phone_label2.pack()
		phone_entry2.pack()
		addr_label2 = ttk.Label(right_frame, text="Change Address:")
		addr_entry2 = ttk.Entry(right_frame)
		addr_label2.pack()
		addr_entry2.pack()
		emerg_contact_label2 = ttk.Label(right_frame, text="Change Emergency Contact:")
		emerg_contact_entry2 = ttk.Entry(right_frame)
		emerg_contact_label2.pack()
		emerg_contact_entry2.pack()
		emerg_phone_label2 = ttk.Label(right_frame, text="Change Emergency Phone:")
		emerg_phone_entry2 = ttk.Entry(right_frame)
		emerg_phone_label2.pack()
		emerg_phone_entry2.pack()
		hire_label2 = ttk.Label(right_frame, text="Change Hire Date (YYYY-MM-DD):")
		hire_entry2 = ttk.Entry(right_frame)
		hire_label2.pack()
		hire_entry2.pack()
		salary_label2 = ttk.Label(right_frame, text="Change Yearly Salary:")
		salary_entry2 = ttk.Entry(right_frame)
		salary_label2.pack()
		salary_entry2.pack()
		status_label2 = ttk.Label(right_frame, text="Change Status:")
		status_entry2 = ttk.Entry(right_frame)
		status_label2.pack()
		status_entry2.pack()
		def manage_employee():
			emp_id_val = emp_identry2.get().strip()

			# Validation
			if not emp_id_val or not emp_id_val.isdigit():
				messagebox.showerror("Error", "Please enter a valid numeric Employee ID.")
				return

			emp_id_val = int(emp_id_val)
			employee = employees.find_one({"EmployeeID": emp_id_val})
			if not employee:
				messagebox.showerror("Error", "Employee ID not found!")
				return

			update_data = {}

			if fname_entry2.get().strip():
				update_data["FirstName"] = fname_entry2.get().strip()

			if lname_entry2.get().strip():
				update_data["LastName"] = lname_entry2.get().strip()

			if dept_entry2.get().strip():
				update_data["Department"] = dept_entry2.get().strip()

			if job_entry2.get().strip():
				update_data["JobTitle"] = job_entry2.get().strip()

			if email_entry2.get().strip():
				if "@" not in email_entry2.get():
					messagebox.showerror("Error", "Invalid email format.")
					return
				update_data["Email"] = email_entry2.get().strip()

			if phone_entry2.get().strip():
				if not phone_entry2.get().isdigit():
					messagebox.showerror("Error", "Phone must be digits only.")
					return
				update_data["Phone"] = phone_entry2.get().strip()

			if addr_entry2.get().strip():
				update_data["Address"] = addr_entry2.get().strip()

			if emerg_contact_entry2.get().strip():
				update_data["EmergencyContact"] = emerg_contact_entry2.get().strip()

			if emerg_phone_entry2.get().strip():
				if not emerg_phone_entry2.get().isdigit():
					messagebox.showerror("Error", "Emergency phone must be digits only.")
					return
				update_data["EmergencyPhone"] = emerg_phone_entry2.get().strip()

			if hire_entry2.get().strip():
				import datetime
				try:
					datetime.datetime.strptime(hire_entry2.get().strip(), "%Y-%m-%d")
				except ValueError:
					messagebox.showerror("Error", "Hire date must be YYYY-MM-DD.")
					return
				update_data["HireDate"] = hire_entry2.get().strip()

			if salary_entry2.get().strip():
				if not salary_entry2.get().isdigit():
					messagebox.showerror("Error", "Salary must be a number.")
					return
				update_data["YearlySalary"] = int(salary_entry2.get().strip())

			if status_entry2.get().strip():
				if status_entry2.get().lower() not in ["active", "terminated", "on leave"]:
					messagebox.showerror("Error", "Status must be Active, Terminated, or On Leave.")
					return
				update_data["Status"] = status_entry2.get().strip()

			if update_data:
				employees.update_one({"EmployeeID": emp_id_val}, {"$set": update_data})
				add_log("Update Employee", f"Employee ID {emp_id_val} updated: {list(update_data.keys())}")
				messagebox.showinfo("Success", f"Employee {emp_id_val} updated!")
			else:
				messagebox.showwarning("Warning", "No fields were updated.")

		manage_btn = tk.Button(
			right_frame, text="Change Employee", command=manage_employee)
		manage_btn.pack(pady=8)
		
		#middle bottom
		back_btn = tk.Button(
			self, text="Back to Home", command=lambda: controller.show_frame(HomePage)
		)
		back_btn.pack()
		
class ReimbursementForms(ttk.Frame):
	def __init__(self, parent, controller):
		super().__init__(parent)
		self.controller = controller

		label = ttk.Label(self, text="Reimbursement Requests", font=("Arial", 30))
		label.pack(pady=20)

		refresh_btn = ttk.Button(self, text="Fetch Reimbursement Forms", command=self.fetch_and_display)
		refresh_btn.pack(pady=10)

		container = ttk.Frame(self)
		container.pack(fill="both", expand=True, padx=20, pady=10)

		canvas = tk.Canvas(container)
		scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
		self.scrollable_frame = ttk.Frame(canvas)

		self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
		canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)

		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		back_btn = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(HomePage))
		back_btn.pack(pady=10)

		self.display_reimbursements()

	def fetch_and_display(self):
		fetch_form_responses()
		self.display_reimbursements()


	def display_reimbursements(self):
		for widget in self.scrollable_frame.winfo_children():
			widget.destroy()

		data = list(reimbursements.find().sort("DateReceived", -1))

		if not data:
			ttk.Label(self.scrollable_frame, text="No reimbursement requests found.").pack()
			return

		for r in data:
			frame = ttk.Frame(self.scrollable_frame, relief="ridge", padding=10)
			frame.pack(fill="x", pady=5)

			info = f"Employee {r['EmployeeID']} - {r['Description']} | Date: {r['DateReceived'].strftime('%Y-%m-%d')} | Status: {r['Status']}"
			ttk.Label(frame, text=info).pack(side="left", padx=5)

			view_btn = ttk.Button(frame, text="View Receipt", command=lambda path=r['ImagePath']: os.startfile(path))
			view_btn.pack(side="right", padx=5)


# Run the app
if __name__ == "__main__":
    # Allow running just the OAuth once with --auth
    if len(sys.argv) > 1 and sys.argv[1] == "--auth":
        # This will open the browser and create token.json, then exit
        authenticate_interactively()
        sys.exit(0)

    # Normal app run: get_sheets_service() will exit if no token.json exists
    app = FinanceApp()
    app.mainloop()
