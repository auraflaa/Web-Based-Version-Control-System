// js/dashboard.js
import { login, register, showError } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    if (localStorage.getItem('userId') && localStorage.getItem('userName')) {
        window.location.href = 'repos.html';
        return;
    }

    // Login form handler
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.onsubmit = async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const loginButton = loginForm.querySelector('button');
            const loginError = document.getElementById('loginError');

            if (!email || !password) {
                showError({ message: 'Please enter both email and password' }, 'loginError');
                return;
            }

            try {
                loginButton.disabled = true;
                const result = await login(email, password);
                
                if (result.success) {
                    localStorage.setItem('userId', result.user_id);
                    localStorage.setItem('userName', result.name);
                    window.location.href = 'repos.html';
                } else {
                    showError({ message: result.error || 'Login failed' }, 'loginError');
                }
            } catch (error) {
                showError(error, 'loginError');
            } finally {
                loginButton.disabled = false;
            }
        };
    }

    // Registration form handler
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.onsubmit = async (e) => {
            e.preventDefault();
            const name = document.getElementById('regName').value.trim();
            const email = document.getElementById('regEmail').value.trim();
            const password = document.getElementById('regPassword').value;
            const registerButton = registerForm.querySelector('button');
            const registerError = document.getElementById('registerError');

            if (!name || !email || !password) {
                showError({ message: 'All fields are required' }, 'registerError');
                return;
            }

            try {
                registerButton.disabled = true;
                const result = await register(name, email, password);
                
                if (result.success) {
                    localStorage.setItem('userId', result.user_id);
                    localStorage.setItem('userName', result.name);
                    window.location.href = 'repos.html';
                } else {
                    showError({ message: result.error || 'Registration failed' }, 'registerError');
                }
            } catch (error) {
                showError(error, 'registerError');
            } finally {
                registerButton.disabled = false;
            }
        };
    }
});

// Form switching functions (made global for onclick handlers)
window.showLoginForm = () => {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
};

window.showRegisterForm = () => {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
};