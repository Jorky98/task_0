import json
import polars as pl

def generate_fully_interactive_report(dm, df):
    # Převod na dict s ošetřením datumu (default=str)
    # Polars -> JSON přímo (rychlejší než přes Pandas)
    transactions_json = json.dumps(df.to_dicts(), default=str)
    daily_metrics_json = json.dumps(dm.daily_metrics_df.to_dicts(), default=str)
    
    available_regions = json.dumps(dm.filters_config.availableRegions)
    available_categories = json.dumps(dm.filters_config.availableCategories)
    available_segments = json.dumps(getattr(dm.filters_config, 'availableSegments', ["Enterprise", "SMB", "Individual"]))

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Business Intelligence Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            :root {{ 
                --st-sidebar: #f0f2f6; 
                --st-primary: #ff4b4b; 
                --sidebar-width: 300px; 
            }}
            body {{ background-color: #ffffff; display: flex; min-height: 100vh; font-family: "Source Sans Pro", sans-serif; color: #31333F; }}
            #sidebar {{ width: var(--sidebar-width); background: var(--st-sidebar); padding: 40px 20px; position: fixed; height: 100vh; overflow-y: auto; border-right: 1px solid rgba(49, 51, 63, 0.1); }}
            #main-content {{ margin-left: var(--sidebar-width); flex: 1; padding: 60px; max-width: 1200px; }}
            .card {{ border: 1px solid rgba(49, 51, 63, 0.1); border-radius: 8px; box-shadow: none; margin-bottom: 20px; }}
            .kpi-card {{ padding: 20px; text-align: left; border-left: 5px solid var(--st-primary); }}
            .kpi-label {{ font-size: 0.9rem; color: #555; font-weight: 400; }}
            .kpi-value {{ font-size: 1.8rem; font-weight: 700; color: #31333F; }}
            .chart-box {{ height: 400px; width: 100%; }}
            .nav-tabs .nav-link {{ color: #31333F; border: none; font-weight: 600; opacity: 0.6; }}
            .nav-tabs .nav-link.active {{ opacity: 1; border-bottom: 3px solid var(--st-primary) !important; background: none; }}
            .btn-primary {{ background-color: var(--st-primary); border: none; padding: 10px; font-weight: 600; }}
        </style>
    </head>
    <body>

    <div id="sidebar">
        <h4 class="mb-4 fw-bold">Filters</h4>
        <div class="mb-4"><label class="fw-bold small text-muted">REGION</label><div id="region-filters" class="mt-2"></div></div>
        <div class="mb-4"><label class="fw-bold small text-muted">CATEGORY</label><div id="category-filters" class="mt-2"></div></div>
        <div class="mb-4"><label class="fw-bold small text-muted">SEGMENT</label><div id="segment-filters" class="mt-2"></div></div>
        <button class="btn btn-primary w-100" onclick="applyFilters()">Update Dashboard</button>
    </div>

    <div id="main-content">
        <h1 class="fw-bold mb-5">Business Performance Dashboard</h1>
        
        <div class="row g-4 mb-4">
            <div class="col-md-3"><div class="card kpi-card"><div class="kpi-label">Total Revenue</div><div id="kpi-rev" class="kpi-value">$0</div></div></div>
            <div class="col-md-3"><div class="card kpi-card"><div class="kpi-label">Avg Order Value</div><div id="kpi-aov" class="kpi-value">$0</div></div></div>
            <div class="col-md-3"><div class="card kpi-card"><div class="kpi-label">Top Region</div><div id="kpi-region" class="kpi-value">-</div></div></div>
            <div class="col-md-3"><div class="card kpi-card"><div class="kpi-label">Top Category</div><div id="kpi-cat" class="kpi-value">-</div></div></div>
        </div>

        <div class="card mb-4"><div id="line-chart" class="chart-box"></div></div>
        <div class="row g-4 mb-4">
            <div class="col-md-6"><div class="card p-2"><div id="cat-pie-chart" class="chart-box"></div></div></div>
            <div class="col-md-6"><div class="card p-2"><div id="reg-bar-chart" class="chart-box"></div></div></div>
        </div>

        <ul class="nav nav-tabs mb-4">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-summary">Summary</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-trans">Transactions</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-daily">Daily Metrics</button></li>
        </ul>
        
        <div class="tab-content">
            <div class="tab-pane fade show active" id="tab-summary">
                <div class="card p-4"><table class="table align-middle"><tbody id="summary-body"></tbody></table></div>
            </div>
            <div class="tab-pane fade" id="tab-trans">
                <div class="card p-4"><table id="txnTable" class="table table-hover w-100"><thead><tr><th>Id</th><th>Date</th><th>Timestamp</th><th>Amount</th><th>Product</th><th>Product id</th><th>Category</th><th>Region</th><th>Customer</th><th>Payment method</th><th>Status</th><th>Segment</th></tr></thead></table></div>
            </div>
            <div class="tab-pane fade" id="tab-daily">
                <div class="card p-4"><table id="dailyTable" class="table table-hover w-100"><thead><tr><th>Date</th><th>Revenue</th><th>Orders</th><th>Active Users</th><th>New Users</th><th>Conversion Rate</th><th>Average Order Value</th><th>Churn Rate</th></tr></thead></table></div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        const rawData = {transactions_json};
        const rawDaily = {daily_metrics_json};
        let txnTable, dailyTable;

        function initFilters() {{
            const setup = (list, containerId, cls) => {{
                const container = document.getElementById(containerId);
                list.forEach(item => {{
                    container.innerHTML += `<div class="form-check"><input class="form-check-input ${{cls}}" type="checkbox" value="${{item}}" checked id="${{item}}"><label class="form-check-label small" for="${{item}}">${{item}}</label></div>`;
                }});
            }};
            setup({available_regions}, 'region-filters', 'reg-check');
            setup({available_categories}, 'category-filters', 'cat-check');
            setup({available_segments}, 'segment-filters', 'seg-check');
        }}

        function applyFilters() {{
            const selReg = new Set(Array.from(document.querySelectorAll('.reg-check:checked')).map(cb => cb.value));
            const selCat = new Set(Array.from(document.querySelectorAll('.cat-check:checked')).map(cb => cb.value));
            const selSeg = new Set(Array.from(document.querySelectorAll('.seg-check:checked')).map(cb => cb.value));

            const filtered = rawData.filter(d => 
                selReg.has(d.region) && selCat.has(d.category) && selSeg.has(d.segment)
            );
            updateDashboard(filtered);
        }}

        function getTop(data, key) {{
            const counts = {{}};
            data.forEach(d => counts[d[key]] = (counts[d[key]] || 0) + d.amount);
            const entries = Object.entries(counts).sort((a,b) => b[1] - a[1]);
            return entries.length > 0 ? entries[0] : [ 'N/A', 0 ];
        }}

        function updateDashboard(data) {{
            const completed = data.filter(d => d.status.toLowerCase() === 'completed');
            const totalRevenue = completed.reduce((s, d) => s + d.amount, 0);
            const aov = completed.length > 0 ? totalRevenue / completed.length : 0;
            const uniqueCust = new Set(data.map(d => d.customer_id)).size;
            
            const refundedCount = data.filter(d => d.status && d.status.toLowerCase() === 'refunded').length;
            const refundRate = data.length > 0 ? (refundedCount / data.length) * 100 : 0;

            const avgConvRate = rawDaily.length > 0 
                ? (rawDaily.reduce((s, d) => s + (d.conversionRate || 0), 0) / rawDaily.length) * 100 
                : 0;

            const topRegData = getTop(completed, 'region');
            const topCatData = getTop(completed, 'category');

            // KPI Update
            document.getElementById('kpi-rev').innerText = '$' + (totalRevenue/1e6).toFixed(2) + 'M';
            document.getElementById('kpi-aov').innerText = '$' + aov.toLocaleString(undefined, {{maximumFractionDigits:0}});
            document.getElementById('kpi-region').innerText = topRegData[0];
            document.getElementById('kpi-cat').innerText = topCatData[0];

            // Summary Table
            document.getElementById('summary-body').innerHTML = `
<tr><td class="fw-bold">Total Revenue</td><td class="text-end">$${{totalRevenue.toLocaleString()}}</td></tr>
                <tr><td class="fw-bold">Average Order Value</td><td class="text-end">$${{aov.toLocaleString(undefined, {{maximumFractionDigits:2}})}}</td></tr>
                <tr><td class="fw-bold">Conversion Rate</td><td class="text-end">${{avgConvRate.toFixed(2)}}%</td></tr>
                <tr><td class="fw-bold">Total Customers</td><td class="text-end">${{uniqueCust}}</td></tr>
                <tr><td class="fw-bold">Refund Rate</td><td class="text-end">${{refundRate.toFixed(2)}}%</td></tr>
                <tr><td class="fw-bold">Top Region</td><td class="text-end">${{topRegData[0]}}</td></tr>
                <tr><td class="fw-bold">Top Category</td><td class="text-end">${{topCatData[0]}}</td></tr>
            `;

            const layout = {{ margin: {{ t: 40, b: 40, l: 50, r: 30 }}, font: {{ family: 'Source Sans Pro' }} }};
            
            // Line Chart
            Plotly.react('line-chart', [{{ 
                x: data.map(d=>d.date), y: data.map(d=>d.amount), 
                type: 'scattergl', mode: 'lines', line: {{color: '#ff4b4b'}} 
            }}], {{ title: 'Revenue Trend', ...layout }}, {{responsive: true}});

            // Pie Chart -> CATEGORY
            const catCounts = {{}};
            completed.forEach(d => catCounts[d.category] = (catCounts[d.category] || 0) + d.amount);
            Plotly.react('cat-pie-chart', [{{
                values: Object.values(catCounts),
                labels: Object.keys(catCounts),
                type: 'pie', hole: .4
            }}], {{ title: 'Revenue by Category', ...layout }}, {{responsive: true}});

            // Bar Chart -> REGION
            const regCounts = {{}};
            completed.forEach(d => regCounts[d.region] = (regCounts[d.region] || 0) + d.amount);
            const sortedReg = Object.entries(regCounts)
                .sort((a, b) => b[1] - a[1]); // b[1] - a[1] pro sestupné řazení

            const regLabels = sortedReg.map(x => x[0]);
            const regValues = sortedReg.map(x => x[1]);

            const colors = [
                '#ff4b4b', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ];

            Plotly.react('reg-bar-chart', [{{
                x: regLabels,
                y: regValues,
                type: 'bar',
                marker: {{
                    color: colors.slice(0, regLabels.length) // Každý sloupec dostane svou barvu
                }}
            }}], {{ title: 'Revenue by Region', ...layout }}, {{responsive: true}});

            // DataTables
            if(txnTable) txnTable.destroy();
            txnTable = $('#txnTable').DataTable({{
                data: data,
                columns: [{{data:'id'}}, {{data:'date'}}, {{data:'timestamp'}}, {{data:'amount'}}, {{data:'product'}}, {{data:'productId'}}, {{data:'category'}}, {{data:'region'}}, {{data:'customer.id'}}, {{data:'paymentMethod'}}, {{data:'status'}}, {{data:'segment'}}],
                pageLength: 10, deferRender: true
            }});

            if(dailyTable) dailyTable.destroy();
            dailyTable = $('#dailyTable').DataTable({{
                data: rawDaily,
                columns: [{{data:'date'}}, {{data:'revenue'}}, {{data:'orders'}}, {{data:'activeUsers'}}, {{data:'newUsers'}}, {{data:'conversionRate'}}, {{data:'averageOrderValue'}}, {{data:'churnRate'}}],
                pageLength: 10, deferRender: true
            }});
        }}

        initFilters();
        applyFilters();

        // Fix pro resize grafů při přepnutí tabu
        document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(el => {{
            el.addEventListener('shown.bs.tab', () => {{ window.dispatchEvent(new Event('resize')); }});
        }});
    </script>
    </body>
    </html>
    """
    return html_content