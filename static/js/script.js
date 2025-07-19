// /home/pi/autocarz/static/js/script.js
// 새로운 레이아웃에 맞춰 전체적으로 수정 및 기능 추가된 버전

// ===========================================
// 페이지 로드 시 초기화
// ===========================================
document.addEventListener("DOMContentLoaded", function () {
  console.log("AutocarZ 새 레이아웃 초기화 시작");

  // [추가] CSS 캐시 강제 새로고침
  forceRefreshCSS();

  // [수정] 모든 슬라이더 값 표시를 한 번에 업데이트
  updateAllSliderValues();

  // [추가] 모든 슬라이더에 이벤트 리스너를 동적으로 추가
  const sliders = document.querySelectorAll(".range-slider");
  sliders.forEach((slider) => {
    slider.addEventListener("input", function () {
      updateAllSliderValues();
    });
  });

  // [추가] 색상 보정 슬라이더에 대한 지연 적용 리스너 추가
  const colorSliders = ["red_reduction", "green_boost", "blue_boost"];
  colorSliders.forEach((id) => {
    const slider = document.getElementById(id);
    if (slider) {
      slider.addEventListener("input", applyColorSettingsWithDelay);
    }
  });

  // 비디오 스트림 에러 처리 설정
  setupVideoErrorHandling();

  // [추가] 현재 카메라 상태 업데이트
  updateCurrentCameraStatus();

  // 자동 상태 업데이트 시작
  startStatusUpdates();

  console.log("AutocarZ 새 레이아웃 초기화 완료");
});

// ===========================================
// CSS 캐시 강제 새로고침
// ===========================================
function forceRefreshCSS() {
  const links = document.querySelectorAll('link[rel="stylesheet"]');
  links.forEach((link) => {
    const href = link.getAttribute("href");
    if (href) {
      const newHref = href.split("?")[0] + "?v=" + new Date().getTime();
      link.setAttribute("href", newHref);
    }
  });

  // 추가로 스타일 강제 적용
  const style = document.createElement("style");
  style.textContent = `
    .center-video-area { gap: 0px !important; }
    .video-info-section { 
      padding: 3px 10px !important; 
      margin: 0 !important; 
      border-radius: 8px !important;
    }
    .main-video-area { 
      padding: 2px !important; 
      margin: 0 !important; 
      min-height: 500px !important;
    }
    .video-title { font-size: 0.9em !important; margin: 0 !important; }
    .detection-legend { font-size: 0.75em !important; margin: 0 !important; }
    .legend-item { padding: 2px 6px !important; margin: 0 !important; }
    .color-indicator { width: 6px !important; height: 6px !important; }
  `;
  document.head.appendChild(style);
}

// ===========================================
// 설정 패널 토글 기능
// ===========================================
function toggleSettings() {
  const settingsContent = document.getElementById("settingsContent");
  const toggleIcon = document.getElementById("settingsToggleIcon");

  // [수정] null 체크 추가로 안정성 향상
  if (!settingsContent || !toggleIcon) return;

  if (settingsContent.style.display === "none") {
    settingsContent.style.display = "block";
    toggleIcon.textContent = "▼";
  } else {
    settingsContent.style.display = "none";
    toggleIcon.textContent = "▲";
  }
}

// ===========================================
// 슬라이더 값 표시 업데이트 (통합 버전)
// ===========================================
// [수정] 모든 슬라이더 값을 한 번에 업데이트하는 통합 함수
function updateAllSliderValues() {
  const sliders = [
    "quality",
    "fps_limit",
    "red_reduction",
    "green_boost",
    "blue_boost",
  ];
  sliders.forEach((id) => {
    const slider = document.getElementById(id);
    const valueSpan = document.getElementById(`${id}_value`);
    // [수정] 요소가 존재하는지 반드시 확인하여 오류 방지
    if (slider && valueSpan) {
      valueSpan.textContent = slider.value;
    }
  });
}

// ===========================================
// 카메라 상태 관리
// ===========================================
function updateCurrentCameraStatus() {
  fetch("/get_current_camera")
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // 현재 카메라 이름 업데이트
        const currentCameraSpan = document.getElementById("currentCamera");
        if (currentCameraSpan) {
          currentCameraSpan.textContent = data.camera_name;
        }

        // 카메라 버튼 활성화 상태 업데이트
        updateCameraButtonStates(data.camera_index);
      }
    })
    .catch((error) => {
      console.error("카메라 상태 가져오기 오류:", error);
    });
}

function updateCameraButtonStates(activeIndex) {
  // 모든 카메라 버튼에서 active 클래스 제거
  const cameraButtons = document.querySelectorAll(".btn-camera");
  cameraButtons.forEach((button) => {
    button.classList.remove("active");
  });

  // 현재 활성화된 카메라 버튼에 active 클래스 추가
  const activeButton = document.getElementById(`camera-${activeIndex}`);
  if (activeButton) {
    activeButton.classList.add("active");
  }
}

// ===========================================
// 모든 설정 적용 함수들
// ===========================================

// 검출 설정 적용
function applyDetectionSettings() {
  const settings = {
    yolo_enabled: document.getElementById("yolo_enabled").checked,
    opencv_enabled: document.getElementById("opencv_enabled").checked,
    show_fps: document.getElementById("show_fps").checked,
    quality: parseInt(document.getElementById("quality").value),
    fps_limit: parseInt(document.getElementById("fps_limit").value),
  };
  postSettings("/update_detection_settings", settings, "검출 설정 적용");
}

// 카메라(뒤집기/회전) 설정 적용
function applySettings() {
  const settings = {
    horizontal: document.getElementById("horizontal").checked,
    vertical: document.getElementById("vertical").checked,
    rotation: parseInt(document.getElementById("rotation").value),
  };
  postSettings("/update_flip_settings", settings, "카메라 설정 적용");
}

// [추가] 색상 보정 설정 적용
function applyColorSettings() {
  const settings = {
    enabled: document.getElementById("color_correction_enabled").checked,
    red_reduction: parseFloat(document.getElementById("red_reduction").value),
    green_boost: parseFloat(document.getElementById("green_boost").value),
    blue_boost: parseFloat(document.getElementById("blue_boost").value),
    mode: document.getElementById("color_mode").value,
  };
  postSettings("/update_color_settings", settings, "색상 보정 적용");
}

// [추가] 설정을 서버로 전송하는 공통 함수
function postSettings(endpoint, settings, actionName) {
  console.log(`${actionName} 요청:`, settings);
  showLoading(`${actionName} 중...`);

  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading();
      if (data.success) {
        showMessage(data.message || `${actionName} 완료!`, "success");

        // [추가] 카메라 전환인 경우 UI 업데이트
        if (endpoint === "/switch_camera" && data.camera_name) {
          const currentCameraSpan = document.getElementById("currentCamera");
          if (currentCameraSpan) {
            currentCameraSpan.textContent = data.camera_name;
          }
          updateCameraButtonStates(data.camera_index);
        }

        refreshVideoStream();
      } else {
        showMessage(data.error || `${actionName} 실패.`, "error");
      }
    })
    .catch((error) => {
      hideLoading();
      console.error(`${actionName} 오류:`, error);
      showMessage(`${actionName} 중 오류 발생.`, "error");
    });
}

// ===========================================
// 설정 초기화 함수들
// ===========================================
function resetSettings() {
  if (confirm("카메라(뒤집기/회전) 설정을 초기화하시겠습니까?")) {
    postSettings("/reset_flip_settings", {}, "카메라 설정 초기화");
    // [추가] UI도 원래 값으로 복원
    document.getElementById("horizontal").checked = false;
    document.getElementById("vertical").checked = false;
    document.getElementById("rotation").value = 0;
  }
}

// [추가] 색상 설정 초기화
function resetColorSettings() {
  if (confirm("색상 보정 설정을 초기화하시겠습니까?")) {
    postSettings("/reset_color_settings", {}, "색상 설정 초기화");
    // [추가] UI도 원래 값으로 복원
    document.getElementById("color_correction_enabled").checked = false;
    document.getElementById("red_reduction").value = 0.9;
    document.getElementById("green_boost").value = 1.1;
    document.getElementById("blue_boost").value = 1.1;
    document.getElementById("color_mode").value = "standard";
    updateAllSliderValues();
  }
}

// ===========================================
// 카메라 전환 기능
// ===========================================
function switchCamera(cameraIndex) {
  console.log(`카메라 전환 시도: ${cameraIndex}`);
  postSettings("/switch_camera", { camera_index: cameraIndex }, "카메라 전환");
}

// ===========================================
// 비디오 스트림 및 상태 관리
// ===========================================
function refreshVideoStream() {
  const videoElement = document.getElementById("videoStream");
  if (videoElement) {
    const timestamp = new Date().getTime();
    videoElement.src = `/video_feed?t=${timestamp}`;
  }
}

function setupVideoErrorHandling() {
  const videoImg = document.getElementById("videoStream");
  if (!videoImg) return;

  videoImg.addEventListener("error", function () {
    console.warn("비디오 스트림 로드 오류, 3초 후 재시도");
    setTimeout(() => refreshVideoStream(), 3000);
  });
}

// ===========================================
// 상태 업데이트 및 모니터링
// ===========================================
function startStatusUpdates() {
  // 5초마다 시스템 상태 체크
  setInterval(checkSystemStatus, 5000);

  // 10초마다 카메라 상태 체크
  setInterval(updateCurrentCameraStatus, 10000);
}

function checkSystemStatus() {
  // 시스템 상태 체크 로직 (필요시 구현)
  console.log("시스템 상태 체크 중...");
}

// ===========================================
// 유틸리티 함수들
// ===========================================
function showMessage(msg, type = "info") {
  const overlay = document.createElement("div");
  overlay.className = `message-overlay ${type}`;
  overlay.textContent = msg;
  document.body.appendChild(overlay);

  setTimeout(() => overlay.classList.add("show"), 100);
  setTimeout(() => {
    overlay.classList.remove("show");
    setTimeout(() => document.body.removeChild(overlay), 300);
  }, 3000);
}

function showLoading(message = "처리 중...") {
  // 로딩 표시 로직 (필요시 구현)
  console.log("로딩:", message);
}

function hideLoading() {
  // 로딩 숨김 로직 (필요시 구현)
  console.log("로딩 완료");
}

// ===========================================
// 색상 보정 지연 적용
// ===========================================
function applyColorSettingsWithDelay() {
  clearTimeout(window.colorSettingsTimeout);
  window.colorSettingsTimeout = setTimeout(() => {
    applyColorSettings();
  }, 500);
}

// ===========================================
// 기타 유틸리티 함수들
// ===========================================
function checkStatus() {
  // 상태 체크 로직
}

function detectCameras() {
  // 카메라 감지 로직
}

function getDebugLog() {
  // 디버그 로그 가져오기
}

function clearLog() {
  // 로그 클리어
}

function showDebugInfo(title, content) {
  // 디버그 정보 표시
}
