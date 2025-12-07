// API Base URL
const API_URL = 'http://localhost:8000/api';

// Auth Token
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// ==================== UTILITY FUNCTIONS ====================

function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add('active');
        setTimeout(() => errorEl.classList.remove('active'), 5000);
    }
}

function showSuccess(message) {
    alert(message);
}

// ==================== MODAL FUNCTIONS ====================

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function showLogin() {
    showModal('loginModal');
}

function showRegister() {
    showModal('registerModal');
}

// Close modal on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// ==================== NAVIGATION ====================

const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('navMenu');

if (hamburger) {
    hamburger.addEventListener('click', () => {
        navMenu.classList.toggle('active');
    });
}

// ==================== TABS ====================

function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Update buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

// ==================== AUTH FUNCTIONS ====================

async function handleRegister(event) {
    event.preventDefault();

    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value; // Получаем подтверждение
    const phone = document.getElementById('registerPhone').value;
    const role = document.getElementById('registerRole').value;

    if (password !== passwordConfirm) {
        showError('registerError', 'Пароли не совпадают. Пожалуйста, проверьте.');
        return; // Останавливаем отправку запроса
    }

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password,
                phone,
                role
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Регистрация успешна! Теперь войдите в систему.');
            closeModal('registerModal');
            showLogin();
        } else {
            showError('registerError', data.detail || 'Ошибка регистрации');
        }
    } catch (error) {
        showError('registerError', 'Ошибка соединения с сервером');
        console.error('Register error:', error);
    }
}

async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);

            await loadCurrentUser();

            closeModal('loginModal');

            // Redirect based on role
            if (currentUser.role === 'artist') {
                window.location.href = '/static/dashboard-artist.html.html';
            } else if (currentUser.role === 'organizer') {
                window.location.href = '/static/dashboard-organizer.html';
            } else {
                window.location.href = '/static/dashboard.html';
            }
        } else {
            showError('loginError', data.detail || 'Неверный email или пароль');
        }
    } catch (error) {
        showError('loginError', 'Ошибка соединения с сервером');
        console.error('Login error:', error);
    }
}

async function loadCurrentUser() {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_URL}/users/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            currentUser = await response.json();
            updateNavigation();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Load user error:', error);
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    window.location.href = '../index.html';
}

function updateNavigation() {
    const navMenu = document.getElementById('navMenu');
    if (!navMenu || !currentUser) return;

    // Update navigation for logged in user
    navMenu.innerHTML = `
        <li><a href="/static/index.html">Главная</a></li>
        <li><a href="/static/artists.html">Артисты</a></li>
        ${currentUser.role === 'artist' ? 
            '<li><a href="/static/dashboard-artist.html.html">Мой профиль</a></li>' : 
            '<li><a href="/static/dashboard-organizer.html">Панель управления</a></li>'
        }
        <li><a href="/static/messages.html">Сообщения</a></li>
        <li><a href="#" onclick="logout()" class="btn-primary">Выйти</a></li>
    `;
}

// ==================== API HELPERS ====================

async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(authToken && { 'Authorization': `Bearer ${authToken}` })
        }
    };

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });

    if (!response.ok && response.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }

    return response;
}

// ==================== SEARCH ARTISTS ====================

async function searchArtists(filters = {}) {
    const params = new URLSearchParams();

    if (filters.genre) params.append('genre', filters.genre);
    if (filters.price_min) params.append('price_min', filters.price_min);
    if (filters.price_max) params.append('price_max', filters.price_max);
    if (filters.search) params.append('search', filters.search);

    try {
        const response = await fetch(`${API_URL}/artists?${params}`);
        const artists = await response.json();
        return artists;
    } catch (error) {
        console.error('Search error:', error);
        return [];
    }
}

// ==================== LOAD ON PAGE LOAD ====================

document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        loadCurrentUser();
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
});