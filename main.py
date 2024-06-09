import requests
import cv2
import numpy as np
import os
import insightface
from insightface.app import FaceAnalysis
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TOKEN")
chat_id = os.getenv("CHAT_ID")


database_embeddings = {}



def create_face_database(database_directory):
    app = FaceAnalysis()
    app.prepare(ctx_id=0)  # ctx_id=-1 для использования CPU. Измените на 0 для GPU, если доступно
    for filename in os.listdir(database_directory):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            path = os.path.join(database_directory, filename)
            img = cv2.imread(path)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = app.get(rgb_img)
            if faces:
                database_embeddings[filename] = faces[0].normed_embedding
    print(f"Created face database with {len(database_embeddings)} entries.")

def send_photo_to_telegram(chat_id, photo_path, caption=None, token=token):
    """Функция для отправки фото в Telegram"""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {'chat_id': chat_id}
    if caption:
        data['caption'] = caption
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        response = requests.post(url, data=data, files=files)
    return response.json()

def verify_face(face_embedding, threshold=1.0):
    closest_name = None
    min_distance = threshold
    for name, db_embedding in database_embeddings.items():
        distance = np.linalg.norm(face_embedding - db_embedding)
        if distance < min_distance:
            min_distance = distance
            closest_name = name
    return closest_name, min_distance

# Функция "notify_unknown_person" для уведомления о неизвестном лице
def notify_unknown_person(frame, bbox):
    """Уведомление о неизвестном лице с отправкой фото в Telegram"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Измените путь сохранения файла на подходящий для вашей системы
    photo_path = f"C:\\Users\\Erzhan\\Desktop\\MyProject\\Final project\\unknown_face\\unknown_{timestamp}.jpg"
    # Сохраняем кадр с неизвестным лицом
    cv2.imwrite(photo_path, frame)

    # Отправляем фото в Telegram
    send_photo_to_telegram(chat_id, photo_path, caption="Обнаружено неизвестное лицо!")

def real_time_face_verification(database_directory, webcam_index=1):
    create_face_database(database_directory)
    app = FaceAnalysis()
    app.prepare(ctx_id=-1)  # Используйте CPU
    cap = cv2.VideoCapture(webcam_index)  # Используйте веб-камеру под индексом 1
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Не удалось получить кадр. Прерывание.")
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = app.get(rgb_frame)
        for face in faces:
            name, distance = verify_face(face.normed_embedding)
            bbox = face.bbox.astype(int)
            if name is None:
                # Вызов функции уведомления для неизвестных лиц
                notify_unknown_person(frame, bbox)
                cv2.putText(frame, "unknown_person", (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 2)
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2)
            else:
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(frame, f"{name} {distance:.2f}", (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
        cv2.imshow('Face Verification', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

# Пример вызова функции
real_time_face_verification('faces', webcam_index=1)