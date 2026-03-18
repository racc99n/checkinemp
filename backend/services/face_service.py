import numpy as np
from PIL import Image
import base64
import io
import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_app = None


def _get_app():
    global _app
    if _app is None:
        import insightface
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name="buffalo_sc", providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=0, det_size=(320, 320))
        logger.info("InsightFace model loaded (buffalo_sc)")
    return _app


class FaceService:
    def __init__(self, face_data_dir: str, tolerance: float = 0.5):
        self.face_data_dir = face_data_dir
        self.tolerance = tolerance  # cosine similarity threshold (higher = stricter)
        self._cache: dict[int, np.ndarray] = {}
        os.makedirs(face_data_dir, exist_ok=True)

    def reload_cache(self, db):
        from ..models.employee import Employee
        employees = db.query(Employee).filter(
            Employee.is_active == True,
            Employee.face_encoding_path != None
        ).all()
        self._cache = {}
        for emp in employees:
            if emp.face_encoding_path and os.path.exists(emp.face_encoding_path):
                self._cache[emp.id] = np.load(emp.face_encoding_path)
        logger.info(f"Face cache reloaded: {len(self._cache)} employees")

    def _decode_image(self, image_b64: str) -> np.ndarray:
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # InsightFace expects BGR
        import cv2
        arr = np.array(image)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    def _get_embedding(self, image_bgr: np.ndarray) -> Optional[np.ndarray]:
        app = _get_app()
        faces = app.get(image_bgr)
        if not faces:
            return None
        # Pick the largest face
        face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
        return face.normed_embedding  # 512-dim normalized vector

    def enroll(self, employee_id: int, images_b64: list[str]) -> str:
        embeddings = []
        for img_b64 in images_b64:
            try:
                image = self._decode_image(img_b64)
                emb = self._get_embedding(image)
                if emb is None:
                    logger.warning("No face detected in enrollment image, skipping")
                    continue
                embeddings.append(emb)
            except Exception as e:
                logger.warning(f"Skipping image during enroll: {e}")

        if not embeddings:
            raise ValueError("ไม่สามารถตรวจจับใบหน้าได้จากรูปภาพที่ส่งมา")

        avg_embedding = np.mean(embeddings, axis=0)
        # Re-normalize
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)

        save_path = os.path.join(self.face_data_dir, f"{employee_id}.npy")
        np.save(save_path, avg_embedding)
        self._cache[employee_id] = avg_embedding
        logger.info(f"Enrolled face for employee {employee_id} using {len(embeddings)} images")
        return save_path

    def remove(self, employee_id: int):
        path = os.path.join(self.face_data_dir, f"{employee_id}.npy")
        if os.path.exists(path):
            os.remove(path)
        self._cache.pop(employee_id, None)

    def identify(self, image_b64: str) -> Tuple[Optional[int], float]:
        if not self._cache:
            return None, 0.0

        try:
            image = self._decode_image(image_b64)
            unknown_emb = self._get_embedding(image)
            if unknown_emb is None:
                return None, 0.0

            best_id = None
            best_sim = -1.0

            for emp_id, known_emb in self._cache.items():
                # Cosine similarity (both normalized, so dot product)
                sim = float(np.dot(unknown_emb, known_emb))
                if sim > best_sim:
                    best_sim = sim
                    best_id = emp_id

            # Threshold: similarity > 0.35 means same person (insightface buffalo_sc)
            threshold = 1.0 - self.tolerance  # default tolerance=0.5 → threshold=0.5
            if best_sim >= threshold:
                confidence = round(best_sim * 100, 2)
                return best_id, confidence

            return None, 0.0

        except Exception as e:
            logger.error(f"Face identification error: {e}")
            return None, 0.0


_face_service: Optional[FaceService] = None


def get_face_service() -> FaceService:
    global _face_service
    if _face_service is None:
        from ..config import settings
        _face_service = FaceService(settings.FACE_DATA_DIR, settings.FACE_TOLERANCE)
    return _face_service
