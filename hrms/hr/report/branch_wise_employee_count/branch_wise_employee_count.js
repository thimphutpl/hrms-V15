// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.query_reports["Branch Wise Employee Count"] = {
// 	"filters": [

// 	]
// };


// Copyright (c) 2026
// For license information, please see license.txt

frappe.query_reports["Branch Wise Employee Count"] = {
    filters: [
        {
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Branch",
            reqd: 0
        }
    ],

    add_total_row: 1,

    onload: function () {
        schedule_summary_formatting();
    },

    after_datatable_render: function () {
        schedule_summary_formatting();
    },

    formatter: function (
        value,
        row,
        column,
        data,
        default_formatter
    ) {
        value = default_formatter(
            value,
            row,
            column,
            data
        );

        if (!data) {
            return value;
        }

        if (column.fieldname === "branch") {
            return `<strong>${value}</strong>`;
        }

        if (column.fieldname === "employee_total") {
            return `
                <strong style="color:#2563eb;">
                    ${value}
                </strong>
            `;
        }

        if (column.fieldname === "total_employees") {
            return `
                <strong style="color:#169c46;">
                    ${value}
                </strong>
            `;
        }

        return value;
    }
};


function schedule_summary_formatting() {
    // Run more than once because Frappe may render the summary
    // slightly later than the report table.
    setTimeout(format_summary_sections, 200);
    setTimeout(format_summary_sections, 500);
    setTimeout(format_summary_sections, 900);
}


function format_summary_sections() {
    const report = frappe.query_report;

    if (!report || !report.page || !report.page.main) {
        return;
    }

    add_summary_styles();

    const $summary = report.page.main
        .find(".report-summary")
        .first();

    if (!$summary.length) {
        return;
    }

    // Already formatted and section containers still exist.
    if (
        $summary.hasClass("employee-summary-formatted")
        && $summary.find(".employee-summary-section").length
    ) {
        return;
    }

    // Remove a stale marker after a Frappe report refresh.
    $summary.removeClass("employee-summary-formatted");

    const $items = $summary.children(".summary-item");

    if (!$items.length) {
        return;
    }

    let otherSectionIndex = -1;

    $items.each(function (index) {
        const label = $(this)
            .find(".summary-label")
            .text()
            .trim()
            .toUpperCase();

        if (label === "OTHER EMPLOYEES TOTAL") {
            otherSectionIndex = index;
            return false;
        }
    });

    if (otherSectionIndex === -1) {
        return;
    }

    const $employeeSection = $(`
        <div class="employee-summary-section employee-main-section">
            <div class="employee-section-title">
                EMPLOYEE
            </div>

            <div class="employee-section-items"></div>
        </div>
    `);

    const $otherSection = $(`
        <div class="employee-summary-section other-employees-section">
            <div class="employee-section-title">
                OTHER EMPLOYEES
            </div>

            <div class="employee-section-items"></div>
        </div>
    `);

    const $employeeItems = $employeeSection.find(
        ".employee-section-items"
    );

    const $otherItems = $otherSection.find(
        ".employee-section-items"
    );

    $items.each(function (index) {
        if (index < otherSectionIndex) {
            $employeeItems.append(this);
        } else {
            $otherItems.append(this);
        }
    });

    $summary.empty();
    $summary.append($employeeSection);
    $summary.append($otherSection);

    $summary.addClass("employee-summary-formatted");
}


function add_summary_styles() {
    const styleId =
        "branch-wise-employee-summary-style";

    if (document.getElementById(styleId)) {
        return;
    }

    const style = document.createElement("style");

    style.id = styleId;

    style.innerHTML = `
        .report-summary.employee-summary-formatted {
            display: block !important;
            width: 100% !important;
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            padding: 0 !important;
            overflow: visible !important;
            background: transparent !important;
        }

        .employee-summary-section {
            display: block !important;
            width: 100% !important;
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            margin: 0 0 16px !important;
            padding: 16px 18px 18px !important;
            overflow: visible !important;
            box-sizing: border-box !important;
            background: #f8fbff;
            border: 1px solid #dbeafe;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
        }

        .employee-summary-section.other-employees-section {
            background: #fffaf2;
            border-color: #fed7aa;
            border-left-color: #f59e0b;
        }

        .employee-section-title {
            display: block;
            width: 100%;
            margin: 0 0 14px;
            padding: 0 0 8px;
            border-bottom: 1px solid #dbeafe;
            color: #1d4ed8;
            font-size: 14px;
            font-weight: 700;
            line-height: 20px;
            letter-spacing: 0.5px;
        }

        .other-employees-section
        .employee-section-title {
            color: #b45309;
            border-bottom-color: #fed7aa;
        }

        .employee-section-items {
            display: grid !important;
            grid-template-columns:
                repeat(auto-fit, minmax(120px, 1fr));
            gap: 14px !important;
            width: 100% !important;
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
            align-items: start !important;
            box-sizing: border-box !important;
        }

        .employee-section-items .summary-item {
            display: block !important;
            position: relative !important;
            width: auto !important;
            min-width: 0 !important;
            height: auto !important;
            min-height: 75px !important;
            max-height: none !important;
            margin: 0 !important;
            padding: 6px !important;
            overflow: visible !important;
            box-sizing: border-box !important;
            text-align: center !important;
        }

        .employee-section-items .summary-label {
            display: block !important;
            width: 100% !important;
            height: auto !important;
            min-height: 36px !important;
            max-height: none !important;
            margin: 0 0 5px !important;
            padding: 0 !important;
            overflow: visible !important;
            white-space: normal !important;
            word-break: normal !important;
            overflow-wrap: anywhere !important;
            text-overflow: unset !important;
            line-height: 17px !important;
            text-align: center !important;
        }

        .employee-section-items .summary-value {
            display: block !important;
            position: static !important;
            width: 100% !important;
            height: auto !important;
            min-height: 28px !important;
            max-height: none !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
            white-space: normal !important;
            line-height: 28px !important;
            font-size: 20px !important;
            font-weight: 600 !important;
            text-align: center !important;
        }

        @media (max-width: 992px) {
            .employee-section-items {
                grid-template-columns:
                    repeat(3, minmax(0, 1fr)) !important;
            }
        }

        @media (max-width: 768px) {
            .employee-summary-section {
                padding: 14px 10px !important;
            }

            .employee-section-items {
                grid-template-columns:
                    repeat(2, minmax(0, 1fr)) !important;
            }
        }

        @media (max-width: 420px) {
            .employee-section-items {
                grid-template-columns:
                    1fr !important;
            }
        }
    `;

    document.head.appendChild(style);
}