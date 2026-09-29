"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
import streamlit as st

from payroll.compute import build_payroll, payroll_export
from payroll.extract import load_employees, load_timesheet


st.title("Salt City Coffee — Weekly Payroll")
st.write("Upload this week's timesheet to review payroll and prepare the provider export.")

uploaded_file = st.file_uploader(
	"Upload timesheet CSV",
	type="csv",
	key="timesheet",
)

if uploaded_file is not None:
	timesheet = load_timesheet(uploaded_file)
	payroll = build_payroll(timesheet, load_employees())
	payroll_date = payroll["payroll_date"].iloc[0]
	st.subheader(f"Pay period ending {payroll_date}")

	payable = payroll[payroll["pay_type"] != "unmatched"]
	overtime = payroll[payroll["pay_type"] == "overtime"]
	metric_columns = st.columns(4)
	metric_columns[0].metric("Employees paid", len(payable))
	metric_columns[1].metric("Total hours", f"{payroll['hours_worked'].sum():.2f}")
	metric_columns[2].metric("Total gross pay", f"${payroll['gross_pay'].sum():,.2f}")
	metric_columns[3].metric("Overtime weeks", len(overtime))

	unmatched_ids = payroll.loc[
		payroll["pay_type"] == "unmatched", "employee_id"
	].unique().tolist()
	if unmatched_ids:
		st.warning(f"Unmatched employee IDs: {', '.join(unmatched_ids)}")
	else:
		st.success("All timesheet employees matched the roster.")

	st.dataframe(payroll)
	export_csv = payroll_export(payroll).to_csv(index=False)
	st.download_button(
		"Download payroll CSV",
		data=export_csv,
		file_name=f"payroll_{payroll_date}.csv",
		mime="text/csv",
		key="download",
	)
