"""
PDF on Submit. Creates a PDF when a document is submitted.
Copyright (C) 2019  Raffael Meyer <raffael@alyf.de>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import frappe
from frappe import _


def sales_invoice(doc, event=None):
    """Execute on_submit of Sales Invoice."""
    if frappe.get_single("PDF on Submit Settings").sales_invoice:
        enqueue({
            "doctype": "Sales Invoice",
            "name": doc.name,
            "party": doc.customer
        })


def delivery_note(doc, event=None):
    """Execute on_submit of Delivery Note."""
    if frappe.get_single("PDF on Submit Settings").delivery_note:
        enqueue({
            "doctype": "Delivery Note",
            "name": doc.name,
            "party": doc.customer
        })


def sales_order(doc, event=None):
    """Execute on_submit of Sales Order."""
    if frappe.get_single("PDF on Submit Settings").sales_order:
        enqueue({
            "doctype": "Sales Order",
            "name": doc.name,
            "party": doc.customer
        })


def quotation(doc, event=None):
    """Execute on_submit of Quotation."""
    if frappe.get_single("PDF on Submit Settings").quotation:
        enqueue({
            "doctype": "Quotation",
            "name": doc.name,
            "party": doc.party_name
        })


def dunning(doc, event=None):
    """Execute on_submit of Dunning."""
    if frappe.get_single("PDF on Submit Settings").dunning:
        enqueue({
            "doctype": "Dunning",
            "name": doc.name,
            "party": frappe.get_value("Sales Invoice", doc.sales_invoice, "customer")
        })


def enqueue(args):
    """Add method `execute` with given args to the queue."""
    frappe.enqueue(method=execute, queue='long',
                   timeout=30, is_async=True, **args)


def execute(doctype, name, party):
    """
    Queue calls this method, when it's ready.

    1. Create necessary folders
    2. Get raw PDF data
    3. Save PDF file and attach it to the document
    """
    doctype_folder = create_folder(_(doctype), "Home")
    party_folder = create_folder(party, doctype_folder)
    pdf_data = get_pdf_data(doctype, name)
    save_and_attach(pdf_data, doctype, name, party_folder)


def create_folder(folder, parent):
    """Make sure the folder exists and return it's name."""
    from frappe.core.doctype.file.file import create_new_folder
    try:
        create_new_folder(folder, parent)
    except frappe.DuplicateEntryError:
        pass

    return "/".join([parent, folder])


def get_pdf_data(doctype, name):
    """Document -> HTML -> PDF."""
    html = frappe.get_print(doctype, name)
    return frappe.utils.pdf.get_pdf(html)


def save_and_attach(content, to_doctype, to_name, folder):
    """
    Save content to disk and create a File document.

    File document is linked to another document.
    """
    from frappe.utils.file_manager import save_file
    file_name = "{}.pdf".format(to_name.replace(" ", "-").replace("/", "-"))
    save_file(file_name, content, to_doctype,
              to_name, folder=folder, is_private=1)
