#!/usr/bin/env python3
"""
V2G 사업 분석 웹 서버 - 기초 분석 통합 + 고급 분석 개선 버전 (완전판)
"""

import os
import sys
import threading
import time
import webbrowser
import re
from flask import Flask, render_template, request, jsonify, send_from_directory

# 기존 모듈들 import
try:
    from v2g_business_analyzer import V2GBusinessAnalyzer, V2GBusinessConsultant
    from advances_analysis import AdvancedV2GAnalyzer, BusinessScenario, run_market_benchmarking_analysis
    BASIC_FEATURES_AVAILABLE = True
    print("✅ 기본 분석 모듈 로드 완료")
except ImportError as e:
    print(f"❌ 기본 모듈 import 오류: {e}")
    sys.exit(1)

# 새 모듈들은 있을 때만 import (선택적)
try:
    from v2g_score_analyzer import V2GScoreAnalyzer, V2GScoreInput
    from v2g_integrated_analyzer import V2GIntegratedAnalyzer, run_score_analysis_from_web, run_integrated_analysis_from_web
    NEW_FEATURES_AVAILABLE = True
    print("✅ 점수화 기능 모듈 로드 완료")
except ImportError as e:
    NEW_FEATURES_AVAILABLE = False
    print(f"⚠️ 점수화 모듈 없음 - 기본 기능만 사용: {e}")

def create_enhanced_app():
    """Flask 앱 생성 - 기초 분석 통합 + 고급 분석 개선"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    assets_dir = os.path.join(base_dir, 'assets')
    
    for directory in [template_dir, static_dir, assets_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # 분석기들 초기화
    base_analyzer = V2GBusinessAnalyzer()
    consultant = V2GBusinessConsultant()
    advanced_analyzer = AdvancedV2GAnalyzer()
    
    if NEW_FEATURES_AVAILABLE:
        score_analyzer = V2GScoreAnalyzer()
        integrated_analyzer = V2GIntegratedAnalyzer()
    
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(assets_dir, filename)
    
    @app.context_processor
    def utility_processor():
        def check_asset_exists(filename):
            file_path = os.path.join(assets_dir, filename)
            return os.path.exists(file_path)
        return dict(check_asset_exists=check_asset_exists)
    
    @app.route('/')
    def index():
        """메인 페이지"""
        return render_template('index.html')
    
    # 기초 분석 API (기본분석 + 점수화분석 통합)
    @app.route('/basic_analysis', methods=['POST'])
    def basic_analysis():
        """기초 분석 API - 기본분석과 점수화분석 통합"""
        try:
            data = request.get_json()
            
            # 점수화 분석 데이터에서 기본 분석 데이터 추출
            capacity = float(data.get('capacity_kw', 1000))
            location = data.get('location', '수도권')
            
            # 기본 분석용 활용률 계산
            dr_dispatch_ratio = float(data.get('dr_dispatch_time_ratio', 0.6))
            regular_pattern = float(data.get('regular_pattern_ratio', 0.7))
            
            # DR/SMP 활용률 추정
            utilization_dr = min(0.95, dr_dispatch_ratio * regular_pattern + 0.1)
            utilization_smp = min(0.85, (1 - dr_dispatch_ratio) * 0.8 + 0.2)
            
            print(f"🔍 기초 분석 시작 - {location} {capacity:,}kW (DR: {utilization_dr:.1%}, SMP: {utilization_smp:.1%})")
            
            # 1. 기본 수익성 분석 실행
            basic_result, basic_fig, basic_report = consultant.run_consultation(
                capacity_kw=capacity,
                location=location,
                utilization_dr=utilization_dr,
                utilization_smp=utilization_smp
            )
            
            # 2. 기본 분석 리포트에서 추천 부분 제거
            cleaned_basic_report = remove_recommendation_from_report(basic_report)
            
            result = {
                'success': True,
                'basic_result': basic_result,
                'basic_chart_json': basic_fig.to_json(),
                'basic_report': cleaned_basic_report
            }
            
            # 3. 점수화 분석 실행 (모듈이 있는 경우)
            if NEW_FEATURES_AVAILABLE:
                try:
                    score_inputs = {
                        'capacity_kw': capacity,
                        'location': location,
                        'budget_billion': float(data.get('budget_billion', 15)),
                        'risk_preference': data.get('risk_preference', 'neutral'),
                        'regular_pattern_ratio': float(data.get('regular_pattern_ratio', 0.7)),
                        'dr_dispatch_time_ratio': float(data.get('dr_dispatch_time_ratio', 0.6)),
                        'charging_spots': int(data.get('charging_spots', 50)),
                        'power_capacity_mva': float(data.get('power_capacity_mva', 0.3)),
                        'total_ports': int(data.get('total_ports', 100)),
                        'smart_ocpp_ports': int(data.get('smart_ocpp_ports', 60)),
                        'v2g_ports': int(data.get('v2g_ports', 30)),
                        'brand_type': data.get('brand_type', 'others'),
                        'soh_under_70_ratio': float(data.get('soh_under_70_ratio', 0.1)),
                        'soh_70_85_ratio': float(data.get('soh_70_85_ratio', 0.3)),
                        'soh_85_95_ratio': float(data.get('soh_85_95_ratio', 0.5)),
                        'soh_over_95_ratio': float(data.get('soh_over_95_ratio', 0.1))
                    }
                    
                    score_result = run_score_analysis_from_web(score_inputs)
                    
                    if score_result['success']:
                        result['score_result'] = score_result['result']
                        result['score_chart_json'] = score_result['chart_json']
                        result['score_report'] = score_result['report']
                        
                        # 최종 추천 생성 (점수화 결과 기반)
                        result['final_recommendation'] = generate_final_recommendation(
                            basic_result, score_result['result']
                        )
                        
                        print("✅ 기초 분석 완료 (기본분석 + 점수화분석)")
                    else:
                        print("⚠️ 점수화 분석 실패, 기본분석만 제공")
                        
                except Exception as score_error:
                    print(f"⚠️ 점수화 분석 오류: {score_error}")
                    # 점수화 분석 실패해도 기본분석은 제공
            
            return jsonify(result)
            
        except Exception as e:
            print(f"❌ 기초 분석 오류: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # 새로운 고급 분석 API - 점수화 시스템 포함
    @app.route('/advanced_analysis', methods=['POST'])
    def advanced_analysis():
        """고급 분석 API - 점수화 시스템 포함"""
        try:
            data = request.get_json()
            scenarios_data = data.get('scenarios', [])
            
            print(f"🔬 고급 분석 시작 - {len(scenarios_data)}개 시나리오")
            
            # 시나리오별 점수화 분석 실행
            if NEW_FEATURES_AVAILABLE:
                scenario_results = []
                
                for i, scenario_data in enumerate(scenarios_data):
                    try:
                        # 점수화 분석을 위한 입력 데이터 구성
                        score_inputs = {
                            'capacity_kw': float(scenario_data.get('capacity_kw', 1000)),
                            'location': scenario_data.get('location', '수도권'),
                            'budget_billion': float(scenario_data.get('budget_billion', 15)),
                            'risk_preference': scenario_data.get('risk_preference', 'neutral'),
                            'regular_pattern_ratio': float(scenario_data.get('regular_pattern_ratio', 0.7)),
                            'dr_dispatch_time_ratio': float(scenario_data.get('dr_dispatch_time_ratio', 0.6)),
                            'charging_spots': int(scenario_data.get('charging_spots', 50)),
                            'power_capacity_mva': float(scenario_data.get('power_capacity_mva', 0.3)),
                            'total_ports': int(scenario_data.get('total_ports', 100)),
                            'smart_ocpp_ports': int(scenario_data.get('smart_ocpp_ports', 60)),
                            'v2g_ports': int(scenario_data.get('v2g_ports', 30)),
                            'brand_type': scenario_data.get('brand_type', 'others'),
                            'soh_under_70_ratio': float(scenario_data.get('soh_under_70_ratio', 0.1)),
                            'soh_70_85_ratio': float(scenario_data.get('soh_70_85_ratio', 0.3)),
                            'soh_85_95_ratio': float(scenario_data.get('soh_85_95_ratio', 0.5)),
                            'soh_over_95_ratio': float(scenario_data.get('soh_over_95_ratio', 0.1))
                        }
                        
                        # 점수화 분석 실행
                        score_result = run_score_analysis_from_web(score_inputs)
                        
                        # 기본 수익성 분석도 실행
                        dr_dispatch_ratio = score_inputs['dr_dispatch_time_ratio']
                        regular_pattern = score_inputs['regular_pattern_ratio']
                        utilization_dr = min(0.95, dr_dispatch_ratio * regular_pattern + 0.1)
                        utilization_smp = min(0.85, (1 - dr_dispatch_ratio) * 0.8 + 0.2)
                        
                        basic_result, _, _ = consultant.run_consultation(
                            capacity_kw=score_inputs['capacity_kw'],
                            location=score_inputs['location'],
                            utilization_dr=utilization_dr,
                            utilization_smp=utilization_smp
                        )
                        
                        scenario_results.append({
                            'name': scenario_data.get('name', f'시나리오{i+1}'),
                            'capacity_kw': score_inputs['capacity_kw'],
                            'location': score_inputs['location'],
                            'budget_billion': score_inputs['budget_billion'],
                            'risk_preference': score_inputs['risk_preference'],
                            'brand_type': score_inputs['brand_type'],
                            'dr_score': score_result['result']['total_scores']['dr'] if score_result['success'] else 0,
                            'smp_score': score_result['result']['total_scores']['smp'] if score_result['success'] else 0,
                            'dr_roi': basic_result['DR']['roi_metrics']['roi'],
                            'smp_roi': basic_result['SMP']['roi_metrics']['roi']
                        })
                        
                        print(f"✅ 시나리오 {i+1} 분석 완료 - DR점수: {scenario_results[-1]['dr_score']:.1f}, SMP점수: {scenario_results[-1]['smp_score']:.1f}")
                        
                    except Exception as scenario_error:
                        print(f"⚠️ 시나리오 {i+1} 분석 오류: {scenario_error}")
                        continue
                
                return jsonify({
                    'success': True,
                    'scenarios': scenario_results,
                    'message': f'{len(scenario_results)}개 시나리오 점수화 분석 완료'
                })
            
            # 점수화 모듈이 없는 경우 기존 방식
            else:
                scenarios = []
                for s in scenarios_data:
                    scenario = BusinessScenario(
                        name=s.get('name', '시나리오'),
                        capacity_kw=float(s.get('capacity_kw', 1000)),
                        location=s.get('location', '수도권'),
                        investment_budget=float(s.get('budget_billion', 15)) * 100000000,  # 억원을 원으로 변환
                        target_roi=15.0,
                        risk_tolerance=s.get('risk_preference', 'neutral')
                    )
                    scenarios.append(scenario)
                
                if not scenarios:
                    scenarios = [BusinessScenario("기본시나리오", 1000, "수도권", 1500000000, 15.0, "neutral")]
                
                portfolio_result = advanced_analyzer.portfolio_optimization(scenarios)
                base_scenario = scenarios[0]
                
                sensitivity_vars = {
                    'utilization_dr': [0.5, 0.6, 0.7, 0.8, 0.9],
                    'utilization_smp': [0.4, 0.5, 0.6, 0.7, 0.8],
                    'capacity': [base_scenario.capacity_kw * 0.5, base_scenario.capacity_kw * 0.75, 
                               base_scenario.capacity_kw, base_scenario.capacity_kw * 1.25, base_scenario.capacity_kw * 1.5]
                }
                
                sensitivity_result = advanced_analyzer.sensitivity_analysis(base_scenario, sensitivity_vars)
                risk_result = advanced_analyzer.risk_analysis(base_scenario)
                
                return jsonify({
                    'success': True,
                    'portfolio': portfolio_result,
                    'sensitivity': sensitivity_result,
                    'risk': risk_result
                })
            
        except Exception as e:
            print(f"❌ 고급 분석 오류: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # 기존 종합 분석 API 유지
    @app.route('/comprehensive_analysis', methods=['POST'])
    def comprehensive_analysis():
        """종합 분석 API"""
        try:
            data = request.get_json() if request.is_json else {}
            
            user_capacity = data.get('capacity', 1000)
            user_location = data.get('location', '수도권')
            user_dr_util = data.get('utilization_dr', 0.7)
            user_smp_util = data.get('utilization_smp', 0.6)
            
            comprehensive_report = run_market_benchmarking_analysis(
                user_capacity=user_capacity,
                user_location=user_location,
                user_dr_util=user_dr_util,
                user_smp_util=user_smp_util
            )
            
            return jsonify({
                'success': True,
                'report': comprehensive_report,
                'message': '개별 시나리오 상세 비교 분석이 완료되었습니다.'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app

def remove_recommendation_from_report(report):
    """기본 분석 리포트에서 추천 관련 부분 제거"""
    if not report:
        return report
    
    # HTML 형태의 리포트에서 추천 부분 제거
    if '<' in report:
        # 추천 관련 섹션 패턴들 제거
        patterns_to_remove = [
            r'<div[^>]*style="[^"]*background[^"]*#[^"]*"[^>]*>.*?최종 추천.*?</div>',
            r'<div[^>]*class="[^"]*recommendation[^"]*"[^>]*>.*?</div>',
            r'<h[1-6][^>]*>.*?추천.*?</h[1-6]>.*?(?=<h[1-6]|$)',
            r'<div[^>]*>.*?추천 사업.*?</div>',
            r'<div[^>]*>.*?최종 추천.*?</div>',
            r'현재 조건.*?추천합니다\.',  # 추가: 특정 문구 제거
            r'현재 조건.*?에서는.*?사업을.*?추천.*?',  # 추가: 특정 문구 제거
            r'<p[^>]*>.*?현재 조건.*?추천.*?</p>',  # HTML 태그 내 특정 문구
            r'현재 조건.*?\(.*?\).*?에서는.*?사업을.*?추천.*?\.?'  # 더 포괄적인 패턴
        ]
        
        for pattern in patterns_to_remove:
            report = re.sub(pattern, '', report, flags=re.DOTALL | re.IGNORECASE)
    
    # 텍스트 형태의 리포트에서 추천 부분 제거
    else:
        lines = report.split('\n')
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            # 추천 관련 키워드가 있는 라인 건너뛰기
            if any(keyword in line for keyword in ['추천', '권장', '최종 판단', '현재 조건']):
                skip_section = True
                continue
            elif line.strip() == '' and skip_section:
                skip_section = False
                continue
            elif not skip_section:
                filtered_lines.append(line)
        
        report = '\n'.join(filtered_lines)
    
    return report

def generate_final_recommendation(basic_result, score_result):
    """점수화 결과를 기반으로 최종 추천 생성"""
    try:
        # 수익성 지표
        dr_roi = basic_result.get('DR', {}).get('roi_metrics', {}).get('roi', 0)
        smp_roi = basic_result.get('SMP', {}).get('roi_metrics', {}).get('roi', 0)
        
        # 점수화 지표
        dr_score = score_result.get('total_scores', {}).get('dr', 0)
        smp_score = score_result.get('total_scores', {}).get('smp', 0)
        score_recommendation = score_result.get('recommendation', 'DR')
        
        # 가중 종합 점수 (수익성 60% + 점수화 40%)
        dr_weighted = (dr_roi * 0.6) + (dr_score * 0.4)
        smp_weighted = (smp_roi * 0.6) + (smp_score * 0.4)
        
        final_recommendation = 'DR' if dr_weighted > smp_weighted else 'SMP'
        weighted_gap = abs(dr_weighted - smp_weighted)
        
        # 신뢰도 계산
        if weighted_gap > 15:
            confidence = "매우 높음"
        elif weighted_gap > 10:
            confidence = "높음"
        elif weighted_gap > 5:
            confidence = "보통"
        else:
            confidence = "낮음"
        
        return {
            'recommendation': final_recommendation,
            'confidence': confidence,
            'dr_weighted_score': round(dr_weighted, 1),
            'smp_weighted_score': round(smp_weighted, 1),
            'score_gap': round(weighted_gap, 1),
            'analysis_summary': {
                'dr_roi': round(dr_roi, 1),
                'smp_roi': round(smp_roi, 1),
                'dr_score': round(dr_score, 1),
                'smp_score': round(smp_score, 1)
            }
        }
        
    except Exception as e:
        print(f"❌ 최종 추천 생성 오류: {e}")
        return {
            'recommendation': 'DR',
            'confidence': '낮음',
            'dr_weighted_score': 0,
            'smp_weighted_score': 0,
            'score_gap': 0,
            'analysis_summary': {}
        }

def run_server_enhanced():
    """서버 실행"""
    try:
        app = create_enhanced_app()
        
        print("=" * 70)
        print("V2G 사업 분석 시스템 (기초 분석 통합 + 고급 분석 확장 버전)")
        print("=" * 70)
        print("🌐 서버 시작 중...")
        print("📱 브라우저에서 http://127.0.0.1:5000 접속")
        print("📊 주요 기능:")
        print("   - 기초 분석 (기본분석 + 점수화분석 통합)")
        print("   - 고급 분석 (다중 시나리오 점수화 기반)")
        print("   - 종합 분석 (시장 벤치마킹)")
        if NEW_FEATURES_AVAILABLE:
            print("   - 9개 지표 기반 점수화 시스템")
        print("⚡ Ctrl+C로 서버 종료")
        print("=" * 70)
        
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://127.0.0.1:5000')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False, threaded=True)
        
    except KeyboardInterrupt:
        print("\n👋 서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")

if __name__ == '__main__':
    run_server_enhanced()