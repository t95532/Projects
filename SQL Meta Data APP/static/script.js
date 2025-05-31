const dbSelect = document.getElementById('dbSelect');
const tableSelect = document.getElementById('tableSelect');
const columnTableBody = document.getElementById('columnTableBody');
const rowCountDisplay = document.getElementById('rowCount');
const colCountDisplay = document.getElementById('colCount');
const viewSelect = document.getElementById('viewSelect');
const procSelect = document.getElementById('procSelect');
const procDefinition = document.getElementById('procDefinition');
const viewDefinition = document.getElementById('viewDefinition');
const viewTableBody = document.getElementById('viewTableBody');
const sampleTableHead = document.getElementById('sampleTableHead');
const sampleTableBody = document.getElementById('sampleTableBody');


const spinnerHTML = '<div class="spinner"></div>';

async function loadDatabases() {
  const res = await fetch('/databases');
  const dbs = await res.json();
  dbSelect.innerHTML = '';
  dbs.forEach(db => {
    const option = document.createElement('option');
    option.value = db;
    option.textContent = db;
    dbSelect.appendChild(option);
  });
  loadTables();
}

async function loadTables() {
  const db = dbSelect.value;
  const res = await fetch(`/tables?database=${db}`);
  const tables = await res.json();
  tableSelect.innerHTML = '';
  tables.forEach(table => {
    const option = document.createElement('option');
    option.value = table;
    option.textContent = table;
    tableSelect.appendChild(option);
  });
  loadColumns();
  loadStats();
}

async function loadColumns() {
  const db = dbSelect.value;
  const table = tableSelect.value;

  // Optional: show loading row in table body
  columnTableBody.innerHTML = `
    <tr><td colspan="3" style="text-align:center;"><div class="spinner"></div></td></tr>
  `;

  try {
    const res = await fetch(`/columns?database=${db}&table=${table}`);
    const columns = await res.json();
    columnTableBody.innerHTML = '';
    columns.forEach(col => {
      const row = document.createElement('tr');
      row.innerHTML = `<td>${col.name}</td><td>${col.type}</td><td>${col.nullable ? 'YES' : 'NO'}</td>`;
      columnTableBody.appendChild(row);
    });
  } catch (err) {
    console.error(err);
    columnTableBody.innerHTML = '<tr><td colspan="3">Failed to load columns.</td></tr>';
  }
}

async function loadStats() {
  const db = dbSelect.value;
  const table = tableSelect.value;

  // Show spinner during loading
  rowCountDisplay.innerHTML = spinnerHTML;
  colCountDisplay.innerHTML = spinnerHTML;

  try {
    const res = await fetch(`/stats?database=${db}&table=${table}`);
    const stats = await res.json();
    rowCountDisplay.textContent = stats.rows;
    colCountDisplay.textContent = stats.columns;
  } catch (err) {
    console.error(err);
    rowCountDisplay.textContent = 'Error';
    colCountDisplay.textContent = 'Error';
  }
}

// Event listeners
dbSelect.addEventListener('change', loadTables);
tableSelect.addEventListener('change', () => {
  loadColumns();
  loadStats();
});

async function loadViews() {
  const db = dbSelect.value;
  const res = await fetch(`/views?database=${db}`);
  const views = await res.json();
  viewSelect.innerHTML = '';
  views.forEach(view => {
    const option = document.createElement('option');
    option.value = view;
    option.textContent = view;
    viewSelect.appendChild(option);
  });
}

async function loadStoredProcedures() {
  const db = dbSelect.value;
  const res = await fetch(`/stored_procedures?database=${db}`);
  const procs = await res.json();
  procSelect.innerHTML = '';
  procs.forEach(proc => {
    const option = document.createElement('option');
    option.value = proc;
    option.textContent = proc;
    procSelect.appendChild(option);
  });
}

async function loadProcedureDefinition() {
  const db = dbSelect.value;
  const proc = procSelect.value;
  procDefinition.textContent = 'Loading...';

  try {
    const res = await fetch(`/procedure_definition?database=${db}&procedure=${encodeURIComponent(proc)}`);
    const data = await res.json();
    procDefinition.textContent = data.definition || 'Definition not found';
  } catch (err) {
    procDefinition.textContent = 'Error loading definition';
  }
}
async function loadViewDefinition() {
  const db = dbSelect.value;
  const view = viewSelect.value;
  viewDefinition.textContent = 'Loading...';

  try {
    const res = await fetch(`/view_definition?database=${db}&view=${encodeURIComponent(view)}`);
    const data = await res.json();
    viewDefinition.textContent = data.definition || 'Definition not found';
  } catch (err) {
    viewDefinition.textContent = 'Error loading definition';
  }
}

async function loadTables() {
  const db = dbSelect.value;
  const res = await fetch(`/tables?database=${db}`);
  const tables = await res.json();
  tableSelect.innerHTML = '';
  tables.forEach(table => {
    const option = document.createElement('option');
    option.value = table;
    option.textContent = table;
    tableSelect.appendChild(option);
  });

  loadColumns();
  loadStats();
  loadViews();
  loadStoredProcedures();
}
// Event listeners for views and stored procedures
async function loadSampleData() {
  const db = dbSelect.value;
  const table = tableSelect.value;

  sampleTableHead.innerHTML = '';
  sampleTableBody.innerHTML = `<tr><td colspan="100%" style="text-align:center;"><div class="spinner"></div></td></tr>`;

  try {
    const res = await fetch(`/sample_data?database=${db}&table=${table}&limit=10`);
    const data = await res.json();

    if (data.error) {
      sampleTableBody.innerHTML = `<tr><td colspan="100%">Error: ${data.error}</td></tr>`;
      return;
    }

    const { columns, rows } = data;

    // Header
    sampleTableHead.innerHTML = '<tr>' + columns.map(col => `<th>${col}</th>`).join('') + '</tr>';

    // Rows
    sampleTableBody.innerHTML = '';
    rows.forEach(row => {
      const tr = document.createElement('tr');
      tr.innerHTML = columns.map(col => `<td>${row[col] != null ? row[col] : ''}</td>`).join('');
      sampleTableBody.appendChild(tr);
    });
  } catch (err) {
    sampleTableBody.innerHTML = '<tr><td colspan="100%">Error loading data</td></tr>';
  }
}
tableSelect.addEventListener('change', loadSampleData);

procSelect.addEventListener('change', loadProcedureDefinition);
viewSelect.addEventListener('change', loadViewDefinition);

document.querySelectorAll('.tab-button').forEach(btn => {
  btn.addEventListener('click', () => {
    const tabId = btn.getAttribute('data-tab');

    document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');

    btn.classList.add('active');
    document.getElementById(tabId).style.display = 'block';
  });
});


// Initial load
loadDatabases();
