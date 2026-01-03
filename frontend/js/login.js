document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const errorMsg = document.getElementById('error-msg');

    // Check if already logged in
    if (Api.token) {
        window.location.href = 'dashboard.html';
    }

    // Login Handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const identifier = document.getElementById('identifier').value;
        const password = document.getElementById('password').value;

        try {
            const response = await Api.login(identifier, password);
            Api.token = response.access_token;
            localStorage.setItem('user_data', JSON.stringify(response.user));
            window.location.href = 'dashboard.html';
        } catch (error) {
            showError(error.message);
        }
    });

    // Signup Modal Logic
    const modal = document.getElementById('signup-modal');
    document.getElementById('toggle-signup').onclick = () => modal.classList.remove('hidden');
    document.getElementById('close-signup').onclick = () => modal.classList.add('hidden');

    // Signup Handler
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            company_name: document.getElementById('company_name').value,
            company_prefix: document.getElementById('company_prefix').value,
            admin_name: document.getElementById('admin_name').value,
            admin_email: document.getElementById('admin_email').value,
            admin_password: document.getElementById('admin_password').value
        };

        try {
            const response = await Api.signup(data);
            Api.token = response.access_token;
            localStorage.setItem('user_data', JSON.stringify(response.user));
            window.location.href = 'dashboard.html';
        } catch (error) {
            alert(error.message); // Simple alert for modal error
        }
    });

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.classList.remove('hidden');
    }
});
