# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import re
import math
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, get_first_day, today, get_last_day,cint
from frappe.model.naming import make_autoname
from hrms.hr.hr_custom_function import get_payroll_settings, get_salary_tax


class SalaryStructure(Document):
    def autoname(self):
        if not self.employee:
            frappe.throw(_("Employee field cannot be empty for autoname generation."))
        self.name = make_autoname(f"{self.employee}/.SST/.####")

    def validate(self):
        self.validate_dates()
        self.validate_amount()
        self.update_salary_structure()

    def validate_dates(self):
        joining_date, relieving_date = frappe.db.get_value(
            "Employee", self.employee, ["date_of_joining", "relieving_date"]
        )

        if self.from_date:
            existing_salary_structure = frappe.db.sql("""
                SELECT name FROM `tabSalary Structure`
                WHERE employee = %s
                AND is_active = 'Yes'
                AND from_date <= %s
                
            """, (self.employee, self.from_date), as_dict=True)

            if existing_salary_structure and existing_salary_structure[0]["name"] != self.name:
                frappe.throw(_("An active Salary Structure for this employee already exists."))

            if joining_date and getdate(self.from_date) < joining_date:
                frappe.throw(
                    _("From Date {0} cannot be before employee's joining Date {1}").format(
                        self.from_date, joining_date
                    )
                )

            # flag - old_employee is for migrating the old employees data via patch
            if relieving_date and getdate(self.from_date) > relieving_date and not self.flags.old_employee:
                frappe.throw(
                    _("From Date {0} cannot be after employee's relieving Date {1}").format(
                        self.from_date, relieving_date
                    )
                )

    def validate_amount(self):
        if flt(self.net_pay) < 0 and self.salary_slip_based_on_timesheet:
            frappe.throw(_("Net pay cannot be negative"))

    def validate_salary_component(self):
        dup = {}
        for parentfield in ['earnings', 'deductions']:
            parenttype = 'Earning' if parentfield == 'earnings' else 'Deduction'
            for i in self.get(parentfield):
                # Restricting users from entering earning component under deductions table and vice versa.
                component_type, is_loan_component = frappe.db.get_value("Salary Component", i.salary_component, ["type", "is_loan_component"])
                if parenttype != component_type:
                    frappe.throw(_('Salary Component <b>`{1}`</b> of type <b>`{2}`</b> cannot be added under <b>`{3}`</b> table. <br/> <b><u>Reference# : </u></b> <a href="#Form/Salary Structure/{0}">{0}</a>').format(
                        self.name, i.salary_component, component_type, parentfield.title()), title="Invalid Salary Component")
                # Checking duplicate entries
                if i.salary_component in ('Basic Pay') and i.salary_component in dup:
                    frappe.throw(_("Row#{0} : Duplicate entries not allowed for component <b>{1}</b>.")
                                 .format(i.idx, i.salary_component), title="Duplicate Record Found")
                else:
                    dup.update({i.salary_component: 1})

                # Validate Loan details
                if parenttype == 'Deduction' and cint(is_loan_component):
                    if not i.institution_name:
                        frappe.throw(_("Row#{}: <b>Institution Name</b> is mandatory for <b>{}</b>").format(i.idx, i.salary_component))
                    elif not i.reference_number:
                        frappe.throw(_("Row#{}: <b>Loan Account No.(Reference Number)</b> is mandatory for <b>{}</b>").format(i.idx, i.salary_component))

    def get_active_amount(self, rec):
        ''' return amount only if the component is active '''
        calc_amt = 0
        if rec.from_date or rec.to_date:
            if rec.to_date and str(rec.to_date) >= str(get_first_day(today())):
                calc_amt = rec.amount
            elif rec.from_date and str(rec.from_date) <= str(get_last_day(today())):
                calc_amt = rec.amount
            else:
                calc_amt = 0
        else:    
            calc_amt = rec.amount

        if rec.parentfield == "deductions":
            if not flt(rec.total_deductible_amount):
                calc_amt = calc_amt
            elif flt(rec.total_deductible_amount) and flt(rec.total_deductible_amount) != flt(rec.total_deducted_amount):
                calc_amt = calc_amt
            else:
                calc_amt = 0
                
        return flt(calc_amt)

    @frappe.whitelist()
    def update_salary_structure(self, new_basic_pay=0, remove_flag=1):
        '''
            This method calculates all the allowances and deductions based on the preferences
            set in the GUI. Calculated values are then checked and updated as follows.
                    1) If the calculated component is missing in the existing earnings/deductions
                        table then insert a new row.
                    2) If the calculated component is found in the existing earnings/deductions
                        table but amounts do not match, then update the respective row.
        '''
        self.validate_salary_component()

        basic_pay = comm_allowance = gis_amt = sws_amt = pf_amt = health_cont_amt = tax_amt = basic_pay_arrears = payscale_lower_limit= 0
        total_earning = total_deduction = net_pay = 0
        payscale_lower_limit = frappe.db.get_value("Employee Grade", frappe.db.get_value("Employee",self.employee,"grade"), "lower_limit")
        settings = get_payroll_settings(self.employee)
        settings = settings if settings else {}

        tbl_list = {'earnings': 'Earning', 'deductions': 'Deduction'}
        del_list_all = []
        
        for ed in ['earnings', 'deductions']:
            add_list = []
            del_list = []
            calc_map = []

            sst_map = {ed: []}
            for sc in frappe.db.sql("select * from `tabSalary Component` where `type`='{0}' and ifnull(field_name,'') != ''".format(tbl_list[ed]), as_dict=True):
                sst_map.setdefault(ed, []).append(sc)
            
            
            ed_map = [i.name for i in sst_map[ed]]
            for ed_item in self.get(ed):
                # validate component validity dates
                if ed_item.from_date and ed_item.to_date and str(ed_item.to_date) < str(ed_item.from_date):
                    frappe.throw(_("<b>Row#{}:</b> Invalid <b>From Date</b> for <b>{}</b> under <b>{}s</b>").format(ed_item.idx, ed_item.salary_component, tbl_list[ed]))

                ed_item.amount = roundoff(ed_item.amount)
                amount = ed_item.amount
            
                if ed_item.salary_component not in ed_map:
                    if ed == 'earnings':
                        if ed_item.salary_component == 'Basic Salary':
                            if flt(new_basic_pay) > 0 and flt(new_basic_pay) != flt(amount):
                                amount = flt(new_basic_pay)
                            basic_pay = amount
                            ed_item.amount = basic_pay
                            
                        elif frappe.db.exists("Salary Component", {"name": ed_item.salary_component, "is_pf_deductible": 1}):
                            basic_pay_arrears += flt(ed_item.amount)
                        total_earning += round(amount)
                        
                    else:
                        if flt(ed_item.total_deductible_amount) == 0:
                            total_deduction += amount
                        else:
                            if flt(ed_item.total_deductible_amount) != flt(ed_item.total_deducted_amount):
                                total_deduction += round(amount)
                else:
                    for m in sst_map[ed]:
                        if m['name'] == ed_item.salary_component and not self.get(m['field_name']):
                            del_list.append(ed_item)
                            del_list_all.append(ed_item)
            
            if remove_flag:
                [self.remove(d) for d in del_list]

            # Calculating Earnings and Deductions based on preferences and values set
            for m in sst_map[ed]:
                calc_amt = 0
                if self.get(m['field_method']) == 'Percent' and flt(self.get(m['field_value'])) < 0:
                    frappe.throw(
                        _("Percentage cannot be less than 0 for component <b>{0}</b>").format(m['name']), title="Invalid Data")
                elif self.get(m['field_method']) == 'Percent' and flt(self.get(m['field_value'])) > 200:
                    frappe.throw(
                        _("Percentage cannot exceed 200 for component <b>{0}</b>").format(m['name']), title="Invalid Data")

                if ed == 'earnings':
                    if self.get(m['field_name']):
                        if self.get(m["field_method"]) == 'Percent':
                            if m['based_on'] == 'Pay Scale Lower Limit':
                                calc_amt = flt(payscale_lower_limit)*flt(self.get(m['field_value']))*0.01
                            else:
                                calc_amt = flt(basic_pay)*flt(self.get(m['field_value']))*0.01
                        else:
                            calc_amt = flt(self.get(m['field_value']))

                        # Special handling for FA and HRA
                        if m["field_name"] == "eligible_for_fixed_allowance":
                            payment_method = frappe.db.get_value("Salary Component", "FA", "payment_method")
                            cal_based = frappe.db.get_value("Salary Component", "FA", "based_on")
                            amount = frappe.db.get_value("Salary Component", "FA", "amount")
                            if payment_method == 'Percent' and cal_based == 'Basic Pay' and amount:
                                calc_amt = (flt(basic_pay) * flt(amount) / 100)
                            if payment_method == 'Lumpsum' and amount:
                                calc_amt = (flt(amount))

                        if m["field_name"] == "eligible_for_hra":
                            payment_method = frappe.db.get_value("Salary Component", "HRA", "payment_method")
                            cal_based = frappe.db.get_value("Salary Component", "HRA", "based_on")
                            amount = frappe.db.get_value("Salary Component", "HRA", "amount")
                            if payment_method == 'Percent' and cal_based == 'Basic Pay' and amount:
                                calc_amt = (flt(basic_pay) * flt(amount) / 100)
                            if payment_method == 'Lumpsum' and amount:
                                calc_amt = (flt(amount))

                        calc_amt = roundoff(calc_amt)
                        comm_allowance += flt(calc_amt) if m['name'] == 'Communication Allowance' else 0
                        total_earning += calc_amt
                        calc_map.append({'salary_component': m['name'], 'amount': calc_amt})
                else:
                    if self.get(m['field_name']) and m['name'] == 'SWS':
                        sws_amt = flt(settings.get('sws'))
                        calc_amt = roundoff(sws_amt)
                        calc_map.append({'salary_component': m['name'], 'amount': flt(calc_amt)})

                    elif self.get(m['field_name']) and m['name'] == 'GIS':
                        gis_amt = flt(settings.get("gis"))
                        calc_amt = roundoff(gis_amt)
                        calc_map.append({'salary_component': m['name'], 'amount': flt(calc_amt)})

                    elif self.get(m['field_name']) and m['name'] == 'PF':
                        pf_amt = (flt(basic_pay)+flt(basic_pay_arrears))*flt(settings.get("employee_pf"))*0.01
                        calc_amt = roundoff(pf_amt)
                        calc_map.append({'salary_component': m['name'], 'amount': flt(calc_amt)})

                    elif self.get(m['field_name']) and m['name'] == 'Health Contribution':
                        health_cont_amt = flt(total_earning)*flt(settings.get("health_contribution"))*0.01
                        calc_amt = roundoff(health_cont_amt)
                        calc_map.append({'salary_component': m['name'], 'amount': flt(calc_amt)})
                    elif self.get(m['field_name']) and m['name'] == 'HRA':
                        payment_method = frappe.db.get_value("Salary Component", "HRA", "payment_method")
                        cal_based = frappe.db.get_value("Salary Component", "HRA", "based_on")
                        amount = frappe.db.get_value("Salary Component", "HRA", "amount")
                        if not payment_method or not cal_based or not amount:
                            frappe.throw('Add Payment Method, Calculation Based, Amount in salary component in HRA')
                        if payment_method == 'Percent' and cal_based == 'Basic Pay' and amount:
                            hra_amount = (flt(basic_pay) * flt(amount) / 100)
                        calc_amt = roundoff(hra_amount)
                        calc_map.append({'salary_component': m['name'], 'amount': flt(calc_amt)})
                    else:
                        calc_amt = 0
                    total_deduction += calc_amt

            # Calculating Salary Tax
            if ed == 'deductions':
                calc_amt = get_salary_tax(math.floor(flt(total_earning)-flt(pf_amt)-flt(gis_amt)-(comm_allowance*0.5)))
                calc_amt = roundoff(calc_amt)
                total_deduction += calc_amt
                calc_map.append({'salary_component': 'Salary Tax', 'amount': flt(calc_amt)})

            # Updating existing Earnings and Deductions tables
            for c in calc_map:
                found = 0
                for ed_item in self.get(ed):
                    if str(ed_item.salary_component) == str(c['salary_component']):
                        found = 1
                        if flt(ed_item.amount) != flt(c['amount']):
                            ed_item.amount = flt(c['amount'])
                        break

                if not found:
                    add_list.append(c)

            [self.append(ed, i) for i in add_list]
            
        self.total_earning   = sum([self.get_active_amount(rec) for rec in self.get("earnings")])
        self.total_deduction = sum([self.get_active_amount(rec) for rec in self.get("deductions")])
        self.net_pay = flt(self.total_earning) - flt(self.total_deduction)

        if flt(self.total_earning)-flt(self.total_deduction) < 0 and not self.get('__unsaved'):
            frappe.throw(_("Total deduction cannot be more than total earning"), title="Invalid Data")
        return del_list_all

def roundoff(amount):
    return math.ceil(amount) if (amount - int(amount)) >= 0.5 else math.floor(amount)