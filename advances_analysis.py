import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json
from v2g_business_analyzer import V2GBusinessAnalyzer
from v2g_business_analyzer import V2GBusinessConsultant

@dataclass
class BusinessScenario:
    """사업 시나리오 데이터 클래스"""
    name: str
    capacity_kw: float
    location: str
    investment_budget: float
    target_roi: float
    risk_tolerance: str  # 'low', 'medium', 'high'
    utilization_dr: float = 0.7  # DR 활용률 추가
    utilization_smp: float = 0.6  # SMP 활용률 추가

class AdvancedV2GAnalyzer:
    """고급 V2G 사업 분석기 - 웹 입력 변수 완전 반영"""
    
    def __init__(self):
        self.base_analyzer = V2GBusinessAnalyzer()
        self.scenarios = []
        
    def add_scenario(self, scenario: BusinessScenario):
        """시나리오 추가"""
        self.scenarios.append(scenario)
    
    def sensitivity_analysis(self, base_scenario: BusinessScenario, 
                           variables: Dict[str, List[float]]) -> Dict:
        """민감도 분석 - 웹 입력 시나리오 기반"""
        results = {}
        
        for var_name, var_values in variables.items():
            var_results = []
            
            for value in var_values:
                # 변수에 따른 시나리오 조정 (웹 입력값 활용)
                if var_name == 'capacity':
                    # 용량 변경 시나리오
                    analysis = self.base_analyzer.generate_comparison_report(
                        value, base_scenario.location, 
                        base_scenario.utilization_dr, base_scenario.utilization_smp
                    )
                elif var_name == 'utilization_dr':
                    # DR 활용률 변경 시나리오
                    analysis = self.base_analyzer.generate_comparison_report(
                        base_scenario.capacity_kw, base_scenario.location,
                        value, base_scenario.utilization_smp
                    )
                elif var_name == 'utilization_smp':
                    # SMP 활용률 변경 시나리오
                    analysis = self.base_analyzer.generate_comparison_report(
                        base_scenario.capacity_kw, base_scenario.location,
                        base_scenario.utilization_dr, value
                    )
                elif var_name == 'location':
                    # 지역 변경 시나리오 (value는 지역명)
                    analysis = self.base_analyzer.generate_comparison_report(
                        base_scenario.capacity_kw, value,
                        base_scenario.utilization_dr, base_scenario.utilization_smp
                    )
                    var_results.append({
                        'value': value,
                        'dr_roi': analysis['DR']['roi_metrics']['roi'],
                        'smp_roi': analysis['SMP']['roi_metrics']['roi']
                    })
                    continue
                else:
                    # 기본 분석
                    analysis = self.base_analyzer.generate_comparison_report(
                        base_scenario.capacity_kw, base_scenario.location,
                        base_scenario.utilization_dr, base_scenario.utilization_smp
                    )
                
                var_results.append({
                    'value': value,
                    'dr_roi': analysis['DR']['roi_metrics']['roi'],
                    'smp_roi': analysis['SMP']['roi_metrics']['roi']
                })
            
            results[var_name] = var_results
        
        return results
    
    def risk_analysis(self, scenario: BusinessScenario) -> Dict:
        """리스크 분석 - 웹 입력 시나리오 기반"""
        # 몬테카르로 시뮬레이션
        num_simulations = 1000
        dr_rois = []
        smp_rois = []
        
        for _ in range(num_simulations):
            # 랜덤 변수들 (웹 입력값을 중심으로 변동)
            capacity_variation = np.random.normal(1.0, 0.1)  # ±10% 변동
            utilization_dr = max(0.1, min(0.95, np.random.normal(scenario.utilization_dr, 0.1)))
            utilization_smp = max(0.1, min(0.85, np.random.normal(scenario.utilization_smp, 0.1)))
            
            adjusted_capacity = scenario.capacity_kw * capacity_variation
            
            # 웹 입력 기반 분석
            analysis = self.base_analyzer.generate_comparison_report(
                adjusted_capacity, scenario.location, utilization_dr, utilization_smp
            )
            
            dr_rois.append(analysis['DR']['roi_metrics']['roi'])
            smp_rois.append(analysis['SMP']['roi_metrics']['roi'])
        
        return {
            'dr_risk_metrics': {
                'mean_roi': np.mean(dr_rois),
                'std_roi': np.std(dr_rois),
                'var_95': np.percentile(dr_rois, 5),  # 95% VaR
                'var_99': np.percentile(dr_rois, 1),  # 99% VaR
                'prob_positive': len([x for x in dr_rois if x > 0]) / len(dr_rois)
            },
            'smp_risk_metrics': {
                'mean_roi': np.mean(smp_rois),
                'std_roi': np.std(smp_rois),
                'var_95': np.percentile(smp_rois, 5),
                'var_99': np.percentile(smp_rois, 1),
                'prob_positive': len([x for x in smp_rois if x > 0]) / len(smp_rois)
            },
            'base_scenario': {
                'name': scenario.name,
                'capacity': scenario.capacity_kw,
                'location': scenario.location,
                'dr_utilization': scenario.utilization_dr,
                'smp_utilization': scenario.utilization_smp
            }
        }
    
    def portfolio_optimization(self, scenarios: List[BusinessScenario]) -> Dict:
        """포트폴리오 최적화 - 웹 입력 시나리오들 기반"""
        results = []
        
        for scenario in scenarios:
            # 각 시나리오의 웹 입력값들을 모두 활용
            analysis = self.base_analyzer.generate_comparison_report(
                scenario.capacity_kw, scenario.location, 
                scenario.utilization_dr, scenario.utilization_smp
            )
            
            risk_analysis = self.risk_analysis(scenario)
            
            # 샤프 비율 계산 (위험 대비 수익)
            dr_sharpe = (risk_analysis['dr_risk_metrics']['mean_roi'] - 3) / risk_analysis['dr_risk_metrics']['std_roi'] if risk_analysis['dr_risk_metrics']['std_roi'] > 0 else 0
            smp_sharpe = (risk_analysis['smp_risk_metrics']['mean_roi'] - 3) / risk_analysis['smp_risk_metrics']['std_roi'] if risk_analysis['smp_risk_metrics']['std_roi'] > 0 else 0
            
            results.append({
                'scenario': scenario.name,
                'capacity': scenario.capacity_kw,
                'location': scenario.location,
                'dr_utilization': scenario.utilization_dr,
                'smp_utilization': scenario.utilization_smp,
                'dr_roi': analysis['DR']['roi_metrics']['roi'],
                'smp_roi': analysis['SMP']['roi_metrics']['roi'],
                'dr_sharpe': dr_sharpe,
                'smp_sharpe': smp_sharpe,
                'dr_risk': risk_analysis['dr_risk_metrics']['std_roi'],
                'smp_risk': risk_analysis['smp_risk_metrics']['std_roi'],
                'dr_annual_revenue': analysis['DR']['revenue']['annual_revenue'],
                'smp_annual_revenue': analysis['SMP']['revenue']['annual_revenue']
            })
        
        # 포트폴리오 효율 곡선 계산
        df = pd.DataFrame(results)
        
        if len(df) > 0:
            best_dr_sharpe = df.loc[df['dr_sharpe'].idxmax()]['scenario'] if not df['dr_sharpe'].isna().all() else 'N/A'
            best_smp_sharpe = df.loc[df['smp_sharpe'].idxmax()]['scenario'] if not df['smp_sharpe'].isna().all() else 'N/A'
            lowest_risk_dr = df.loc[df['dr_risk'].idxmin()]['scenario'] if not df['dr_risk'].isna().all() else 'N/A'
            lowest_risk_smp = df.loc[df['smp_risk'].idxmin()]['scenario'] if not df['smp_risk'].isna().all() else 'N/A'
        else:
            best_dr_sharpe = best_smp_sharpe = lowest_risk_dr = lowest_risk_smp = 'N/A'
        
        return {
            'scenarios': results,
            'best_dr_sharpe': best_dr_sharpe,
            'best_smp_sharpe': best_smp_sharpe,
            'lowest_risk_dr': lowest_risk_dr,
            'lowest_risk_smp': lowest_risk_smp
        }

# 강화된 시장 벤치마킹 분석 함수
def run_market_benchmarking_analysis(user_capacity=1000, user_location="수도권", user_dr_util=0.7, user_smp_util=0.6):
    """개별 시나리오 대 사용자 상세 비교 분석 - 메인 콘텐츠 강화"""
    analyzer = AdvancedV2GAnalyzer()
    
    # 시장 표준 시나리오들 (고정)
    market_scenarios = [
        BusinessScenario("A_소규모수도권", 500, "수도권", 500_000_000, 15.0, "medium", 0.7, 0.6),
        BusinessScenario("B_중규모충청권", 1000, "충청권", 1_000_000_000, 12.0, "low", 0.75, 0.65),
        BusinessScenario("C_대규모영남권", 2000, "영남권", 2_000_000_000, 18.0, "high", 0.8, 0.7),
        BusinessScenario("D_초대규모수도권", 5000, "수도권", 5_000_000_000, 20.0, "high", 0.85, 0.75),
    ]
    
    # 사용자 시나리오 (E)
    user_scenario = BusinessScenario(
        f"E_사용자계획", 
        user_capacity, user_location, 
        user_capacity * 1400000,  # kW당 140만원 추정
        15.0, "medium", user_dr_util, user_smp_util
    )
    
    # HTML 리포트 시작
    report = f"""
<div style="font-family: 'Noto Serif KR', '함초롱바탕', serif; line-height: 1.6;">

<h3 style="text-align: center; color: #0d6efd; margin-bottom: 2rem; border-bottom: 3px solid #0d6efd; padding-bottom: 1rem;">🎯 V2G 사업 개별 시나리오 상세 비교 분석</h3>

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
    <h4 style="color: white; margin-bottom: 1rem; font-size: 1.4rem;">📊 분석 대상 - 사용자 시나리오(E)</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold;">{user_location}</div>
            <div style="font-size: 0.9rem;">사업 지역</div>
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold;">{user_capacity:,}kW</div>
            <div style="font-size: 0.9rem;">설비 용량</div>
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold;">DR {user_dr_util*100:.0f}%</div>
            <div style="font-size: 0.9rem;">DR 활용률</div>
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold;">SMP {user_smp_util*100:.0f}%</div>
            <div style="font-size: 0.9rem;">SMP 활용률</div>
        </div>
    </div>
</div>
"""
    
    # 각 시나리오 분석 결과 수집
    consultant = V2GBusinessConsultant()
    scenario_analyses = {}
    
    # 시장 표준 시나리오들 분석
    for scenario in market_scenarios:
        result, _, _ = consultant.run_consultation(
            scenario.capacity_kw, scenario.location, scenario.utilization_dr, scenario.utilization_smp
        )
        scenario_letter = scenario.name.split('_')[0]
        scenario_analyses[scenario_letter] = {
            'scenario': scenario,
            'result': result,
            'dr_roi': result['DR']['roi_metrics']['roi'],
            'smp_roi': result['SMP']['roi_metrics']['roi'],
            'dr_revenue': result['DR']['revenue']['annual_revenue'],
            'smp_revenue': result['SMP']['revenue']['annual_revenue'],
            'dr_payback': result['DR']['roi_metrics']['payback_period'],
            'smp_payback': result['SMP']['roi_metrics']['payback_period'],
            'dr_npv': result['DR']['roi_metrics']['npv'],
            'smp_npv': result['SMP']['roi_metrics']['npv']
        }
    
    # 사용자 시나리오(E) 분석
    user_result, _, _ = consultant.run_consultation(
        user_scenario.capacity_kw, user_scenario.location, user_scenario.utilization_dr, user_scenario.utilization_smp
    )
    scenario_analyses['E'] = {
        'scenario': user_scenario,
        'result': user_result,
        'dr_roi': user_result['DR']['roi_metrics']['roi'],
        'smp_roi': user_result['SMP']['roi_metrics']['roi'],
        'dr_revenue': user_result['DR']['revenue']['annual_revenue'],
        'smp_revenue': user_result['SMP']['revenue']['annual_revenue'],
        'dr_payback': user_result['DR']['roi_metrics']['payback_period'],
        'smp_payback': user_result['SMP']['roi_metrics']['payback_period'],
        'dr_npv': user_result['DR']['roi_metrics']['npv'],
        'smp_npv': user_result['SMP']['roi_metrics']['npv']
    }
    
    # 개별 비교 분석 - 메인 콘텐츠
    report += """
<h4 style="color: #0d6efd; margin: 2rem 0 1rem 0; border-bottom: 2px solid #0d6efd; padding-bottom: 0.5rem; font-size: 1.6rem;">
    🔍 개별 시나리오 대 사용자(E) 상세 비교 분석
</h4>
"""
    
    comparison_results = []
    user_data = scenario_analyses['E']
    
    for scenario_letter in ['A', 'B', 'C', 'D']:
        market_data = scenario_analyses[scenario_letter]
        
        # 상세 비교 분석
        # 1. 조건 비교
        location_same = market_data['scenario'].location == user_data['scenario'].location
        capacity_ratio = user_data['scenario'].capacity_kw / market_data['scenario'].capacity_kw
        dr_util_diff = (user_data['scenario'].utilization_dr - market_data['scenario'].utilization_dr) * 100
        smp_util_diff = (user_data['scenario'].utilization_smp - market_data['scenario'].utilization_smp) * 100
        
        # 2. 수익성 비교
        dr_roi_diff = user_data['dr_roi'] - market_data['dr_roi']
        smp_roi_diff = user_data['smp_roi'] - market_data['smp_roi']
        dr_revenue_ratio = user_data['dr_revenue'] / market_data['dr_revenue']
        smp_revenue_ratio = user_data['smp_revenue'] / market_data['smp_revenue']
        dr_payback_diff = market_data['dr_payback'] - user_data['dr_payback']  # 짧을수록 좋음
        smp_payback_diff = market_data['smp_payback'] - user_data['smp_payback']
        
        # 3. 우위 판단 함수들
        def get_advantage_icon_text(diff, threshold=1.0):
            if diff > threshold:
                return "🟢 E 우위", "#198754"
            elif diff < -threshold:
                return "🔴 시나리오 우위", "#dc3545"
            else:
                return "🟡 비슷함", "#ffc107"
        
        def get_capacity_comparison():
            if capacity_ratio > 2:
                return f"🟢 E가 {capacity_ratio:.1f}배 대규모", "#198754"
            elif capacity_ratio > 1.2:
                return f"🟢 E가 {capacity_ratio:.1f}배 큰 규모", "#198754"
            elif capacity_ratio < 0.5:
                return f"🔴 E가 {1/capacity_ratio:.1f}배 소규모", "#dc3545"
            elif capacity_ratio < 0.8:
                return f"🟡 E가 작은 규모", "#ffc107"
            else:
                return "🟡 비슷한 규모", "#ffc107"
        
        def get_location_advantage():
            if location_same:
                return "🟡 동일 지역", "#ffc107"
            else:
                # 지역별 유리함 판단 (수도권 > 영남권 > 충청권 > 호남권 > 강원권 > 제주권)
                location_score = {
                    "수도권": 6, "영남권": 5, "충청권": 4, 
                    "호남권": 3, "강원권": 2, "제주권": 1
                }
                user_score = location_score.get(user_data['scenario'].location, 3)
                market_score = location_score.get(market_data['scenario'].location, 3)
                
                if user_score > market_score:
                    return "🟢 E가 유리한 지역", "#198754"
                elif user_score < market_score:
                    return "🔴 시나리오가 유리한 지역", "#dc3545"
                else:
                    return "🟡 비슷한 지역", "#ffc107"
        
        # 4. 최적 전략 비교
        user_best = "DR" if user_data['dr_roi'] > user_data['smp_roi'] else "SMP"
        market_best = "DR" if market_data['dr_roi'] > market_data['smp_roi'] else "SMP"
        strategy_match = user_best == market_best
        
        # 5. 종합 경쟁력 점수 계산
        if user_best == "DR":
            main_roi_diff = dr_roi_diff
            main_payback_diff = dr_payback_diff
        else:
            main_roi_diff = smp_roi_diff
            main_payback_diff = smp_payback_diff
        
        competitiveness_score = main_roi_diff + (main_payback_diff * 2)  # 회수기간이 중요
        
        if competitiveness_score > 5:
            comp_grade = "A+ 매우 우수"
            comp_color = "#198754"
            comp_icon = "🏆"
        elif competitiveness_score > 2:
            comp_grade = "A 우수"
            comp_color = "#20c997"
            comp_icon = "🥇"
        elif competitiveness_score > 0:
            comp_grade = "B 양호"
            comp_color = "#17a2b8"
            comp_icon = "🥈"
        elif competitiveness_score > -2:
            comp_grade = "C 보통"
            comp_color = "#ffc107"
            comp_icon = "🥉"
        elif competitiveness_score > -5:
            comp_grade = "D 미흡"
            comp_color = "#fd7e14"
            comp_icon = "⚠️"
        else:
            comp_grade = "F 매우 미흡"
            comp_color = "#dc3545"
            comp_icon = "❌"
        
        # 6. 구체적인 분석 의견
        def generate_analysis_opinion():
            opinions = []
            
            # 규모 분석
            if capacity_ratio > 1.5:
                opinions.append(f"대규모 사업으로 규모의 경제 효과를 기대할 수 있습니다.")
            elif capacity_ratio < 0.7:
                opinions.append(f"소규모 사업으로 초기 투자 부담은 적지만 수익 규모도 제한적입니다.")
            
            # ROI 분석
            if dr_roi_diff > 3:
                opinions.append(f"DR 사업에서 {dr_roi_diff:.1f}%p 높은 수익률을 보입니다.")
            elif smp_roi_diff > 3:
                opinions.append(f"SMP 사업에서 {smp_roi_diff:.1f}%p 높은 수익률을 보입니다.")
            
            # 활용률 분석
            if dr_util_diff > 10:
                opinions.append(f"DR 활용률이 {dr_util_diff:.0f}%p 높아 적극적인 운영 전략입니다.")
            elif smp_util_diff > 10:
                opinions.append(f"SMP 활용률이 {smp_util_diff:.0f}%p 높아 시장 참여도가 높습니다.")
            
            # 지역 분석
            if not location_same:
                opinions.append(f"지역 특성상 {user_data['scenario'].location}과 {market_data['scenario'].location}의 전력 시장 환경이 다릅니다.")
            
            return " ".join(opinions) if opinions else "전반적으로 시장 평균 수준의 조건입니다."
        
        # 개별 비교 결과 HTML 생성
        dr_advantage, dr_color = get_advantage_icon_text(dr_roi_diff)
        smp_advantage, smp_color = get_advantage_icon_text(smp_roi_diff)
        capacity_text, capacity_color = get_capacity_comparison()
        location_text, location_color = get_location_advantage()
        
        report += f"""
<div style="border: 2px solid {comp_color}; border-radius: 12px; margin-bottom: 2.5rem; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <div style="background: {comp_color}; color: white; padding: 1.5rem; position: relative;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h5 style="margin: 0; color: white; font-size: 1.4rem;">
                {comp_icon} 시나리오 {scenario_letter} vs 사용자(E) 상세 비교
            </h5>
            <div style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px;">
                <strong style="font-size: 1.1rem;">{comp_grade}</strong>
            </div>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.95rem; opacity: 0.9;">
            {market_data['scenario'].name.split('_')[1]} vs 사용자계획 | 경쟁력 점수: {competitiveness_score:+.1f}점
        </div>
    </div>
    
    <!-- 기본 조건 비교 -->
    <div style="padding: 1.5rem; background: #f8f9fa;">
        <h6 style="color: #495057; margin-bottom: 1rem; font-size: 1.2rem; border-bottom: 1px solid #dee2e6; padding-bottom: 0.5rem;">📋 기본 조건 비교</h6>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {location_color};">
                <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.3rem;">지역</div>
                <div style="font-weight: bold; margin-bottom: 0.3rem;">{market_data['scenario'].location} → {user_data['scenario'].location}</div>
                <div style="font-size: 0.9rem; color: {location_color};">{location_text}</div>
            </div>
            <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {capacity_color};">
                <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.3rem;">설비 용량</div>
                <div style="font-weight: bold; margin-bottom: 0.3rem;">{market_data['scenario'].capacity_kw:,.0f}kW → {user_data['scenario'].capacity_kw:,.0f}kW</div>
                <div style="font-size: 0.9rem; color: {capacity_color};">{capacity_text}</div>
            </div>
            <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.3rem;">DR 활용률</div>
                <div style="font-weight: bold; margin-bottom: 0.3rem;">{market_data['scenario'].utilization_dr*100:.0f}% → {user_data['scenario'].utilization_dr*100:.0f}%</div>
                <div style="font-size: 0.9rem; color: #17a2b8;">{dr_util_diff:+.0f}%p 차이</div>
            </div>
            <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #fd7e14;">
                <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.3rem;">SMP 활용률</div>
                <div style="font-weight: bold; margin-bottom: 0.3rem;">{market_data['scenario'].utilization_smp*100:.0f}% → {user_data['scenario'].utilization_smp*100:.0f}%</div>
                <div style="font-size: 0.9rem; color: #fd7e14;">{smp_util_diff:+.0f}%p 차이</div>
            </div>
        </div>
    </div>
    
    <!-- 수익성 비교 -->
    <div style="padding: 1.5rem;">
        <h6 style="color: #495057; margin-bottom: 1rem; font-size: 1.2rem; border-bottom: 1px solid #dee2e6; padding-bottom: 0.5rem;">💰 수익성 상세 비교</h6>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
            <!-- DR 비교 -->
            <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 10px; border: 1px solid #2196f3;">
                <h6 style="color: #1976d2; margin-bottom: 1rem; text-align: center;">🔵 국민DR 사업 비교</h6>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: 0.5rem 0; color: #666;">ROI (10년)</td>
                        <td style="text-align: right; font-weight: bold;">{market_data['dr_roi']:.1f}% → {user_data['dr_roi']:.1f}%</td>
                        <td style="text-align: right; color: {dr_color}; font-weight: bold;">{dr_advantage}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0; color: #666;">연간 수익</td>
                        <td style="text-align: right; font-weight: bold;">{market_data['dr_revenue']/100000000:.1f}억 → {user_data['dr_revenue']/100000000:.1f}억</td>
                        <td style="text-align: right; color: {dr_color}; font-weight: bold;">{dr_revenue_ratio:.1f}배</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0; color: #666;">회수기간</td>
                        <td style="text-align: right; font-weight: bold;">{market_data['dr_payback']:.1f}년 → {user_data['dr_payback']:.1f}년</td>
                        <td style="text-align: right; color: {'#198754' if dr_payback_diff > 0 else '#dc3545'}; font-weight: bold;">
                            {dr_payback_diff:+.1f}년
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- SMP 비교 -->
            <div style="background: #fff3e0; padding: 1.5rem; border-radius: 10px; border: 1px solid #ff9800;">
                <h6 style="color: #f57c00; margin-bottom: 1rem; text-align: center;">🟠 SMP 사업 비교</h6>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: 0.5rem 0; color: #666;">ROI (10년)</td>
                        <td style="text-align: right; font-weight: bold;">{market_data['smp_roi']:.1f}% → {user_data['smp_roi']:.1f}%</td>
                        <td style="text-align: right; color: {smp_color}; font-weight: bold;">{smp_advantage}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0; color: #666;">연간 수익</td>
                        <td style="text-align: right; font-weight: bold;">{market_data['smp_revenue']/100000000:.1f}억 → {user_data['smp_revenue']/100000000:.1f}억</td>
                        <td style="text-align: right; color: {smp_color}; font-weight: bold;">{smp_revenue_ratio:.1f}배</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0; color: #666;">회수기간</td>
                        <td style="text-align: right; font-weight: bold;">{market_data['smp_payback']:.1f}년 → {user_data['smp_payback']:.1f}년</td>
                        <td style="text-align: right; color: {'#198754' if smp_payback_diff > 0 else '#dc3545'}; font-weight: bold;">
                            {smp_payback_diff:+.1f}년
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        
        <!-- 전략 분석 -->
        <div style="background: {'#d4edda' if strategy_match else '#fff3cd'}; border: 1px solid {'#c3e6cb' if strategy_match else '#ffeaa7'}; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: {'#155724' if strategy_match else '#856404'};">최적 전략:</strong>
                    <span style="margin-left: 0.5rem;">시나리오 {scenario_letter}: {market_best} | 사용자 E: {user_best}</span>
                </div>
                <div style="color: {'#155724' if strategy_match else '#856404'}; font-weight: bold;">
                    {'✅ 전략 일치' if strategy_match else '⚠️ 전략 상이'}
                </div>
            </div>
        </div>
        
        <!-- 분석 의견 -->
        <div style="background: #f8f9fa; border-left: 4px solid {comp_color}; padding: 1rem; border-radius: 0 8px 8px 0;">
            <h6 style="color: {comp_color}; margin-bottom: 0.5rem;">📊 분석 의견</h6>
            <p style="margin: 0; line-height: 1.6; color: #495057;">{generate_analysis_opinion()}</p>
        </div>
    </div>
</div>
"""
        
        comparison_results.append({
            'scenario': scenario_letter,
            'competitiveness': competitiveness_score,
            'comp_grade': comp_grade,
            'strategy_match': strategy_match,
            'user_best': user_best,
            'comp_color': comp_color
        })
    
    # 최종 종합 평가
    avg_competitiveness = np.mean([r['competitiveness'] for r in comparison_results])
    strategy_matches = sum(1 for r in comparison_results if r['strategy_match'])
    
    user_dr_better = user_data['dr_roi'] > user_data['smp_roi']
    final_recommendation = "국민DR" if user_dr_better else "SMP"
    final_roi = user_data['dr_roi'] if user_dr_better else user_data['smp_roi']
    final_revenue = user_data['dr_revenue'] if user_dr_better else user_data['smp_revenue']
    final_payback = user_data['dr_payback'] if user_dr_better else user_data['smp_payback']
    
    # 시장 포지션 결정
    if avg_competitiveness > 3:
        market_position = "시장 최고급"
        position_color = "#198754"
        position_icon = "👑"
    elif avg_competitiveness > 1:
        market_position = "시장 선도급"
        position_color = "#20c997"
        position_icon = "🥇"
    elif avg_competitiveness > -1:
        market_position = "시장 평균급"
        position_color = "#ffc107"
        position_icon = "🥈"
    elif avg_competitiveness > -3:
        market_position = "시장 평균 이하"
        position_color = "#fd7e14"
        position_icon = "🥉"
    else:
        market_position = "시장 하위급"
        position_color = "#dc3545"
        position_icon = "⚠️"
    
    # 사업 타당성 결론
    if avg_competitiveness > 2 and final_roi > 12:
        conclusion = "높은 사업 타당성 - 적극 투자 추진 권장"
        conclusion_color = "#198754"
        conclusion_icon = "✅"
    elif avg_competitiveness > 0 and final_roi > 8:
        conclusion = "양호한 사업 타당성 - 투자 추진 권장"
        conclusion_color = "#20c997"
        conclusion_icon = "👍"
    elif avg_competitiveness > -1 and final_roi > 5:
        conclusion = "보통 사업 타당성 - 신중한 검토 필요"
        conclusion_color = "#ffc107"
        conclusion_icon = "🤔"
    elif avg_competitiveness > -2 and final_roi > 2:
        conclusion = "제한적 사업 타당성 - 조건 개선 후 검토"
        conclusion_color = "#fd7e14"
        conclusion_icon = "⚠️"
    else:
        conclusion = "낮은 사업 타당성 - 계획 재검토 필요"
        conclusion_color = "#dc3545"
        conclusion_icon = "❌"
    
    # 구체적 개선 제안
    improvement_suggestions = []
    if user_data['dr_roi'] < 10 and user_data['smp_roi'] < 10:
        improvement_suggestions.append("활용률을 높여 수익성을 개선하세요.")
    if user_scenario.capacity_kw < 1000:
        improvement_suggestions.append("규모의 경제를 위해 설비 용량 확대를 검토하세요.")
    if user_location in ["강원권", "제주권"]:
        improvement_suggestions.append("유리한 지역으로의 사업 지역 변경을 고려하세요.")
    if not any(r['strategy_match'] for r in comparison_results):
        improvement_suggestions.append("시장 트렌드에 맞는 사업 전략 조정이 필요합니다.")
    
    if not improvement_suggestions:
        improvement_suggestions.append("현재 조건이 양호하므로 계획대로 추진하세요.")
    
    report += f"""
<div style="border: 3px solid {conclusion_color}; border-radius: 15px; margin-top: 3rem; overflow: hidden; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">
    <div style="background: {conclusion_color}; color: white; padding: 2rem; text-align: center;">
        <h3 style="margin: 0; color: white; font-size: 1.8rem;">{conclusion_icon} 최종 종합 평가 결과</h3>
    </div>
    
    <div style="padding: 2rem;">
        <!-- 핵심 지표 요약 -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
            <div style="background: {position_color}15; border: 2px solid {position_color}; padding: 1.5rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{position_icon}</div>
                <div style="font-size: 1.3rem; font-weight: bold; color: {position_color}; margin-bottom: 0.5rem;">{market_position}</div>
                <div style="font-size: 0.9rem; color: #6c757d;">평균 경쟁력: {avg_competitiveness:+.1f}점</div>
            </div>
            
            <div style="background: #0d6efd15; border: 2px solid #0d6efd; padding: 1.5rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="font-size: 1.3rem; font-weight: bold; color: #0d6efd; margin-bottom: 0.5rem;">전략 일치도</div>
                <div style="font-size: 1.1rem; color: #495057;">{strategy_matches}/4 시나리오</div>
            </div>
            
            <div style="background: #19875415; border: 2px solid #198754; padding: 1.5rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💰</div>
                <div style="font-size: 1.3rem; font-weight: bold; color: #198754; margin-bottom: 0.5rem;">추천 사업</div>
                <div style="font-size: 1.1rem; color: #495057;">{final_recommendation}</div>
            </div>
            
            <div style="background: #20c99715; border: 2px solid #20c997; padding: 1.5rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
                <div style="font-size: 1.3rem; font-weight: bold; color: #20c997; margin-bottom: 0.5rem;">예상 ROI</div>
                <div style="font-size: 1.1rem; color: #495057;">{final_roi:.1f}%</div>
            </div>
        </div>
        
        <!-- 상세 수치 -->
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <h6 style="color: #495057; margin-bottom: 1rem;">📊 {final_recommendation} 사업 상세 예상 수치</h6>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; font-size: 1rem;">
                <div><strong>예상 연간수익:</strong> {final_revenue/100000000:.1f}억원</div>
                <div><strong>투자회수기간:</strong> {final_payback:.1f}년</div>
                <div><strong>10년 ROI:</strong> {final_roi:.1f}%</div>
                <div><strong>월평균 수익:</strong> {final_revenue/12/10000:.0f}만원</div>
            </div>
        </div>
        
        <!-- 최종 결론 -->
        <div style="background: {conclusion_color}15; border: 2px solid {conclusion_color}; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; text-align: center;">
            <h5 style="color: {conclusion_color}; margin-bottom: 1rem; font-size: 1.4rem;">
                {conclusion_icon} {conclusion}
            </h5>
            <p style="margin: 0; color: #495057; font-size: 1.1rem; line-height: 1.6;">
                현재 조건에서는 <strong style="color: {conclusion_color};">{final_recommendation} 사업</strong>을 추천하며,
                시장 대비 <strong style="color: {position_color};">{market_position}</strong> 수준의 경쟁력을 보입니다.
            </p>
        </div>
        
        <!-- 개선 제안 -->
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1.5rem;">
            <h6 style="color: #856404; margin-bottom: 1rem;">💡 개선 제안 사항</h6>
            <ul style="margin: 0; color: #856404; line-height: 1.8;">
"""
    
    for suggestion in improvement_suggestions:
        report += f"                <li>{suggestion}</li>\n"
    
    report += """
            </ul>
        </div>
    </div>
</div>

</div>
"""
    
    return report

# 기존 종합 분석 함수 (호환성 유지)
def run_comprehensive_analysis(web_scenarios=None):
    """기존 호환성을 위한 래퍼 함수"""
    if web_scenarios:
        # 웹에서 시나리오가 제공된 경우 기존 방식 사용
        analyzer = AdvancedV2GAnalyzer()
        scenarios = web_scenarios
    else:
        # 기본값으로 시장 벤치마킹 분석 실행
        return run_market_benchmarking_analysis()

# 웹 인터페이스용 함수
def create_scenario_from_web_input(name, capacity, location, budget, target_roi, risk_tolerance, 
                                 dr_utilization=0.7, smp_utilization=0.6):
    """웹 입력으로부터 시나리오 객체 생성"""
    return BusinessScenario(
        name=name,
        capacity_kw=float(capacity),
        location=location,
        investment_budget=float(budget),
        target_roi=float(target_roi),
        risk_tolerance=risk_tolerance,
        utilization_dr=float(dr_utilization),
        utilization_smp=float(smp_utilization)
    )

def run_web_based_analysis(web_scenarios_data):
    """웹 기반 분석 실행"""
    # 웹 데이터를 시나리오 객체로 변환
    scenarios = []
    for data in web_scenarios_data:
        scenario = create_scenario_from_web_input(
            data.get('name', '웹시나리오'),
            data.get('capacity', 1000),
            data.get('location', '수도권'),
            data.get('budget', 1000000000),
            data.get('target_roi', 15.0),
            data.get('risk_tolerance', 'medium'),
            data.get('dr_utilization', 0.7),
            data.get('smp_utilization', 0.6)
        )
        scenarios.append(scenario)
    
    # 웹 시나리오로 종합 분석 실행
    return run_comprehensive_analysis(scenarios)

if __name__ == "__main__":
    # 시장 벤치마킹 분석 실행 (예시)
    benchmarking_results = run_market_benchmarking_analysis(
        user_capacity=1500, 
        user_location="수도권", 
        user_dr_util=0.8, 
        user_smp_util=0.7
    )
    print(benchmarking_results)
