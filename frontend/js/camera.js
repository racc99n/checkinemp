/**
 * Camera Service - จัดการ camera stream และ capture รูปภาพ
 * รองรับ mobile browser (Android/iOS) และ fallback constraints
 */

class CameraService {
  constructor(videoElement, canvasElement) {
    this.video = videoElement;
    this.canvas = canvasElement;
    this.stream = null;
    this.isActive = false;
  }

  async start() {
    // ลองหลาย constraint เพื่อให้ทำงานได้บนทุก browser/อุปกรณ์
    const constraintsList = [
      // 1. กล้องหน้า HD
      { video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } } },
      // 2. กล้องหน้าอย่างเดียว
      { video: { facingMode: "user" } },
      // 3. กล้องใดก็ได้ (fallback)
      { video: true },
    ];

    let lastErr = null;
    for (const constraints of constraintsList) {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia(constraints);
        this.video.srcObject = this.stream;
        this.isActive = true;

        // รอให้ video พร้อม (บาง browser event อาจไม่ยิง)
        await new Promise((resolve, reject) => {
          const cleanup = () => {
            this.video.onloadedmetadata = null;
            this.video.oncanplay = null;
            this.video.onerror = null;
          };

          const timeoutId = setTimeout(() => {
            cleanup();
            const hasTrack = !!(this.stream && this.stream.getVideoTracks().some(t => t.readyState === "live"));
            if (hasTrack) {
              resolve();
            } else {
              reject(new Error("Camera metadata timeout"));
            }
          }, 8000);

          this.video.onloadedmetadata = () => {
            clearTimeout(timeoutId);
            cleanup();
            resolve();
          };

          this.video.oncanplay = () => {
            clearTimeout(timeoutId);
            cleanup();
            resolve();
          };

          this.video.onerror = () => {
            clearTimeout(timeoutId);
            cleanup();
            reject(new Error("Video stream error"));
          };
        });

        try {
          await this.video.play();
        } catch {
          // บางมือถือ play() ต้อง user gesture; มี stream อยู่แล้วให้ผ่าน
        }

        const hasTrack = !!(this.stream && this.stream.getVideoTracks().some(t => t.readyState === "live"));
        if (!hasTrack) {
          throw new Error("No live camera track");
        }

        return true;
      } catch (err) {
        const errName = err?.name || "UnknownError";
        lastErr = { name: errName, message: err?.message || "Unknown media error" };

        if (this.stream) {
          this.stream.getTracks().forEach(t => t.stop());
          this.stream = null;
        }

        // ถ้า user ปฏิเสธ permission ให้หยุดเลย ไม่ต้อง retry
        if (errName === "NotAllowedError" || errName === "PermissionDeniedError") {
          throw new Error("กรุณาอนุญาตการเข้าถึงกล้องในเบราว์เซอร์ แล้ว refresh หน้าใหม่");
        }
        console.warn("Camera constraint failed, trying next:", errName, lastErr.message);
      }
    }

    // ลองทุก constraint แล้วล้มเหลว
    if (lastErr) {
      if (lastErr.name === "NotFoundError" || lastErr.name === "DevicesNotFoundError") {
        throw new Error("ไม่พบกล้องในอุปกรณ์นี้");
      }
      if (lastErr.name === "NotReadableError" || lastErr.name === "TrackStartError") {
        throw new Error("กล้องกำลังถูกใช้งานโดยแอปอื่น กรุณาปิดแอปอื่นแล้วลองใหม่");
      }
      if (lastErr.name === "AbortError") {
        throw new Error("เปิดกล้องไม่สำเร็จ กรุณากดปุ่มเปิดกล้องอีกครั้ง");
      }
      throw new Error("ไม่สามารถเปิดกล้องได้ กรุณาตรวจสอบสิทธิ์การเข้าถึงกล้อง");
    }
  }

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    this.isActive = false;
  }

  captureFrame(quality = 0.85) {
    if (!this.isActive) throw new Error("กล้องยังไม่เปิด");
    const ctx = this.canvas.getContext("2d");
    this.canvas.width = this.video.videoWidth || 640;
    this.canvas.height = this.video.videoHeight || 480;
    // mirror เหมือน preview
    ctx.save();
    ctx.translate(this.canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(this.video, 0, 0);
    ctx.restore();
    return this.canvas.toDataURL("image/jpeg", quality);
  }
}

window.CameraService = CameraService;
