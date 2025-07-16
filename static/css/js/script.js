// /home/pi/autocarz/static/js/script.js

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 슬라이더 값 표시 업데이트
    updateSliderValues();
    
    // 슬라이더 이벤트 리스너 추가
    document.getElementById('quality').addEventListener('input', updateSliderValues);
    document.getElementById('fps_limit').addEventListener('input', updateSliderValues);
});

// 슬라이더 값 표시 업데이트
function updateSliderValues() {
    const qualitySlider = document.getElementById('quality');
    const fpsSlider = document.getElementById('fps_limit');
    const qualityValue = document.getElementById('quality_value');
    const fpsValue = document.getElementById('fps_value');
    
    if (qualitySlider && qualityValue) {
        qualityValue.textContent = qualitySlider.value;
    }
    
    if (fpsSlider && fpsValue) {
        fpsValue.textContent = fpsSlider.value;
    }
}

// 검출 설정 적용
function applyDetectionSettings() {
    const detection_settings = {
        yolo_enabled: document.getElementById('yolo_enabled').checked,
        opencv_enabled: document.getElementById('opencv_enabled').checked,
        show_fps: document.getElementById('show_fps').checked,
        quality: parseInt(document.getElementById('quality').value),
        fps_limit: parseInt(document.getElementById('fps_limit').value)
    };
    
    showLoading('검출 설정 적용 중...');
    
    fetch('/update_detection_settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(detection_settings)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showMessage(data.message, data.success ? 'success' : 'error');
        
        if (data.success) {
            // 설정 적용 후 비디오 스트림 새로고침
            refreshVideoStream();
        }
    })
    .catch(error => {
        hideLoading();
        showMessage('설정 적용 중 오류가 발생했습니다: ' + error.message, 'error');
    });
}

// 카메라 설정 적용
function applySettings() {
    const settings = {
        horizontal: document.getElementById('horizontal').checked,
        vertical: document.getElementById('vertical').checked,
        rotation: parseInt(document.getElementById('rotation').value)
    };
    
    showLoading('카메라 설정 적용 중...');
    
    fetch('/update_settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showMessage(data.message, data.success ? 'success' : 'error');
    })
    .catch(error => {
        hideLoading();
        showMessage('카메라 설정 적용 중 오류가 발생했습니다: ' + error.message, 'error');
    });
}

// 전체 설정 초기화
function resetSettings() {
    if (confirm('모든 설정을 초기화하시겠습니까?')) {
        // UI 초기화
        document.getElementById('horizontal').checked = false;
        document.getElementById('vertical').checked = false;
        document.getElementById('rotation').value = '0';
        document.getElementById('yolo_enabled').checked = true;
        document.getElementById('opencv_enabled').checked = true;
        document.getElementById('show_fps').checked = true;
        document.getElementById('quality').value = 85;
        document.getElementById('fps_limit').value = 15;
        
        // 슬라이더 값 표시 업데이트
        updateSliderValues();
        
        // 설정 적용
        applySettings();
        applyDetectionSettings();
    }
}

// 빠른 반전 설정
function setFlip(type) {
    switch(type) {
        case 'normal':
            document.getElementById('horizontal').checked = false;
            document.getElementById('vertical').checked = false;
            document.getElementById('rotation').value = '0';
            break;
        case 'horizontal':
            document.getElementById('horizontal').checked = true;
            document.getElementById('vertical').checked = false;
            document.getElementById('rotation').value = '0';
            break;
        case 'vertical':
            document.getElementById('horizontal').checked = false;
            document.getElementById('vertical').checked = true;
            document.getElementById('rotation').value = '0';
            break;
        case 'both':
            document.getElementById('horizontal').checked = true;
            document.getElementById('vertical').checked = true;
            document.getElementById('rotation').value = '0';
            break;
        case 'rotate180':
            document.getElementById('horizontal').checked = false;
            document.getElementById('vertical').checked = false;
            document.getElementById('rotation').value = '180';
            break;
    }
    applySettings();
}

// 메시지 표시
function showMessage(msg, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = msg;
    messageDiv.className = 'status ' + type;
    messageDiv.style.display = 'block';
    
    // 자동으로 메시지 숨기기
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 4000);
}

// 로딩 표시
function showLoading(message = '처리 중...') {
    const messageDiv = document.getElementById('message');
    messageDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="spinner"></div>
            <span>${message}</span>
        </div>
    `;
    messageDiv.className = 'status info';
    messageDiv.style.display = 'block';
    
    // 스피너 CSS 동적 추가
    if (!document.getElementById('spinner-style')) {
        const style = document.createElement('style');
        style.id = 'spinner-style';
        style.textContent = `
            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

// 로딩 숨기기
function hideLoading() {
    const messageDiv = document.getElementById('message');
    messageDiv.style.display = 'none';
}

// 비디오 스트림 새로고침
function refreshVideoStream() {
    const videoImg = document.querySelector('.video-stream');
    if (videoImg) {
        const currentSrc = videoImg.src;
        videoImg.src = '';
        setTimeout(() => {
            videoImg.src = currentSrc + '?t=' + new Date().getTime();
        }, 100);
    }
}

// 시스템 상태 확인
function checkSystemStatus() {
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        console.log('시스템 상태:', data);
        updateStatusDisplay(data);
    })
    .catch(error => {
        console.error('상태 확인 오류:', error);
    });
}

// 상태 표시 업데이트
function updateStatusDisplay(statusData) {
    // FPS 정보가 있으면 표시
    if (statusData.current_fps !== undefined) {
        const statusInfo = document.querySelector('.status.info');
        if (statusInfo) {
            const fpsInfo = statusInfo.querySelector('.fps-info');
            if (fpsInfo) {
                fpsInfo.textContent = `현재 FPS: ${statusData.current_fps}`;
            } else {
                const fpsElement = document.createElement('p');
                fpsElement.className = 'fps-info';
                fpsElement.innerHTML = `<strong>현재 FPS:</strong> ${statusData.current_fps}`;
                statusInfo.appendChild(fpsElement);
            }
        }
    }
}

// 키보드 단축키 지원
document.addEventListener('keydown', function(event) {
    // Ctrl + R: 설정 초기화
    if (event.ctrlKey && event.key === 'r') {
        event.preventDefault();
        resetSettings();
    }
    
    // Ctrl + S: 현재 설정 적용
    if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        applySettings();
        applyDetectionSettings();
    }
    
    // 스페이스바: YOLO 토글
    if (event.code === 'Space' && event.target.tagName !== 'INPUT') {
        event.preventDefault();
        const yoloCheckbox = document.getElementById('yolo_enabled');
        yoloCheckbox.checked = !yoloCheckbox.checked;
        applyDetectionSettings();
    }
    
    // C 키: OpenCV 토글
    if (event.key === 'c' && event.target.tagName !== 'INPUT') {
        const opencvCheckbox = document.getElementById('opencv_enabled');
        opencvCheckbox.checked = !opencvCheckbox.checked;
        applyDetectionSettings();
    }
});

// 자동 상태 확인 (5초마다)
setInterval(checkSystemStatus, 5000);

// 비디오 스트림 에러 처리
document.addEventListener('DOMContentLoaded', function() {
    const videoImg = document.querySelector('.video-stream');
    if (videoImg) {
        videoImg.addEventListener('error', function() {
            console.log('비디오 스트림 로드 오류, 재시도 중...');
            setTimeout(() => {
                refreshVideoStream();
            }, 2000);
        });
        
        videoImg.addEventListener('load', function() {
            console.log('비디오 스트림 로드 완료');
        });
    }
});

// 품질 및 FPS 실시간 적용
let settingsTimeout;
function applySettingsWithDelay() {
    clearTimeout(settingsTimeout);
    settingsTimeout = setTimeout(() => {
        applyDetectionSettings();
    }, 1000); // 1초 후 적용
}

// 슬라이더 실시간 업데이트
document.addEventListener('DOMContentLoaded', function() {
    const qualitySlider = document.getElementById('quality');
    const fpsSlider = document.getElementById('fps_limit');
    
    if (qualitySlider) {
        qualitySlider.addEventListener('input', function() {
            updateSliderValues();
            applySettingsWithDelay();
        });
    }
    
    if (fpsSlider) {
        fpsSlider.addEventListener('input', function() {
            updateSliderValues();
            applySettingsWithDelay();
        });
    }
});

// 화면 크기 변경 감지
window.addEventListener('resize', function() {
    // 모바일 화면에서 비디오 크기 조정
    const videoContainer = document.querySelector('.video-container');
    if (videoContainer && window.innerWidth < 768) {
        videoContainer.style.padding = '10px';
    } else if (videoContainer) {
        videoContainer.style.padding = '20px';
    }
});

// 터치 디바이스 지원
if ('ontouchstart' in window) {
    document.body.classList.add('touch-device');
    
    // 터치 이벤트로 비디오 새로고침
    const videoImg = document.querySelector('.video-stream');
    if (videoImg) {
        let touchStartTime;
        
        videoImg.addEventListener('touchstart', function() {
            touchStartTime = Date.now();
        });
        
        videoImg.addEventListener('touchend', function() {
            const touchDuration = Date.now() - touchStartTime;
            // 긴 터치(1초 이상)로 비디오 새로고침
            if (touchDuration > 1000) {
                refreshVideoStream();
                showMessage('비디오 스트림을 새로고침했습니다.', 'info');
            }
        });
    }
}

// 성능 모니터링
let performanceData = {
    frameCount: 0,
    startTime: Date.now()
};

function logPerformance() {
    performanceData.frameCount++;
    const elapsed = Date.now() - performanceData.startTime;
    
    if (elapsed > 10000) { // 10초마다 로그
        const avgFPS = (performanceData.frameCount / elapsed * 1000).toFixed(1);
        console.log(`평균 FPS: ${avgFPS}`);
        
        // 리셋
        performanceData.frameCount = 0;
        performanceData.startTime = Date.now();
    }
}

// 비디오 프레임 변경 감지 (실험적)
document.addEventListener('DOMContentLoaded', function() {
    const videoImg = document.querySelector('.video-stream');
    if (videoImg) {
        videoImg.addEventListener('load', logPerformance);
    }
});

// 오류 보고
window.addEventListener('error', function(event) {
    console.error('JavaScript 오류:', event.error);
    showMessage('예상치 못한 오류가 발생했습니다. 페이지를 새로고침해보세요.', 'error');
});

// 네트워크 상태 확인
window.addEventListener('online', function() {
    showMessage('네트워크 연결이 복구되었습니다.', 'success');
    refreshVideoStream();
});

window.addEventListener('offline', function() {
    showMessage('네트워크 연결이 끊어졌습니다.', 'error');
});