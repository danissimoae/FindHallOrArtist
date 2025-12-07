// ==================== ARTIST DASHBOARD ====================

let artistProfile = null;
let allBookings = [];
let allReviews = [];

// Check authentication
if (!authToken) {
    window.location.href = '../index.html';
}

// Load data on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadCurrentUser();

    if (!currentUser || currentUser.role !== 'artist') {
        alert('Доступ запрещен');
        logout();
        return;
    }

    document.getElementById('userName').textContent = currentUser.email.split('@')[0];
    document.getElementById('userEmail').textContent = currentUser.email;

    await loadArtistProfile();
    await loadBookings();
    await loadReviews();
    loadStats();
});

// ==================== NAVIGATION ====================

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    const sectionMap = {
        'profile': 'profileSection',
        'bookings': 'bookingsSection',
        'reviews': 'reviewsSection',
        'stats': 'statsSection'
    };

    const sectionId = sectionMap[sectionName];
    if (sectionId) {
        document.getElementById(sectionId).style.display = 'block';
    }

    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.classList.add('active');
}

// ==================== PROFILE ====================

async function loadArtistProfile() {
    try {
        // ИСПРАВЛЕНИЕ: Используем новый, эффективный эндпоинт /artists/me
        const response = await apiRequest('/artists/me', {
            method: 'GET'
        });

        // Обработка случая, когда профиль артиста не существует (статус 404)
        if (response.status === 404) {
            artistProfile = null;
            document.getElementById('profileView').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-user-plus"></i>
                    <h3>Профиль не создан</h3>
                    <p>Создайте свой профиль артиста</p>
                    <button class="btn btn-primary" onclick="toggleEditMode(true)">
                        Создать профиль
                    </button>
                </div>
            `;
            toggleEditMode(true); // Показываем форму создания
            return;
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        artistProfile = await response.json();
        displayProfile(artistProfile);
        toggleEditMode(false); // Показываем режим просмотра

    } catch (error) {
        console.error('Load profile error:', error);
    }
}

function displayProfile(artist) {
    const genres = artist.genres || [];
    const genresText = genres.join(', ') || 'Не указано';

    const priceText = artist.price_min && artist.price_max
        ? `${artist.price_min.toLocaleString()} - ${artist.price_max.toLocaleString()} ₽`
        : 'Не указано';

    document.getElementById('stageName').textContent = artist.stage_name;
    document.getElementById('rating').textContent = artist.rating ? artist.rating.toFixed(1) : '0.0';
    document.getElementById('genresView').textContent = genresText;
    document.getElementById('priceView').textContent = priceText;
    document.getElementById('bioView').textContent = artist.bio || 'Не указано';
}

function toggleEditMode(forceEdit = false) {
    const profileView = document.getElementById('profileView');
    const profileEdit = document.getElementById('profileEdit');

    if (forceEdit || profileView.style.display !== 'none') {
        profileView.style.display = 'none';
        profileEdit.style.display = 'block';

        // Заполнение формы
        if (artistProfile) {
            document.getElementById('stageNameEdit').value = artistProfile.stage_name || '';
            document.getElementById('priceMinEdit').value = artistProfile.price_min || '';
            document.getElementById('priceMaxEdit').value = artistProfile.price_max || '';

            // Приводим массив жанров к строке для поля ввода
            document.getElementById('genresEdit').value = artistProfile.genres.join(', ') || '';

            document.getElementById('bioEdit').value = artistProfile.bio || '';
        } else {
            // Очистка формы, если профиль создается впервые
            document.getElementById('stageNameEdit').value = '';
            document.getElementById('priceMinEdit').value = '';
            document.getElementById('priceMaxEdit').value = '';
            document.getElementById('genresEdit').value = '';
            document.getElementById('bioEdit').value = '';
        }
    } else {
        // Переключение с редактирования на вид
        profileView.style.display = 'block';
        profileEdit.style.display = 'none';
    }
}

async function saveProfile(event) {
    event.preventDefault();

    const stageName = document.getElementById('stageNameEdit').value;
    const priceMin = parseFloat(document.getElementById('priceMinEdit').value) || null;
    const priceMax = parseFloat(document.getElementById('priceMaxEdit').value) || null;
    const genresStr = document.getElementById('genresEdit').value;
    const bio = document.getElementById('bioEdit').value;

    const genres = genresStr.split(',').map(g => g.trim()).filter(g => g);

    const profileData = {
        stage_name: stageName,
        price_min: priceMin,
        price_max: priceMax,
        genres: genres,
        bio: bio
    };

    try {
        let response;

        if (artistProfile) {
            // Update existing profile
            response = await apiRequest(`/artists/${artistProfile.artist_id}`, {
                method: 'PUT',
                body: JSON.stringify(profileData)
            });
        } else {
            // Create new profile
            response = await apiRequest('/artists', {
                method: 'POST',
                body: JSON.stringify(profileData)
            });
        }

        if (response.ok) {
            artistProfile = await response.json();
            displayProfile(artistProfile);
            toggleEditMode();
            alert('Профиль успешно сохранен!');
        } else {
            const error = await response.json();
            alert('Ошибка: ' + (error.detail || 'Не удалось сохранить профиль'));
        }
    } catch (error) {
        console.error('Save profile error:', error);
        alert('Ошибка сохранения профиля');
    }
}

// ==================== BOOKINGS ====================

async function loadBookings() {
    try {
        const response = await apiRequest('/bookings');
        allBookings = await response.json();
        displayBookings(allBookings);
    } catch (error) {
        console.error('Load bookings error:', error);
        document.getElementById('bookingsList').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Ошибка загрузки</h3>
            </div>
        `;
    }
}

function displayBookings(bookings) {
    const bookingsList = document.getElementById('bookingsList');

    if (bookings.length === 0) {
        bookingsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-calendar"></i>
                <h3>Нет заявок</h3>
                <p>У вас пока нет заявок на выступления</p>
            </div>
        `;
        return;
    }

    bookingsList.innerHTML = bookings.map(booking => {
        const statusText = {
            'pending': 'Ожидает',
            'confirmed': 'Подтверждено',
            'declined': 'Отклонено',
            'cancelled': 'Отменено'
        }[booking.status] || booking.status;

        return `
            <div class="booking-card ${booking.status}">
                <div class="booking-header">
                    <div class="booking-info">
                        <h3>Заявка #${booking.booking_id}</h3>
                        <div class="booking-date">
                            <i class="fas fa-clock"></i>
                            ${new Date(booking.created_at).toLocaleString('ru')}
                        </div>
                    </div>
                    <span class="booking-status ${booking.status}">${statusText}</span>
                </div>
                
                <div class="booking-details">
                    <div class="detail-row">
                        <i class="fas fa-building"></i>
                        <span>Организатор #${booking.organizer_id}</span>
                    </div>
                    ${booking.proposed_price ? `
                        <div class="detail-row">
                            <i class="fas fa-ruble-sign"></i>
                            <span>${booking.proposed_price.toLocaleString()} ₽</span>
                        </div>
                    ` : ''}
                    ${booking.technical_requirements ? `
                        <div class="detail-row">
                            <i class="fas fa-list"></i>
                            <span>${booking.technical_requirements}</span>
                        </div>
                    ` : ''}
                </div>
                
                ${booking.status === 'pending' ? `
                    <div class="booking-actions">
                        <button class="btn btn-success" onclick="updateBookingStatus(${booking.booking_id}, 'confirmed')">
                            <i class="fas fa-check"></i> Подтвердить
                        </button>
                        <button class="btn btn-danger" onclick="updateBookingStatus(${booking.booking_id}, 'declined')">
                            <i class="fas fa-times"></i> Отклонить
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function filterBookings(status) {
    // Update filter buttons
    document.querySelectorAll('.filter-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Filter bookings
    const filtered = status === 'all'
        ? allBookings
        : allBookings.filter(b => b.status === status);

    displayBookings(filtered);
}

async function updateBookingStatus(bookingId, newStatus) {
    try {
        const response = await apiRequest(`/bookings/${bookingId}`, {
            method: 'PATCH',
            body: JSON.stringify({ status: newStatus })
        });

        if (response.ok) {
            await loadBookings();
            alert('Статус заявки обновлен');
        } else {
            const error = await response.json();
            alert('Ошибка: ' + (error.detail || 'Не удалось обновить статус'));
        }
    } catch (error) {
        console.error('Update booking error:', error);
        alert('Ошибка обновления статуса');
    }
}

// ==================== REVIEWS ====================

async function loadReviews() {
    if (!artistProfile) return;

    try {
        const response = await fetch(`${API_URL}/reviews/artist/${artistProfile.artist_id}`);
        allReviews = await response.json();
        displayReviews(allReviews);
    } catch (error) {
        console.error('Load reviews error:', error);
        document.getElementById('reviewsList').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Ошибка загрузки</h3>
            </div>
        `;
    }
}

function displayReviews(reviews) {
    const reviewsList = document.getElementById('reviewsList');

    if (reviews.length === 0) {
        reviewsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-star"></i>
                <h3>Нет отзывов</h3>
                <p>У вас пока нет отзывов</p>
            </div>
        `;
        return;
    }

    reviewsList.innerHTML = reviews.map(review => `
        <div class="review-card">
            <div class="review-header">
                <span class="review-author">Пользователь #${review.reviewer_id}</span>
                <div class="review-rating">${getStarRating(review.rating_score)}</div>
            </div>
            <p class="review-comment">${review.comment || 'Без комментария'}</p>
            <div class="review-date">
                <i class="fas fa-calendar"></i>
                ${new Date(review.created_at).toLocaleDateString('ru')}
            </div>
        </div>
    `).join('');
}

function getStarRating(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        stars += i <= rating ? '<i class="fas fa-star"></i>' : '<i class="far fa-star"></i>';
    }
    return stars;
}

// ==================== STATISTICS ====================

function loadStats() {
    const total = allBookings.length;
    const confirmed = allBookings.filter(b => b.status === 'confirmed').length;
    const avgRating = artistProfile ? artistProfile.rating : 0;
    const totalReviews = allReviews.length;

    document.getElementById('totalBookings').textContent = total;
    document.getElementById('confirmedBookings').textContent = confirmed;
    document.getElementById('avgRating').textContent = avgRating.toFixed(1);
    document.getElementById('totalReviews').textContent = totalReviews;
}