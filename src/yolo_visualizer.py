# /home/pi/autocarz/src/yolo_visualizer.py
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import cv2
from datetime import datetime

class YoloVisualizer:
    def __init__(self, font_path, font_size_large, font_size_small):
        """폰트 경로와 크기를 받아 초기화합니다."""
        try:
            self.font_large = ImageFont.truetype(font_path, font_size_large)
            self.font_small = ImageFont.truetype(font_path, font_size_small)
        except IOError:
            self.font_large = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
        print("✅ YOLO Visualizer: 폰트 설정 완료!")

    def draw_detections(self, frame, results, conf_threshold):
        """탐지 결과를 프레임 위에 그립니다."""
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        detected_info = "탐지된 객체 없음"
        is_real_detection = False

        if results:
            for r in results:
                for box in r.boxes:
                    confidence = float(box.conf[0])
                    if confidence > conf_threshold:
                        is_real_detection = True
                        class_name = r.names[int(box.cls[0])]
                        detected_info = f"{class_name.upper()} ({confidence:.0%})"
                        
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        label = f"{class_name} {confidence:.2f}"
                        
                        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=4)
                        draw.text((x1, y1 - 30), label, font=self.font_large, fill="red")

        # 정보 패널 그리기
        h, w, _ = frame.shape
        panel_y = h - 100
        draw.rectangle([(0, panel_y), (w, h)], fill=(0, 0, 0, 128))
        draw.text((20, panel_y + 15), f"[탐지 시간] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", font=self.font_small, fill="white")
        draw.text((w - 450, panel_y + 35), f"[객체 정보] {detected_info}", font=self.font_large, fill="yellow" if is_real_detection else "white")

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR), is_real_detection