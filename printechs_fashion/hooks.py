app_name = "printechs_fashion"
app_title = "Printechs Fashion"
app_publisher = "Printechs"
app_description = "Printechs Fashion"
app_email = "thomas@printechs.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "printechs_fashion",
# 		"logo": "/assets/printechs_fashion/logo.png",
# 		"title": "Printechs Fashion",
# 		"route": "/printechs_fashion",
# 		"has_permission": "printechs_fashion.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/printechs_fashion/css/printechs_fashion.css"
# app_include_js = "/assets/printechs_fashion/js/printechs_fashion.js"

# include js, css files in header of web template
# web_include_css = "/assets/printechs_fashion/css/printechs_fashion.css"
# web_include_js = "/assets/printechs_fashion/js/printechs_fashion.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "printechs_fashion/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "printechs_fashion/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------


# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "printechs_fashion.utils.jinja_methods",
# 	"filters": "printechs_fashion.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "printechs_fashion.install.before_install"
# after_install = "printechs_fashion.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "printechs_fashion.uninstall.before_uninstall"
# after_uninstall = "printechs_fashion.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "printechs_fashion.utils.before_app_install"
# after_app_install = "printechs_fashion.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "printechs_fashion.utils.before_app_uninstall"
# after_app_uninstall = "printechs_fashion.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "printechs_fashion.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
    "Item Attribute Value": {
        "on_update": "printechs_fashion.api.insert_item_attribute_value"
    },
   "Sales Order": {
        "on_submit": "printechs_fashion.animo_connector.enqueue_animo_order_sync",
        "on_cancel": "printechs_fashion.animo_connector.enqueue_animo_order_cancel"
    },
   "Sales Invoice": {
        "on_submit": [ 
            "printechs_fashion.animo_connector.enqueue_animo_invoice_sync",          
            "printechs_fashion.update_status.on_submit_si"
        ],        
        "on_cancel": [
            "printechs_fashion.update_status.on_submit_si"
        ]
    },    
     "Delivery Note": {
        "on_submit": "printechs_fashion.update_status.on_submit_dn",
        "on_cancel": "printechs_fashion.update_status.on_submit_dn"
    }
}

after_migrate = "printechs_fashion.animo_connector.setup_custom_fields"
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"printechs_fashion.tasks.all"
# 	],
# 	"daily": [
# 		"printechs_fashion.tasks.daily"
# 	],
# 	"hourly": [
# 		"printechs_fashion.tasks.hourly"
# 	],
# 	"weekly": [
# 		"printechs_fashion.tasks.weekly"
# 	],
# 	"monthly": [
# 		"printechs_fashion.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "printechs_fashion.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "printechs_fashion.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "printechs_fashion.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["printechs_fashion.utils.before_request"]
# after_request = ["printechs_fashion.utils.after_request"]

# Job Events
# ----------
# before_job = ["printechs_fashion.utils.before_job"]
# after_job = ["printechs_fashion.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"printechs_fashion.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["name", "in", ("Sales Order Item-custom_return_status","Sales Order-custom_return_status","custom_dcs", "custom_vendor_cost","custom_exchange_rate","custom_vendor_currency","custom_vendor_name","custom_vendor_code","custom_column_break_vbtwc","custom_bin_no","custom_image_url","custom_material","custom_style_code","custom_fashion","custom_item_name_ar")]]
    }
]