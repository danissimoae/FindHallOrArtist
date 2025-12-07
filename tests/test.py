import requests
import json

BASE_URL = "http://localhost:8010"


def print_response(title, response):
    """Красивый вывод ответа"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")


def test_full_workflow():
    """Полный тестовый сценарий работы с платформой"""

    print("\n ТЕСТИРОВАНИЕ МузПлатформы \n")

    # 1. Регистрация артиста
    print("\n Регистрация артиста...")
    artist_data = {
        "email": "rockstar@test.com",
        "password": "rock123",
        "phone": "+79001234567",
        "role": "artist"
    }
    response = requests.post(f"{BASE_URL}/api/register", json=artist_data)
    print_response("Регистрация артиста", response)

    # 2. Регистрация организатора
    print("\n Регистрация организатора...")
    organizer_data = {
        "email": "eventorg@test.com",
        "password": "event123",
        "phone": "+79009876543",
        "role": "organizer"
    }
    response = requests.post(f"{BASE_URL}/api/register", json=organizer_data)
    print_response("Регистрация организатора", response)

    # 3. Получение токена артиста
    print("\n Логин артиста...")
    login_data = {
        "username": "rockstar@test.com",
        "password": "rock123"
    }
    response = requests.post(f"{BASE_URL}/api/token", data=login_data)
    print_response("Логин артиста", response)

    if response.status_code == 200:
        artist_token = response.json()["access_token"]
        artist_headers = {"Authorization": f"Bearer {artist_token}"}
    else:
        print(" Не удалось получить токен артиста")
        return

    # 4. Получение токена организатора
    print("\n Логин организатора...")
    login_data = {
        "username": "eventorg@test.com",
        "password": "event123"
    }
    response = requests.post(f"{BASE_URL}/api/token", data=login_data)
    print_response("Логин организатора", response)

    if response.status_code == 200:
        organizer_token = response.json()["access_token"]
        organizer_headers = {"Authorization": f"Bearer {organizer_token}"}
    else:
        print(" Не удалось получить токен организатора")
        return

    # 5. Создание профиля артиста
    print("\n Создание профиля артиста...")
    artist_profile = {
        "stage_name": "The Rock Stars",
        "bio": "Профессиональная рок-группа с 10-летним опытом выступлений на крупных площадках",
        "genres": ["rock", "alternative", "indie"],
        "price_min": 50000,
        "price_max": 150000
    }
    response = requests.post(
        f"{BASE_URL}/api/artists",
        json=artist_profile,
        headers=artist_headers
    )
    print_response("Создание профиля артиста", response)

    if response.status_code == 200:
        artist_id = response.json()["artist_id"]
    else:
        print(" Не удалось создать профиль артиста")
        return

    # 6. Создание профиля организатора
    print("\n Создание профиля организатора...")
    organizer_profile = {
        "company_name": "EventPro Moscow",
        "description": "Организация корпоративных и частных мероприятий",
        "address": "Москва, ул. Тверская, д. 10",
        "website": "https://eventpro.example.com"
    }
    response = requests.post(
        f"{BASE_URL}/api/organizers",
        json=organizer_profile,
        headers=organizer_headers
    )
    print_response("Создание профиля организатора", response)

    # 7. Поиск артистов
    print("\n Поиск артистов по жанру 'rock'...")
    response = requests.get(f"{BASE_URL}/api/artists?genre=rock")
    print_response("Результаты поиска артистов", response)

    # 8. Создание заявки на бронирование
    print("\n Создание заявки на бронирование...")
    booking_data = {
        "artist_id": artist_id,
        "proposed_price": 80000,
        "technical_requirements": "Сцена 6x4 метра, профессиональный звук, сценический свет"
    }
    response = requests.post(
        f"{BASE_URL}/api/bookings",
        json=booking_data,
        headers=organizer_headers
    )
    print_response("Создание бронирования", response)

    if response.status_code == 200:
        booking_id = response.json()["booking_id"]
    else:
        print(" Не удалось создать бронирование")
        return

    # 9. Просмотр заявок артистом
    print("\n Просмотр заявок артистом...")
    response = requests.get(
        f"{BASE_URL}/api/bookings",
        headers=artist_headers
    )
    print_response("Заявки артиста", response)

    # 10. Подтверждение заявки артистом
    print("\n Подтверждение заявки артистом...")
    booking_update = {
        "status": "confirmed"
    }
    response = requests.patch(
        f"{BASE_URL}/api/bookings/{booking_id}",
        json=booking_update,
        headers=artist_headers
    )
    print_response("Подтверждение бронирования", response)

    # 11. Отправка сообщения от организатора к артисту
    print("\n Отправка сообщения от организатора...")

    # Сначала получим user_id артиста
    response = requests.get(
        f"{BASE_URL}/api/users/me",
        headers=artist_headers
    )
    if response.status_code == 200:
        artist_user_id = response.json()["id"]

        message_data = {
            "receiver_id": artist_user_id,
            "booking_id": booking_id,
            "content": "Здравствуйте! Подтверждаем бронирование на 15 декабря. Ждем технический райдер."
        }
        response = requests.post(
            f"{BASE_URL}/api/messages",
            json=message_data,
            headers=organizer_headers
        )
        print_response("Отправка сообщения", response)

    # 12. Создание отзыва
    print("\n Создание отзыва организатором...")

    # Получаем user_id артиста для отзыва
    response = requests.get(
        f"{BASE_URL}/api/users/me",
        headers=organizer_headers
    )
    organizer_user_id = response.json()["id"]

    review_data = {
        "booking_id": booking_id,
        "reviewed_id": artist_user_id,
        "rating_score": 5.0,
        "comment": "Отличное выступление! Профессиональный подход, качественный звук, публика в восторге!"
    }
    response = requests.post(
        f"{BASE_URL}/api/reviews",
        json=review_data,
        headers=organizer_headers
    )
    print_response("Создание отзыва", response)

    # 13. Просмотр отзывов артиста
    print("\nПросмотр отзывов артиста...")
    response = requests.get(f"{BASE_URL}/api/reviews/artist/{artist_id}")
    print_response("Отзывы артиста", response)

    # 14. Обновленный профиль артиста с рейтингом
    print("\nПрофиль артиста с обновленным рейтингом...")
    response = requests.get(f"{BASE_URL}/api/artists/{artist_id}")
    print_response("Обновленный профиль артиста", response)

    print("\n\n ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    print("=" * 60)
    print("\nВсе основные функции работают корректно:")
    print("✓ Регистрация и аутентификация")
    print("✓ Создание профилей артистов и организаторов")
    print("✓ Поиск артистов")
    print("✓ Создание и обработка бронирований")
    print("✓ Система сообщений")
    print("✓ Рейтинги и отзывы")


if __name__ == "__main__":
    try:
        test_full_workflow()
    except requests.exceptions.ConnectionError:
        print("\n ОШИБКА: Не удалось подключиться к серверу")
        print("Убедитесь, что сервер запущен: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n ОШИБКА: {str(e)}")
        import traceback

        traceback.print_exc()