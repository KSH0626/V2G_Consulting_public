// V2G 분석 시스템 JavaScript - 고급 분석 확장 버전 (완전판)

console.log('🚀 V2G 분석 시스템 JavaScript 로드 시작');

// 전역 변수
let scenarioCount = 0;
let lastBasicAnalysisData = null; // 종합 분석용

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 DOM 로드 완료 - 초기화 시작');
    initializeApp();
});

// 앱 초기화
function initializeApp() {
    console.log('🔧 앱 초기화 시작');
    try {
        setupEventListeners();
        setupSliders();
        addInitialScenario();
        updateSOHTotal(); // 초기 SOH 총합 계산
        console.log('✅ 앱 초기화 완료');
    } catch (error) {
        console.error('❌ 앱 초기화 오류:', error);
    }
}

// 이벤트 리스너 설정
function setupEventListeners() {
    console.log('🎯 이벤트 리스너 설정 시작');
    
    try {
        // 기초 분석 폼 제출
        const basicForm = document.getElementById('basicAnalysisForm');
        if (basicForm) {
            basicForm.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log('📊 기초 분석 폼 제출됨');
                runBasicAnalysis();
            });
            console.log('✅ 기초 분석 폼 이벤트 설정 완료');
        }

        // 부드러운 스크롤
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        console.log('✅ 이벤트 리스너 설정 완료');
    } catch (error) {
        console.error('❌ 이벤트 리스너 설정 오류:', error);
    }
}

// 슬라이더 설정
function setupSliders() {
    console.log('🎛️ 슬라이더 설정 시작');
    
    try {
        // 일정 패턴 비율 슬라이더
        const regularPatternSlider = document.getElementById('regularPatternRatio');
        if (regularPatternSlider) {
            regularPatternSlider.addEventListener('input', function() {
                const valueSpan = document.getElementById('regularPatternValue');
                if (valueSpan) {
                    valueSpan.textContent = this.value;
                }
            });
        }

        // DR 발령시간 비율 슬라이더
        const drDispatchSlider = document.getElementById('drDispatchTimeRatio');
        if (drDispatchSlider) {
            drDispatchSlider.addEventListener('input', function() {
                const valueSpan = document.getElementById('drDispatchValue');
                if (valueSpan) {
                    valueSpan.textContent = this.value;
                }
            });
        }

        // SOH 분포 슬라이더들
        const sohSliders = [
            { id: 'sohUnder70Ratio', valueId: 'sohUnder70Value' },
            { id: 'soh7085Ratio', valueId: 'soh7085Value' },
            { id: 'soh8595Ratio', valueId: 'soh8595Value' },
            { id: 'sohOver95Ratio', valueId: 'sohOver95Value' }
        ];

        sohSliders.forEach(slider => {
            const sliderElement = document.getElementById(slider.id);
            const valueElement = document.getElementById(slider.valueId);
            
            if (sliderElement && valueElement) {
                sliderElement.addEventListener('input', function() {
                    valueElement.textContent = this.value;
                    updateSOHTotal();
                });
            }
        });
        
        console.log('✅ 슬라이더 설정 완료');
    } catch (error) {
        console.error('❌ 슬라이더 설정 오류:', error);
    }
}

// 동적 슬라이더 설정 (시나리오용)
function setupScenarioSliders(scenarioId) {
    try {
        // 각 시나리오의 슬라이더 설정
        const sliderConfigs = [
            { sliderId: `regularPatternRatio_${scenarioId}`, valueId: `regularPatternValue_${scenarioId}` },
            { sliderId: `drDispatchTimeRatio_${scenarioId}`, valueId: `drDispatchValue_${scenarioId}` },
            { sliderId: `sohUnder70Ratio_${scenarioId}`, valueId: `sohUnder70Value_${scenarioId}` },
            { sliderId: `soh7085Ratio_${scenarioId}`, valueId: `soh7085Value_${scenarioId}` },
            { sliderId: `soh8595Ratio_${scenarioId}`, valueId: `soh8595Value_${scenarioId}` },
            { sliderId: `sohOver95Ratio_${scenarioId}`, valueId: `sohOver95Value_${scenarioId}` }
        ];

        sliderConfigs.forEach(config => {
            const sliderElement = document.getElementById(config.sliderId);
            const valueElement = document.getElementById(config.valueId);
            
            if (sliderElement && valueElement) {
                sliderElement.addEventListener('input', function() {
                    valueElement.textContent = this.value;
                    updateScenarioSOHTotal(scenarioId);
                });
            }
        });
        
        // 초기 SOH 총합 계산
        updateScenarioSOHTotal(scenarioId);
        
        console.log(`✅ 시나리오 ${scenarioId} 슬라이더 설정 완료`);
    } catch (error) {
        console.error(`❌ 시나리오 ${scenarioId} 슬라이더 설정 오류:`, error);
    }
}

// 시나리오별 SOH 총합 업데이트
function updateScenarioSOHTotal(scenarioId) {
    try {
        const sohUnder70Element = document.getElementById(`sohUnder70Ratio_${scenarioId}`);
        const soh7085Element = document.getElementById(`soh7085Ratio_${scenarioId}`);
        const soh8595Element = document.getElementById(`soh8595Ratio_${scenarioId}`);
        const sohOver95Element = document.getElementById(`sohOver95Ratio_${scenarioId}`);
        const totalElement = document.getElementById(`sohTotal_${scenarioId}`);
        const alertElement = document.getElementById(`sohTotalDisplay_${scenarioId}`);
        
        if (sohUnder70Element && soh7085Element && soh8595Element && sohOver95Element && totalElement) {
            const sohUnder70 = parseInt(sohUnder70Element.value);
            const soh7085 = parseInt(soh7085Element.value);
            const soh8595 = parseInt(soh8595Element.value);
            const sohOver95 = parseInt(sohOver95Element.value);
            
            const total = sohUnder70 + soh7085 + soh8595 + sohOver95;
            totalElement.textContent = total;
            
            // 색상 변경
            if (alertElement) {
                if (total === 100) {
                    alertElement.className = 'alert alert-success';
                } else {
                    alertElement.className = 'alert alert-warning';
                }
            }
        }
    } catch (error) {
        console.error(`❌ 시나리오 ${scenarioId} SOH 총합 업데이트 오류:`, error);
    }
}

// SOH 총합 업데이트 (기초 분석용)
function updateSOHTotal() {
    try {
        const sohUnder70Element = document.getElementById('sohUnder70Ratio');
        const soh7085Element = document.getElementById('soh7085Ratio');
        const soh8595Element = document.getElementById('soh8595Ratio');
        const sohOver95Element = document.getElementById('sohOver95Ratio');
        const totalElement = document.getElementById('sohTotal');
        
        if (sohUnder70Element && soh7085Element && soh8595Element && sohOver95Element && totalElement) {
            const sohUnder70 = parseInt(sohUnder70Element.value);
            const soh7085 = parseInt(soh7085Element.value);
            const soh8595 = parseInt(soh8595Element.value);
            const sohOver95 = parseInt(sohOver95Element.value);
            
            const total = sohUnder70 + soh7085 + soh8595 + sohOver95;
            totalElement.textContent = total;
            
            // 색상 변경
            const alertElement = document.getElementById('sohTotalDisplay');
            if (alertElement) {
                if (total === 100) {
                    alertElement.className = 'alert alert-success';
                } else {
                    alertElement.className = 'alert alert-warning';
                }
            }
        }
    } catch (error) {
        console.error('❌ SOH 총합 업데이트 오류:', error);
    }
}

// 알림 표시
function showAlert(message, type = 'info') {
    console.log(`📢 알림: [${type}] ${message}`);
    
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // 5초 후 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// 알림 컨테이너 생성
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.position = 'fixed';
    container.style.top = '100px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// 로딩 표시/숨김
function showLoading() {
    console.log('⏳ 로딩 표시');
    hideAllResults();
    
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = 'block';
    }
    
    // 결과 섹션으로 스크롤
    const resultsSection = document.getElementById('results');
    if (resultsSection) {
        resultsSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function hideLoading() {
    console.log('⏳ 로딩 숨김');
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = 'none';
    }
}

function hideAllResults() {
    const resultContainers = [
        'resultsContainer',
        'advancedResults',
        'comprehensiveResults'
    ];
    
    resultContainers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container) {
            container.style.display = 'none';
        }
    });
}

// 숫자 포맷팅
function formatNumber(num) {
    if (typeof num !== 'number') return num;
    return new Intl.NumberFormat('ko-KR').format(Math.round(num));
}

// 기초 분석 실행 (통합)
function runBasicAnalysis() {
    console.log('🔍 기초 분석 실행 시작 (수익성 + 점수화 통합)');
    
    try {
        showLoading();

        // 폼 데이터 수집
        const data = {
            capacity_kw: parseFloat(document.getElementById('capacity').value),
            location: document.getElementById('location').value,
            budget_billion: parseFloat(document.getElementById('budgetBillion').value),
            risk_preference: document.getElementById('riskPreference').value,
            regular_pattern_ratio: parseFloat(document.getElementById('regularPatternRatio').value) / 100,
            dr_dispatch_time_ratio: parseFloat(document.getElementById('drDispatchTimeRatio').value) / 100,
            charging_spots: parseInt(document.getElementById('chargingSpots').value),
            power_capacity_mva: parseFloat(document.getElementById('powerCapacityMva').value),
            total_ports: parseInt(document.getElementById('totalPorts').value),
            smart_ocpp_ports: parseInt(document.getElementById('smartOcppPorts').value),
            v2g_ports: parseInt(document.getElementById('v2gPorts').value),
            brand_type: document.getElementById('brandType').value,
            soh_under_70_ratio: parseFloat(document.getElementById('sohUnder70Ratio').value) / 100,
            soh_70_85_ratio: parseFloat(document.getElementById('soh7085Ratio').value) / 100,
            soh_85_95_ratio: parseFloat(document.getElementById('soh8595Ratio').value) / 100,
            soh_over_95_ratio: parseFloat(document.getElementById('sohOver95Ratio').value) / 100
        };

        // 데이터 저장 (종합 분석용)
        lastBasicAnalysisData = {
            capacity: data.capacity_kw,
            location: data.location,
            utilization_dr: data.dr_dispatch_time_ratio * data.regular_pattern_ratio + 0.1,
            utilization_smp: (1 - data.dr_dispatch_time_ratio) * 0.8 + 0.2
        };

        console.log('📊 기초 분석 데이터:', data);

        // SOH 총합 검증
        const sohTotal = data.soh_under_70_ratio + data.soh_70_85_ratio + data.soh_85_95_ratio + data.soh_over_95_ratio;
        if (Math.abs(sohTotal - 1.0) > 0.01) {
            showAlert(`배터리 SOH 분포의 총합이 ${(sohTotal * 100).toFixed(0)}%입니다. 100%가 되도록 조정해주세요.`, 'warning');
            hideLoading();
            return;
        }

        // 서버 요청
        fetch('/basic_analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log('📡 서버 응답 상태:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ 기초 분석 완료:', data);
            hideLoading();
            
            if (data.success) {
                displayBasicResults(data);
                showAlert('기초 분석이 완료되었습니다!', 'success');
            } else {
                showAlert('분석 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'danger');
            }
        })
        .catch(error => {
            console.error('❌ 기초 분석 오류:', error);
            hideLoading();
            showAlert('서버 통신 중 오류가 발생했습니다: ' + error.message, 'danger');
        });
        
    } catch (error) {
        console.error('❌ 기초 분석 실행 오류:', error);
        hideLoading();
        showAlert('분석을 실행할 수 없습니다: ' + error.message, 'danger');
    }
}

// 기초 분석 결과 표시 (통합)
function displayBasicResults(response) {
    console.log('📈 기초 분석 결과 표시 시작 (통합)');
    
    try {
        // 최종 추천 표시 (최상단)
        if (response.final_recommendation) {
            createFinalRecommendation(response.final_recommendation);
        }

        // 메트릭 카드 생성 (기본 분석 데이터)
        if (response.basic_result) {
            createMetricCards(response.basic_result);
        }
        
        // 기본 분석 차트 표시
        if (response.basic_chart_json) {
            try {
                const chartData = JSON.parse(response.basic_chart_json);
                const chartContainer = document.getElementById('chartContainer');
                if (chartContainer) {
                    Plotly.newPlot('chartContainer', chartData.data, chartData.layout, {
                        responsive: true,
                        displayModeBar: true,
                        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
                    });
                    console.log('📊 기본 분석 차트 생성 완료');
                }
            } catch (chartError) {
                console.error('기본 분석 차트 생성 오류:', chartError);
                const chartContainer = document.getElementById('chartContainer');
                if (chartContainer) {
                    chartContainer.innerHTML = '<p class="text-center text-muted">차트를 생성할 수 없습니다.</p>';
                }
            }
        }

        // 점수화 분석 차트 표시
        if (response.score_chart_json) {
            try {
                const scoreChartData = JSON.parse(response.score_chart_json);
                const scoreChartContainer = document.getElementById('scoreChartContainer');
                if (scoreChartContainer) {
                    Plotly.newPlot('scoreChartContainer', scoreChartData.data, scoreChartData.layout, {
                        responsive: true,
                        displayModeBar: true
                    });
                    console.log('📊 점수화 차트 생성 완료');
                }
            } catch (chartError) {
                console.error('점수화 차트 생성 오류:', chartError);
                const scoreChartContainer = document.getElementById('scoreChartContainer');
                if (scoreChartContainer) {
                    scoreChartContainer.innerHTML = '<p class="text-center text-muted">점수화 차트를 생성할 수 없습니다.</p>';
                }
            }
        }

        // 기본 분석 상세 리포트
        if (response.basic_report) {
            const reportContainer = document.getElementById('detailReport');
            if (reportContainer) {
                reportContainer.innerHTML = response.basic_report;
            }
        }

        // 점수화 분석 리포트
        if (response.score_report) {
            const scoreReportContainer = document.getElementById('scoreReport');
            if (scoreReportContainer) {
                scoreReportContainer.innerHTML = response.score_report;
            }
        }

        // 결과 컨테이너 표시
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.style.display = 'block';
            resultsContainer.classList.add('fade-in-up');
        }
        
        console.log('✅ 기초 분석 결과 표시 완료');
        
    } catch (error) {
        console.error('❌ 기초 분석 결과 표시 오류:', error);
        showAlert('결과를 표시하는 중 오류가 발생했습니다.', 'danger');
    }
}

// 최종 추천 생성
function createFinalRecommendation(recommendation) {
    const container = document.getElementById('finalRecommendationContent');
    if (!container) return;
    
    try {
        const recType = recommendation.recommendation;
        const confidence = recommendation.confidence;
        const drWeighted = recommendation.dr_weighted_score;
        const smpWeighted = recommendation.smp_weighted_score;
        const scoreGap = recommendation.score_gap;
        const analysis = recommendation.analysis_summary;
        
        const isDR = recType === 'DR';
        const recName = isDR ? '국민DR' : 'SMP';
        const bgColor = isDR ? '#28a745' : '#17a2b8';
        
        const html = `
            <div class="final-recommendation-card" style="background: linear-gradient(135deg, ${bgColor}, ${bgColor}dd); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
                <h3 style="color: white; margin-bottom: 1rem; font-size: 1.8rem;">
                    <i class="fas fa-trophy me-2"></i>최종 추천 사업 모델
                </h3>
                <div style="font-size: 2.8rem; font-weight: bold; margin-bottom: 1.5rem;">${recName}</div>
                
                <div class="row text-center">
                    <div class="col-md-3">
                        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                            <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">신뢰도</div>
                            <div style="font-size: 1.3rem; font-weight: bold;">${confidence}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                            <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">DR 종합점수</div>
                            <div style="font-size: 1.3rem; font-weight: bold;">${drWeighted}점</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                            <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">SMP 종합점수</div>
                            <div style="font-size: 1.3rem; font-weight: bold;">${smpWeighted}점</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                            <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">점수 차이</div>
                            <div style="font-size: 1.3rem; font-weight: bold;">${scoreGap}점</div>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.3);">
                    <div style="font-size: 1.1rem; margin-bottom: 0.5rem;">
                        <strong>분석 기준:</strong> 수익성 60% + 종합적합성 40%
                    </div>
                    <div style="font-size: 0.95rem; opacity: 0.9;">
                        ROI ${analysis.dr_roi || 0}% vs ${analysis.smp_roi || 0}% | 적합성 점수 ${analysis.dr_score || 0}점 vs ${analysis.smp_score || 0}점
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        console.log('💡 최종 추천 생성 완료');
        
    } catch (error) {
        console.error('❌ 최종 추천 생성 오류:', error);
        container.innerHTML = '<div class="alert alert-warning">최종 추천을 생성할 수 없습니다.</div>';
    }
}

// 메트릭 카드 생성
function createMetricCards(result) {
    const metricsContainer = document.getElementById('metricsCards');
    if (!metricsContainer) return;
    
    try {
        const metrics = [
            {
                title: 'DR 연간 수익',
                value: formatNumber(result.DR?.revenue?.annual_revenue || 0) + '원',
                icon: 'fas fa-won-sign',
                color: 'primary'
            },
            {
                title: 'SMP 연간 수익',
                value: formatNumber(result.SMP?.revenue?.annual_revenue || 0) + '원',
                icon: 'fas fa-chart-line',
                color: 'warning'
            },
            {
                title: 'DR ROI (10년)',
                value: (result.DR?.roi_metrics?.roi || 0).toFixed(1) + '%',
                icon: 'fas fa-percentage',
                color: 'success'
            },
            {
                title: 'SMP ROI (10년)',
                value: (result.SMP?.roi_metrics?.roi || 0).toFixed(1) + '%',
                icon: 'fas fa-chart-area',
                color: 'info'
            }
        ];

        metricsContainer.innerHTML = metrics.map(metric => `
            <div class="col-lg-3 col-md-6 mb-4">
                <div class="metric-card">
                    <div class="metric-icon">
                        <i class="${metric.icon} text-${metric.color}"></i>
                    </div>
                    <div class="metric-value text-${metric.color}">${metric.value}</div>
                    <div class="metric-label">${metric.title}</div>
                </div>
            </div>
        `).join('');
        
        console.log('📊 메트릭 카드 생성 완료');
    } catch (error) {
        console.error('❌ 메트릭 카드 생성 오류:', error);
    }
}

// 고급 분석 관련 함수들 - 확장된 입력폼
function addScenario() {
    scenarioCount++;
    const scenarioContainer = document.getElementById('scenarioContainer');
    if (!scenarioContainer) return;
    
    const scenarioHtml = `
        <div class="scenario-input mb-4 p-4 border rounded-3 shadow-sm" data-scenario="${scenarioCount}" style="background: #f8f9fa;">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0 text-primary">
                    <i class="fas fa-layer-group me-2"></i>시나리오 ${scenarioCount}
                </h5>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeScenario(this)">
                    <i class="fas fa-trash me-1"></i>삭제
                </button>
            </div>
            
            <!-- 기본 정보 -->
            <div class="mb-4">
                <h6 class="text-secondary border-bottom pb-2 mb-3">📋 기본 정보</h6>
                <div class="row">
                    <div class="col-md-4 mb-3">
                        <label class="form-label">시나리오 이름</label>
                        <input type="text" class="form-control scenario-name" value="시나리오${scenarioCount}">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">설비 용량 (kW)</label>
                        <input type="number" class="form-control scenario-capacity" value="1000" min="100" max="15000">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">사업 지역</label>
                        <select class="form-select scenario-location">
                            <option value="수도권">수도권</option>
                            <option value="충청권">충청권</option>
                            <option value="영남권">영남권</option>
                            <option value="호남권">호남권</option>
                            <option value="강원권">강원권</option>
                            <option value="제주권">제주권</option>
                        </select>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-4 mb-3">
                        <label class="form-label">예산 (억원)</label>
                        <input type="number" class="form-control scenario-budget" value="15" min="1" max="1000" step="0.1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">리스크 선호도</label>
                        <select class="form-select scenario-risk">
                            <option value="stable">안정형</option>
                            <option value="neutral" selected>중립형</option>
                            <option value="high_risk">고위험형</option>
                        </select>
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">브랜드 유형</label>
                        <select class="form-select scenario-brand">
                            <option value="b2g_large">공공기관/대기업</option>
                            <option value="others" selected>기타</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <!-- 운영 패턴 -->
            <div class="mb-4">
                <h6 class="text-secondary border-bottom pb-2 mb-3">⚖️ 운영 패턴</h6>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">일정 패턴 비율: <span id="regularPatternValue_${scenarioCount}">70</span>%</label>
                        <input type="range" class="form-range" id="regularPatternRatio_${scenarioCount}" min="0" max="100" value="70">
                        <div class="form-text">차량이 일정한 시간에 주차하는 비율</div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">DR 발령시간 비율: <span id="drDispatchValue_${scenarioCount}">60</span>%</label>
                        <input type="range" class="form-range" id="drDispatchTimeRatio_${scenarioCount}" min="0" max="100" value="60">
                        <div class="form-text">DR 발령 시간대에 주차된 차량 비율</div>
                    </div>
                </div>
            </div>
            
            <!-- 인프라 정보 -->
            <div class="mb-4">
                <h6 class="text-secondary border-bottom pb-2 mb-3">🏗️ 인프라 정보</h6>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">충전부지 (면수)</label>
                        <input type="number" class="form-control scenario-charging-spots" value="50" min="1" max="500">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">수전용량 (MVA)</label>
                        <input type="number" class="form-control scenario-power-capacity" value="0.3" min="0.1" max="5" step="0.1">
                    </div>
                </div>
            </div>
            
            <!-- 충전기 정보 -->
            <div class="mb-4">
                <h6 class="text-secondary border-bottom pb-2 mb-3">🔌 충전기 정보</h6>
                <div class="row">
                    <div class="col-md-4 mb-3">
                        <label class="form-label">전체 포트수</label>
                        <input type="number" class="form-control scenario-total-ports" value="100" min="1" max="1000">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">스마트/OCPP 포트수</label>
                        <input type="number" class="form-control scenario-smart-ports" value="60" min="0" max="1000">
                        <div class="form-text">DR 참여 가능한 포트수</div>
                    </div>
                    <div class="col-md-4 mb-3">
                        <label class="form-label">V2G 포트수</label>
                        <input type="number" class="form-control scenario-v2g-ports" value="30" min="0" max="1000">
                        <div class="form-text">양방향 충전 가능한 포트수</div>
                    </div>
                </div>
            </div>
            
            <!-- 배터리 SOH 분포 -->
            <div class="mb-4">
                <h6 class="text-secondary border-bottom pb-2 mb-3">🔋 배터리 SOH 분포</h6>
                <p class="text-muted small">각 SOH 구간별 차량 비율을 입력하세요 (합계가 100%가 되도록)</p>
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <label class="form-label">70% 이하: <span id="sohUnder70Value_${scenarioCount}">10</span>%</label>
                        <input type="range" class="form-range" id="sohUnder70Ratio_${scenarioCount}" min="0" max="100" value="10">
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">70-85%: <span id="soh7085Value_${scenarioCount}">30</span>%</label>
                        <input type="range" class="form-range" id="soh7085Ratio_${scenarioCount}" min="0" max="100" value="30">
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">85-95%: <span id="soh8595Value_${scenarioCount}">50</span>%</label>
                        <input type="range" class="form-range" id="soh8595Ratio_${scenarioCount}" min="0" max="100" value="50">
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">95% 초과: <span id="sohOver95Value_${scenarioCount}">10</span>%</label>
                        <input type="range" class="form-range" id="sohOver95Ratio_${scenarioCount}" min="0" max="100" value="10">
                    </div>
                    <div class="col-12">
                        <div id="sohTotalDisplay_${scenarioCount}" class="alert alert-info">
                            <small>현재 SOH 분포 총합: <span id="sohTotal_${scenarioCount}">100</span>%</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    scenarioContainer.insertAdjacentHTML('beforeend', scenarioHtml);
    
    // 새로 추가된 시나리오의 슬라이더 설정
    setupScenarioSliders(scenarioCount);
    
    console.log(`➕ 시나리오 ${scenarioCount} 추가 완료`);
}

function addInitialScenario() {
    if (scenarioCount === 0 && document.getElementById('scenarioContainer')) {
        addScenario();
    }
}

function removeScenario(button) {
    const scenarioElement = button.closest('.scenario-input');
    if (scenarioElement) {
        const scenarioNum = scenarioElement.dataset.scenario;
        scenarioElement.remove();
        console.log(`➖ 시나리오 ${scenarioNum} 제거`);
        
        // 시나리오가 하나도 없으면 기본 시나리오 추가
        if (document.querySelectorAll('.scenario-input').length === 0) {
            addScenario();
        }
    }
}

function runAdvancedAnalysis() {
    console.log('🔬 고급 분석 시작');
    showLoading();

    const scenarios = [];
    document.querySelectorAll('.scenario-input').forEach(function(element) {
        const scenarioId = element.dataset.scenario;
        
        // SOH 총합 검증
        const sohTotal = 
            parseInt(element.querySelector(`#sohUnder70Ratio_${scenarioId}`).value) +
            parseInt(element.querySelector(`#soh7085Ratio_${scenarioId}`).value) +
            parseInt(element.querySelector(`#soh8595Ratio_${scenarioId}`).value) +
            parseInt(element.querySelector(`#sohOver95Ratio_${scenarioId}`).value);
        
        if (sohTotal !== 100) {
            hideLoading();
            showAlert(`시나리오 ${scenarioId}의 SOH 분포 총합이 ${sohTotal}%입니다. 100%가 되도록 조정해주세요.`, 'warning');
            return;
        }
        
        const scenario = {
            name: element.querySelector('.scenario-name').value,
            capacity_kw: parseFloat(element.querySelector('.scenario-capacity').value),
            location: element.querySelector('.scenario-location').value,
            budget_billion: parseFloat(element.querySelector('.scenario-budget').value),
            risk_preference: element.querySelector('.scenario-risk').value,
            brand_type: element.querySelector('.scenario-brand').value,
            regular_pattern_ratio: parseFloat(element.querySelector(`#regularPatternRatio_${scenarioId}`).value) / 100,
            dr_dispatch_time_ratio: parseFloat(element.querySelector(`#drDispatchTimeRatio_${scenarioId}`).value) / 100,
            charging_spots: parseInt(element.querySelector('.scenario-charging-spots').value),
            power_capacity_mva: parseFloat(element.querySelector('.scenario-power-capacity').value),
            total_ports: parseInt(element.querySelector('.scenario-total-ports').value),
            smart_ocpp_ports: parseInt(element.querySelector('.scenario-smart-ports').value),
            v2g_ports: parseInt(element.querySelector('.scenario-v2g-ports').value),
            soh_under_70_ratio: parseFloat(element.querySelector(`#sohUnder70Ratio_${scenarioId}`).value) / 100,
            soh_70_85_ratio: parseFloat(element.querySelector(`#soh7085Ratio_${scenarioId}`).value) / 100,
            soh_85_95_ratio: parseFloat(element.querySelector(`#soh8595Ratio_${scenarioId}`).value) / 100,
            soh_over_95_ratio: parseFloat(element.querySelector(`#sohOver95Ratio_${scenarioId}`).value) / 100
        };
        scenarios.push(scenario);
    });

    console.log('📊 고급 분석 시나리오:', scenarios);

    fetch('/advanced_analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({scenarios: scenarios})
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            displayAdvancedResults(data);
            showAlert('고급 분석이 완료되었습니다!', 'success');
        } else {
            showAlert('고급 분석 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'danger');
        }
    })
    .catch(error => {
        console.error('❌ 고급 분석 오류:', error);
        hideLoading();
        showAlert('고급 분석 중 오류가 발생했습니다: ' + error.message, 'danger');
    });
}

function runComprehensiveAnalysis() {
    console.log('🎯 종합 분석 시작');
    
    if (!lastBasicAnalysisData) {
        showAlert('기초 분석을 먼저 실행해주세요.', 'warning');
        return;
    }
    
    showLoading();

    fetch('/comprehensive_analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(lastBasicAnalysisData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            displayComprehensiveResults(data);
            showAlert('종합 분석이 완료되었습니다!', 'success');
        } else {
            showAlert('종합 분석 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'danger');
        }
    })
    .catch(error => {
        console.error('❌ 종합 분석 오류:', error);
        hideLoading();
        showAlert('종합 분석 중 오류가 발생했습니다: ' + error.message, 'danger');
    });
}

// 고급 분석 결과 표시
function displayAdvancedResults(response) {
    console.log('📊 고급 분석 결과 표시 시작');
    const advancedResults = document.getElementById('advancedResults');
    if (!advancedResults) return;
    
    try {
        let resultsHtml = `
            <div class="row mb-5">
                <div class="col-lg-12 text-center">
                    <h2 class="section-title">고급 분석 결과</h2>
                    <p class="section-subtitle">다중 시나리오 기반 DR/SMP 종합 비교 분석</p>
                </div>
            </div>
        `;
        
        // 시나리오별 결과 카드가 있는 경우
        if (response.scenarios && response.scenarios.length > 0) {
            resultsHtml += '<div class="row mb-5">';
            
            response.scenarios.forEach(function(scenario, index) {
                const drBetter = (scenario.dr_score || 0) > (scenario.smp_score || 0);
                const recommendedBusiness = drBetter ? 'DR' : 'SMP';
                const recommendedColor = drBetter ? '#1f77b4' : '#ff7f0e';
                
                resultsHtml += `
                    <div class="col-lg-6 mb-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header" style="background: ${recommendedColor}; color: white;">
                                <h6 class="mb-0">
                                    <i class="fas fa-chart-pie me-2"></i>${scenario.name || `시나리오 ${index + 1}`}
                                    <span class="badge bg-light text-dark float-end">추천: ${recommendedBusiness}</span>
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <small class="text-muted">설비 용량</small>
                                        <div class="fw-bold">${formatNumber(scenario.capacity_kw || 0)}kW</div>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">사업 지역</small>
                                        <div class="fw-bold">${scenario.location || 'N/A'}</div>
                                    </div>
                                </div>
                                <hr>
                                <div class="row">
                                    <div class="col-6">
                                        <small class="text-muted">DR 점수</small>
                                        <div class="fw-bold text-primary">${(scenario.dr_score || 0).toFixed(1)}점</div>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">SMP 점수</small>
                                        <div class="fw-bold text-warning">${(scenario.smp_score || 0).toFixed(1)}점</div>
                                    </div>
                                </div>
                                <div class="row mt-2">
                                    <div class="col-6">
                                        <small class="text-muted">DR ROI</small>
                                        <div class="fw-bold text-success">${(scenario.dr_roi || 0).toFixed(1)}%</div>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">SMP ROI</small>
                                        <div class="fw-bold text-info">${(scenario.smp_roi || 0).toFixed(1)}%</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            resultsHtml += '</div>';
        }
        // 기존 포트폴리오 결과가 있는 경우 (호환성)
        else if (response.portfolio && response.portfolio.scenarios) {
            resultsHtml += '<div class="row mb-5">';
            
            response.portfolio.scenarios.forEach(function(scenario, index) {
                resultsHtml += `
                    <div class="col-lg-6 mb-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0"><i class="fas fa-chart-pie me-2"></i>${scenario.scenario || `시나리오 ${index + 1}`}</h6>
                            </div>
                            <div class="card-body">
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <small class="text-muted">설비 용량</small>
                                        <div class="fw-bold">${formatNumber(scenario.capacity || 0)}kW</div>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">사업 지역</small>
                                        <div class="fw-bold">${scenario.location || 'N/A'}</div>
                                    </div>
                                </div>
                                <hr>
                                <div class="row">
                                    <div class="col-6">
                                        <small class="text-muted">DR ROI</small>
                                        <div class="fw-bold text-primary">${(scenario.dr_roi || 0).toFixed(1)}%</div>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">SMP ROI</small>
                                        <div class="fw-bold text-warning">${(scenario.smp_roi || 0).toFixed(1)}%</div>
                                    </div>
                                </div>
                                <div class="row mt-2">
                                    <div class="col-6">
                                        <small class="text-muted">DR 샤프비율</small>
                                        <div class="fw-bold text-success">${(scenario.dr_sharpe || 0).toFixed(2)}</div>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">SMP 샤프비율</small>
                                        <div class="fw-bold text-info">${(scenario.smp_sharpe || 0).toFixed(2)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            resultsHtml += '</div>';
        } else {
            resultsHtml += '<div class="row"><div class="col-12"><div class="alert alert-warning">고급 분석 데이터를 찾을 수 없습니다.</div></div></div>';
        }
        
        advancedResults.innerHTML = resultsHtml;
        advancedResults.style.display = 'block';
        advancedResults.classList.add('fade-in-up');
        
        console.log('✅ 고급 분석 결과 표시 완료');
        
    } catch (error) {
        console.error('❌ 고급 분석 결과 표시 오류:', error);
        advancedResults.innerHTML = '<div class="alert alert-danger">결과를 표시하는 중 오류가 발생했습니다.</div>';
        advancedResults.style.display = 'block';
    }
}

function displayComprehensiveResults(response) {
    console.log('🎯 종합 분석 결과 표시');
    const comprehensiveResults = document.getElementById('comprehensiveResults');
    if (comprehensiveResults) {
        const reportContainer = document.getElementById('comprehensiveReport');
        if (reportContainer && response.report) {
            reportContainer.innerHTML = response.report;
        }
        comprehensiveResults.style.display = 'block';
        comprehensiveResults.classList.add('fade-in-up');
    }
}

console.log('✅ V2G 분석 시스템 JavaScript (고급 분석 확장 버전) 로드 완료');