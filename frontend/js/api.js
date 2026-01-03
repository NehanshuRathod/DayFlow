const API_BASE_URL = 'http://localhost:8000'; // Or just '' if served from same origin

class Api {
    static get token() {
        return localStorage.getItem('access_token');
    }

    static set token(value) {
        localStorage.setItem('access_token', value);
    }

    static clearToken() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
    }

    static get headers() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            ...options,
            headers: { ...this.headers, ...options.headers }
        };

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                this.clearToken();
                window.location.href = 'index.html';
                throw new Error('Unauthorized');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'API Request Failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth
    static login(identifier, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ identifier, password })
        });
    }

    static signup(data) {
        return this.request('/auth/signup', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static getMe() {
        return this.request('/auth/me');
    }

    // Employees
    static getEmployees() {
        return this.request('/employees');
    }

    // Attendance
    static checkIn() {
        return this.request('/attendance/check-in', { method: 'POST' });
    }

    static checkOut() {
        return this.request('/attendance/check-out', { method: 'POST' });
    }

    static getTodayAttendance() {
        return this.request('/attendance/today');
    }
}
