// ==================== ARTISTS PAGE ====================

let currentView = 'grid';
let allArtists = [];

// Load artists on page load
document.addEventListener('DOMContentLoaded', () => {
    loadArtists();
});

// ==================== SEARCH & FILTER ====================

function performSearch() {
    const searchQuery = document.getElementById('searchQuery').value;
    const genre = document.getElementById('genreFilter').value;

    // ИСПРАВЛЕНИЕ: Явное преобразование в число и валидация
    const priceMinVal = parseFloat(document.getElementById('priceMin').value);
    const priceMaxVal = parseFloat(document.getElementById('priceMax').value);

    const filters = {};
    if (searchQuery) filters.search = searchQuery;
    if (genre) filters.genre = genre;

    if (!isNaN(priceMinVal) && priceMinVal >= 0) filters.price_min = priceMinVal;
    if (!isNaN(priceMaxVal) && priceMaxVal >= 0) filters.price_max = priceMaxVal;

    loadArtists(filters);
}

async function loadArtists(filters = {}) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const artistsGrid = document.getElementById('artistsGrid');
    const noResults = document.getElementById('noResults');

    // Show loading
    loadingSpinner.style.display = 'block';
    artistsGrid.innerHTML = '';
    noResults.style.display = 'none';

    try {
        const params = new URLSearchParams();
        if (filters.search) params.append('search', filters.search);
        if (filters.genre) params.append('genre', filters.genre);
        if (filters.price_min) params.append('price_min', filters.price_min);
        if (filters.price_max) params.append('price_max', filters.price_max);

        const response = await fetch(`${API_URL}/artists?${params}`);
        allArtists = await response.json();

        loadingSpinner.style.display = 'none';

        if (allArtists.length === 0) {
            noResults.style.display = 'block';
        } else {
            displayArtists(allArtists);
        }
    } catch (error) {
        console.error('Load artists error:', error);
        loadingSpinner.style.display = 'none';
        artistsGrid.innerHTML = '<p style="text-align: center; color: var(--danger-color);">Ошибка загрузки артистов</p>';
    }
}

function displayArtists(artists) {
    const artistsGrid = document.getElementById('artistsGrid');
    artistsGrid.innerHTML = '';

    artists.forEach(artist => {
        const card = createArtistCard(artist);
        artistsGrid.appendChild(card);
    });
}

function createArtistCard(artist) {
    const card = document.createElement('div');
    card.className = 'artist-card';
    card.onclick = () => showArtistDetails(artist.artist_id);

    const genres = artist.genres || [];
    const genreTags = genres.slice(0, 3).map(g =>
        `<span class="genre-tag">${g.trim()}</span>`
    ).join('');

    // Format price
    const priceText = artist.price_min && artist.price_max
        ? `${artist.price_min.toLocaleString()} - ${artist.price_max.toLocaleString()} ₽`
        : 'Цена не указана';

    card.innerHTML = `
        <div class="artist-card-image">
            <i class="fas fa-user-music"></i>
        </div>
        <div class="artist-card-content">
            <h3 class="artist-name">${artist.stage_name}</h3>
            <div class="artist-genres">
                ${genreTags}
            </div>
            <p class="artist-bio">${artist.bio || 'Описание отсутствует'}</p>
            <div class="artist-stats">
                <div class="stat-item artist-rating">
                    <i class="fas fa-star"></i>
                    <span>${artist.rating ? artist.rating.toFixed(1) : '0.0'}</span>
                </div>
                <div class="stat-item artist-price">
                    ${priceText}
                </div>
            </div>
        </div>
    `;

    return card;
}

// ==================== VIEW TOGGLE ====================

function toggleView(view) {
    currentView = view;
    const artistsGrid = document.getElementById('artistsGrid');
    const buttons = document.querySelectorAll('.view-btn');

    // Update grid class
    if (view === 'list') {
        artistsGrid.classList.add('list-view');
    } else {
        artistsGrid.classList.remove('list-view');
    }

    // Update button states
    buttons.forEach(btn => {
        if (btn.dataset.view === view) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// ==================== ARTIST DETAILS ====================

async function showArtistDetails(artistId) {
    try {
        const response = await fetch(`${API_URL}/artists/${artistId}`);
        const artist = await response.json();

        // Load reviews
        const reviewsResponse = await fetch(`${API_URL}/reviews/artist/${artistId}`);
        const reviews = await reviewsResponse.json();

        displayArtistDetails(artist, reviews);
        showModal('artistModal');
    } catch (error) {
        console.error('Load artist details error:', error);
        alert('Ошибка загрузки профиля артиста');
    }
}

function displayArtistDetails(artist, reviews) {
    const artistDetails = document.getElementById('artistDetails');

    // ИСПРАВЛЕНИЕ: genres теперь приходит как массив (List[str])
    const genres = artist.genres || [];
    const genreTags = genres.map(g => `<span class="genre-tag">${g.trim()}</span>` ).join('');

    const priceText = artist.price_min && artist.price_max ? `${artist.price_min.toLocaleString()} - ${artist.price_max.toLocaleString()} ₽` : 'Не указано';

    const reviewsHtml = reviews.length > 0
        ? reviews.map(review => `
            <div class="review-card">
                <div class="review-header">
                    <span class="review-author">Пользователь #${review.reviewer_id}</span>
                    <div class="review-rating">
                        ${getStarRating(review.rating_score)}
                    </div>
                </div>
                <p>${review.comment || 'Без комментария'}</p>
                <small style="color: var(--gray);">${new Date(review.created_at).toLocaleDateString()}</small>
            </div>
        `).join('')
        : '<p style="color: var(--gray);">Отзывов пока нет</p>';

    artistDetails.innerHTML = `
        <div class="artist-detail-header">
            <div class="artist-detail-image">
                <i class="fas fa-user-music"></i>
            </div>
            <div class="artist-detail-info">
                <h2>${artist.stage_name}</h2>
                <div class="artist-genres">
                    ${genreTags}
                </div>
                <div class="artist-detail-stats">
                    <div class="detail-stat">
                        <div class="detail-stat-label">Рейтинг</div>
                        <div class="detail-stat-value">
                            <i class="fas fa-star" style="color: var(--warning-color);"></i>
                            ${artist.rating ? artist.rating.toFixed(1) : '0.0'}
                        </div>
                    </div>
                    <div class="detail-stat">
                        <div class="detail-stat-label">Цена выступления</div>
                        <div class="detail-stat-value">${priceText}</div>
                    </div>
                </div>
                ${authToken && currentUser && currentUser.role === 'organizer' 
                    ? `<div class="artist-detail-actions">
                        <button class="btn btn-primary" onclick="createBooking(${artist.artist_id})">
                            <i class="fas fa-calendar-plus"></i> Забронировать
                        </button>
                        <button class="btn btn-outline" onclick="sendMessage(${artist.user_id})">
                            <i class="fas fa-envelope"></i> Написать
                        </button>
                    </div>`
                    : '<p style="color: var(--gray);"><i class="fas fa-info-circle"></i> Войдите как организатор для бронирования</p>'
                }
            </div>
        </div>
        
        <div class="artist-detail-bio">
            <h3>О артисте</h3>
            <p>${artist.bio || 'Описание отсутствует'}</p>
        </div>
        
        <div class="reviews-section">
            <h3>Отзывы (${reviews.length})</h3>
            ${reviewsHtml}
        </div>
    `;
}

function getStarRating(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= rating) {
            stars += '<i class="fas fa-star"></i>';
        } else if (i - 0.5 <= rating) {
            stars += '<i class="fas fa-star-half-alt"></i>';
        } else {
            stars += '<i class="far fa-star"></i>';
        }
    }
    return stars;
}

// ==================== BOOKING ====================

function createBooking(artistId) {
    if (!authToken) {
        closeModal('artistModal');
        showLogin();
        return;
    }

    if (currentUser.role !== 'organizer') {
        alert('Только организаторы могут создавать бронирования');
        return;
    }

    // Store artistId and redirect to booking page
    localStorage.setItem('selectedArtistId', artistId);
    window.location.href = '/static/create-booking.html';
}

function sendMessage(userId) {
    if (!authToken) {
        closeModal('artistModal');
        showLogin();
        return;
    }

    localStorage.setItem('messageRecipientId', userId);
    window.location.href = '/static/messages.html';
}

// ==================== SEARCH ON ENTER ====================

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchQuery');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
});