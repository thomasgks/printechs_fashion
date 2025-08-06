frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 || frm.doc.docstatus === 2) { // Ensure it's a submitted Sales Order
            frm.add_custom_button(__('Send to Animo'), function() {
                frappe.call({
                    method: 'printechs_fashion.animo_connector.send_sales_order_to_animo',
                    args: {
                        doc: frm.doc,
                        method: 'on_submit'
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__('Sales Order sent to Animo.'));
                        }
                    }
                });
            }, __('Create'));
        }
    }
});
