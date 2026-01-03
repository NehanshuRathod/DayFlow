document.addEventListener('DOMContentLoaded', async () => {
    // Auth Check
    const userData = JSON.parse(localStorage.getItem('user_data'));
    if (!userData || !Api.token) {
        window.location.href = 'index.html';
        return;
    }

    // UI Elements
    const userNameEl = document.getElementById('user-name');
    const clockEl = document.getElementById('clock');
    const checkInBtn = document.getElementById('check-in-btn');
    const checkOutBtn = document.getElementById('check-out-btn');
    const statusMsg = document.getElementById('status-msg');
    const employeeList = document.getElementById('employee-list');
    const attendanceList = document.getElementById('attendance-list');
    const leaveList = document.getElementById('leave-list');
    const addEmployeeBtn = document.getElementById('add-employee-btn');

    // Init
    userNameEl.textContent = `${userData.role === 'admin' ? 'Admin: ' : ''}${userData.first_name || userData.email}`;
    if (userData.role === 'admin' || userData.role === 'hr') {
        addEmployeeBtn.classList.remove('hidden');
    }

    // Clock
    setInterval(() => {
        clockEl.textContent = new Date().toLocaleTimeString();
    }, 1000);

    // Initial Data Load
    loadCheckInStatus();
    loadEmployees();
    loadAttendance();
    loadLeaves();

    // Event Listeners
    document.getElementById('logout-btn').onclick = () => {
        Api.clearToken();
        window.location.href = 'index.html';
    };

    checkInBtn.onclick = async () => {
        try {
            await Api.checkIn();
            loadCheckInStatus();
            loadAttendance();
            alert('Checked in!');
        } catch (e) { alert(e.message); }
    };

    checkOutBtn.onclick = async () => {
        try {
            await Api.checkOut();
            loadCheckInStatus();
            loadAttendance();
            alert('Checked out!');
        } catch (e) { alert(e.message); }
    };

    // Tab Switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            // Update buttons
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('border-b-2', 'border-blue-500', 'font-bold');
                b.classList.add('text-gray-600');
            });
            btn.classList.add('border-b-2', 'border-blue-500', 'font-bold');
            btn.classList.remove('text-gray-600');

            // Show content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
            document.getElementById(`tab-${btn.dataset.tab}`).classList.remove('hidden');
        };
    });

    // Modal Logic
    const leaveModal = document.getElementById('leave-modal');
    document.getElementById('apply-leave-btn').onclick = () => leaveModal.classList.remove('hidden');
    document.getElementById('close-leave-modal').onclick = () => leaveModal.classList.add('hidden');

    document.getElementById('leave-form').onsubmit = async (e) => {
        e.preventDefault();
        try {
            await Api.request('/leaves', {
                method: 'POST',
                body: JSON.stringify({
                    leave_type: document.getElementById('leave-type').value,
                    start_date: document.getElementById('start-date').value,
                    end_date: document.getElementById('end-date').value,
                    description: document.getElementById('leave-desc').value
                })
            });
            leaveModal.classList.add('hidden');
            loadLeaves();
            alert('Leave requested!');
        } catch (error) {
            alert(error.message);
        }
    };


    // Functions
    async function loadCheckInStatus() {
        try {
            const data = await Api.request(`/employees/${userData.user_id}/status`);
            if (data.status === 'present' && !data.check_out) {
                checkInBtn.classList.add('hidden');
                checkOutBtn.classList.remove('hidden');
                statusMsg.textContent = `Checked in at ${new Date(data.check_in).toLocaleTimeString()}`;
            } else if (data.status === 'present' && data.check_out) {
                checkInBtn.classList.add('hidden');
                checkOutBtn.classList.add('hidden');
                statusMsg.textContent = 'Checked out for today';
            } else {
                checkInBtn.classList.remove('hidden');
                checkOutBtn.classList.add('hidden');
                statusMsg.textContent = 'Not checked in yet';
            }
        } catch (e) { console.error(e); }
    }

    async function loadEmployees() {
        try {
            const employees = await Api.getEmployees();
            employeeList.innerHTML = employees.map(emp => `
                <div class="border p-4 rounded flex justify-between items-center ${emp.today_status === 'present' ? 'border-l-4 border-l-green-500' : ''}">
                    <div>
                        <h3 class="font-bold">${emp.first_name} ${emp.last_name}</h3>
                        <p class="text-sm text-gray-600">${emp.job_title || 'Employee'}</p>
                    </div>
                    <span class="px-2 py-1 text-xs rounded ${getStatusColor(emp.today_status)}">
                        ${emp.today_status || 'Unknown'}
                    </span>
                </div>
            `).join('');
        } catch (e) {
            // If not admin, show just self
            employeeList.innerHTML = '<p class="text-gray-500">Employee list only visible to Admin/HR</p>';
        }
    }

    async function loadAttendance() {
        try {
            const data = await Api.request('/attendance');
            attendanceList.innerHTML = data.map(r => `
                <tr class="border-b">
                    <td class="p-2">${r.attendance_date}</td>
                    <td class="p-2">${r.check_in ? new Date(r.check_in).toLocaleTimeString() : '-'}</td>
                    <td class="p-2">${r.check_out ? new Date(r.check_out).toLocaleTimeString() : '-'}</td>
                    <td class="p-2">${r.work_hours || '-'} hrs</td>
                </tr>
            `).join('');
        } catch (e) { console.error(e); }
    }

    async function loadLeaves() {
        try {
            const data = await Api.request('/leaves');
            leaveList.innerHTML = data.map(l => `
                <div class="border p-3 rounded flex justify-between">
                    <div>
                        <span class="font-bold ${l.leave_type === 'sick' ? 'text-red-500' : ''}">${l.leave_type.toUpperCase()}</span>
                        <p class="text-sm">${l.start_date} to ${l.end_date} (${l.days_requested} days)</p>
                        <p class="text-xs text-gray-500">${l.description}</p>
                    </div>
                    <div>
                        <span class="px-2 py-1 rounded text-xs ${l.status === 'approved' ? 'bg-green-100 text-green-800' : l.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}">
                            ${l.status.toUpperCase()}
                        </span>
                    </div>
                </div>
            `).join('');
        } catch (e) { console.error(e); }
    }

    function getStatusColor(status) {
        if (status === 'present') return 'bg-green-100 text-green-800';
        if (status === 'absent') return 'bg-red-100 text-red-800';
        if (status === 'leave') return 'bg-yellow-100 text-yellow-800';
        return 'bg-gray-100';
    }
});
