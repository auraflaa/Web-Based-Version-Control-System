// js/dashboard.js
import { login, register, showError } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const userId = localStorage.getItem('userId');
    if (userId && userId !== 'undefined' && !isNaN(Number(userId)) && Number(userId) > 0) {
        window.location.href = 'repos.html';
        return;
    }
    
    setupForms();
});

function setupForms() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
            const result = await login(email, password);
            if (result.success) {
                window.location.href = 'repos.html';
            }
        } catch (error) {
            const errorElement = document.getElementById('loginError');
            errorElement.textContent = error.message;
            errorElement.style.display = 'block';
        }
    });
    
    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        const name = document.getElementById('regName').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        
        try {
            const result = await register(name, email, password);
            if (result.success) {
                window.location.href = 'repos.html';
            }
        } catch (error) {
            const errorElement = document.getElementById('registerError');
            errorElement.textContent = error.message;
            errorElement.style.display = 'block';
        }
    });
}

// Make form toggle functions global for onclick handlers
window.showRegisterForm = () => {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('loginError').style.display = 'none';
    document.getElementById('registerError').style.display = 'none';
};

window.showLoginForm = () => {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('loginError').style.display = 'none';
    document.getElementById('registerError').style.display = 'none';
};