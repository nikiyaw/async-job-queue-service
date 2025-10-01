// --- Utility Functions ---

function getStatusBadge(status) {
    let color;
    switch (status) {
        case 'queued':
            color = 'bg-gray-100 text-gray-800';
            break;
        case 'processing':
            color = 'bg-blue-100 text-blue-800 animate-pulse';
            break;
        case 'completed':
            color = 'bg-green-100 text-green-800';
            break;
        case 'failed':
            color = 'bg-red-100 text-red-800';
            break;
        case 'retrying':
            color = 'bg-yellow-100 text-yellow-800';
            break;
        default:
            color = 'bg-purple-100 text-purple-800';
    }
    return `<span class="px-3 py-1 text-xs font-semibold rounded-full ${color} capitalize">${status}</span>`;
}

function renderJobs(jobs) {
    const tbody = document.getElementById('jobListBody');
    tbody.innerHTML = '';
    if (jobs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">No jobs found. Submit one above!</td>
            </tr>
        `;
        return;
    }
    jobs.sort((a, b) => b.id - a.id);
    jobs.forEach(job => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-indigo-50 transition duration-100';
        const createdDate = new Date(job.created_at).toLocaleString();
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${job.id}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${job.job_type}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">${getStatusBadge(job.status)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${createdDate}</td>
        `;
        tbody.appendChild(row);
    });
}

// --- Fetch and Polling Logic ---
let isFetching = false;

async function fetchJobs() {
    if (isFetching) return;
    isFetching = true;

    try {
        const response = await fetch('/jobs/');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        let jobsArray = null;

        if (data && Array.isArray(data.jobs)) jobsArray = data.jobs;
        else if (Array.isArray(data)) jobsArray = data;

        if (jobsArray !== null) renderJobs(jobsArray);
        else {
            console.error("API response structure error:", data);
            const tbody = document.getElementById('jobListBody');
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-sm text-red-500">API response error: Data structure invalid. (Check console)</td>
                </tr>
            `;
        }
    } catch (error) {
        console.error("Failed to fetch jobs:", error);
        const tbody = document.getElementById('jobListBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-4 text-center text-sm text-red-500">Error fetching jobs: ${error.toString()}</td>
            </tr>
        `;
    } finally {
        isFetching = false;
    }
}

setInterval(fetchJobs, 2000);
fetchJobs();

// --- Job Submission Handler ---
const messageElement = document.getElementById('message');
const messageContent = document.getElementById('messageContent');
const dismissButton = document.getElementById('dismissMessage');

const hideMessage = () => messageElement.classList.add('hidden');
dismissButton.addEventListener('click', hideMessage);

document.getElementById('submitJobForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const jobType = document.getElementById('jobType').value;
    const payloadText = document.getElementById('payload').value;

    try {
        const payload = JSON.parse(payloadText);
        const response = await fetch('/jobs/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_type: jobType, payload: payload }),
        });
        const result = await response.json();

        if (response.status === 201) {
            messageContent.textContent = `Success! Job ${result.job_id} (${jobType}) queued. Click (X) to dismiss.`;
            messageElement.className = 'mt-4 p-3 rounded-lg text-sm bg-green-100 text-green-800';
            document.getElementById('payload').value = '{"input_data": 100}';
            fetchJobs();
            setTimeout(hideMessage, 5000);
        } else {
            messageContent.textContent = `Error: ${result.detail || 'Could not submit job.'}`;
            messageElement.className = 'mt-4 p-3 rounded-lg text-sm bg-red-100 text-red-800';
        }
    } catch (error) {
        console.error('Submission failed:', error);
        messageContent.textContent = 'Submission Failed: Invalid JSON payload or network error.';
        messageElement.className = 'mt-4 p-3 rounded-lg text-sm bg-red-100 text-red-800';
    } finally {
        messageElement.classList.remove('hidden');
    }
});