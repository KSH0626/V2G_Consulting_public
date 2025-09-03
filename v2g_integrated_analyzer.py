import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# 기존 모듈 import
from v2g_business_analyzer import V2GBusinessAnalyzer, V2GBusinessConsultant
from advances_analysis import AdvancedV2GAnalyzer, BusinessScenario
from v2g_score_analyzer import V2GScoreAnalyzer, V2GScoreInput

class V2GIntegratedAnalyzer:
    """기존 분석과 점수화 시스템을 통합한 분석기"""
    
    def __init__(self):
        self.business_analyzer = V2GBusinessAnalyzer()
        self.consultant = V2GBusinessConsultant()
        self.advanced_analyzer = AdvancedV2GAnalyzer()
        self.score_analyzer = V2GScoreAnalyzer()
    
    def run_integrated_analysis(self, basic_inputs: Dict, score_inputs: Dict) -> Dict:
        """통합 분석 실행 - 기존 분석 + 점수화 분석"""
        
        # 1. 기존 수익성 분석
        revenue_analysis, fig, report = self.consultant.run_consultation(
            capacity_kw=basic_inputs['capacity'],
            location=basic_inputs['location'],
            utilization_dr=basic_inputs['utilization_dr'],
            utilization_smp=basic_inputs['utilization_smp']
        )
        
        # 2. 점수화 분석
        score_input = V2GScoreInput(
            capacity_kw=score_inputs['capacity_kw'],
            location=score_inputs['location'],
            budget_billion=score_inputs['budget_billion'],
            risk_preference=score_inputs['risk_preference'],
            regular_pattern_ratio=score_inputs['regular_pattern_ratio'],
            dr_dispatch_time_ratio=score_inputs['dr_dispatch_time_ratio'],
            charging_spots=score_inputs['charging_spots'],
            power_capacity_mva=score_inputs['power_capacity_mva'],
            total_ports=score_inputs['total_ports'],
            smart_ocpp_ports=score_inputs['smart_ocpp_ports'],
            v2g_ports=score_inputs['v2g_ports'],
            brand_type=score_inputs['brand_type'],
            soh_under_70_ratio=score_inputs['soh_under_70_ratio'],
            soh_70_85_ratio=score_inputs['soh_70_85_ratio'],
            soh_85_95_ratio=score_inputs['soh_85_95_ratio'],
            soh_over_95_ratio=score_inputs['soh_over_95_ratio']
        )
        
        score_result = self.score_analyzer.calculate_comprehensive_score(score_input)
        
        # 3. 통합 비교 분석
        integrated_comparison = self._create_integrated_comparison(
            revenue_analysis, score_result, basic_inputs, score_inputs
        )
        
        # 4. 통합 시각화
        integrated_chart = self._create_integrated_visualization(
            revenue_analysis, score_result
        )
        
        # 5. 통합 리포트
        integrated_report = self._generate_integrated_report(
            revenue_analysis, score_result, integrated_comparison
        )
        
        return {
            'revenue_analysis': revenue_analysis,
            'score_analysis': score_result,
            'integrated_comparison': integrated_comparison,
            'integrated_chart': integrated_chart,
            'integrated_report': integrated_report,
            'revenue_chart': fig,
            'score_chart': self.score_analyzer.create_score_visualization(score_result)
        }
    
    def _create_integrated_comparison(self, revenue_analysis: Dict, 
                                    score_result: Dict, basic_inputs: Dict, 
                                    score_inputs: Dict) -> Dict:
        """통합 비교 분석"""
        
        # 수익성 기준 추천
        dr_roi = revenue_analysis['DR']['roi_metrics']['roi']
        smp_roi = revenue_analysis['SMP']['roi_metrics']['roi']
        revenue_recommendation = 'DR' if dr_roi > smp_roi else 'SMP'
        
        # 점수 기준 추천
        score_recommendation = score_result['recommendation']
        
        # 일치도 분석
        recommendations_match = revenue_recommendation == score_recommendation
        
        # 가중 종합 점수 계산 (수익성 60% + 종합점수 40%)
        dr_weighted_score = (dr_roi * 0.6) + (score_result['total_scores']['dr'] * 0.4)
        smp_weighted_score = (smp_roi * 0.6) + (score_result['total_scores']['smp'] * 0.4)
        
        final_recommendation = 'DR' if dr_weighted_score > smp_weighted_score else 'SMP'
        
        # 신뢰도 계산
        roi_gap = abs(dr_roi - smp_roi)
        score_gap = score_result['score_gap']
        weighted_gap = abs(dr_weighted_score - smp_weighted_score)
        
        if weighted_gap > 15:
            confidence = "매우 높음"
        elif weighted_gap > 10:
            confidence = "높음"
        elif weighted_gap > 5:
            confidence = "보통"
        else:
            confidence = "낮음"
        
        return {
            'revenue_recommendation': revenue_recommendation,
            'score_recommendation': score_recommendation,
            'final_recommendation': final_recommendation,
            'recommendations_match': recommendations_match,
            'confidence': confidence,
            'metrics': {
                'dr_roi': dr_roi,
                'smp_roi': smp_roi,
                'dr_score': score_result['total_scores']['dr'],
                'smp_score': score_result['total_scores']['smp'],
                'dr_weighted': dr_weighted_score,
                'smp_weighted': smp_weighted_score,
                'roi_gap': roi_gap,
                'score_gap': score_gap,
                'weighted_gap': weighted_gap
            }
        }
    
    def _create_integrated_visualization(self, revenue_analysis: Dict, 
                                       score_result: Dict) -> go.Figure:
        """통합 시각화 차트 생성"""
        
        # 서브플롯 생성 (2x2)
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '수익성 비교 (ROI %)', '종합 점수 비교 (100점 만점)',
                '항목별 상세 점수', '투자 회수 분석'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "scatter"}]
            ]
        )
        
        # 1. 수익성 비교
        dr_roi = revenue_analysis['DR']['roi_metrics']['roi']
        smp_roi = revenue_analysis['SMP']['roi_metrics']['roi']
        
        fig.add_trace(
            go.Bar(
                x=['국민DR', 'SMP'],
                y=[dr_roi, smp_roi],
                name='ROI (%)',
                marker_color=['#1f77b4', '#ff7f0e'],
                text=[f'{dr_roi:.1f}%', f'{smp_roi:.1f}%'],
                textposition='auto',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # 2. 종합 점수 비교
        dr_score = score_result['total_scores']['dr']
        smp_score = score_result['total_scores']['smp']
        
        fig.add_trace(
            go.Bar(
                x=['국민DR', 'SMP'],
                y=[dr_score, smp_score],
                name='종합 점수',
                marker_color=['#1f77b4', '#ff7f0e'],
                text=[f'{dr_score:.1f}점', f'{smp_score:.1f}점'],
                textposition='auto',
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. 항목별 상세 점수
        categories = ['지역', '규모', '리스크', '주차', '인프라', '충전기', '브랜드', '배터리', '예산']
        dr_detailed = []
        smp_detailed = []
        
        for key in ['region', 'scale', 'risk', 'parking', 'infrastructure', 
                   'charger', 'brand', 'battery', 'budget']:
            dr_detailed.append(score_result['detailed_scores'][key]['dr'])
            smp_detailed.append(score_result['detailed_scores'][key]['smp'])
        
        fig.add_trace(
            go.Bar(
                x=categories,
                y=dr_detailed,
                name='DR 세부점수',
                marker_color='#1f77b4',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=categories,
                y=smp_detailed,
                name='SMP 세부점수',
                marker_color='#ff7f0e',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # 4. 투자 회수 분석
        years = list(range(1, 11))
        dr_annual_net = revenue_analysis['DR']['roi_metrics']['annual_net_income']
        smp_annual_net = revenue_analysis['SMP']['roi_metrics']['annual_net_income']
        dr_investment = revenue_analysis['DR']['costs']['total_investment']
        smp_investment = revenue_analysis['SMP']['costs']['total_investment']
        
        dr_cumulative = []
        smp_cumulative = []
        dr_cum = -dr_investment
        smp_cum = -smp_investment
        
        for year in years:
            dr_cum += dr_annual_net
            smp_cum += smp_annual_net
            dr_cumulative.append(dr_cum)
            smp_cumulative.append(smp_cum)
        
        fig.add_trace(
            go.Scatter(
                x=years,
                y=dr_cumulative,
                mode='lines+markers',
                name='DR 누적수익',
                line=dict(color='#1f77b4', width=3)
            ),
            row=2, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=years,
                y=smp_cumulative,
                mode='lines+markers',
                name='SMP 누적수익',
                line=dict(color='#ff7f0e', width=3)
            ),
            row=2, col=2
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=2)
        
        # 레이아웃 업데이트
        fig.update_layout(
            title={
                'text': "V2G 사업 통합 분석 대시보드",
                'x': 0.5,
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            height=800,
            showlegend=True,
            font=dict(family="Arial, sans-serif", size=11)
        )
        
        # 축 레이블 설정
        fig.update_xaxes(title_text="사업 유형", row=1, col=1)
        fig.update_yaxes(title_text="ROI (%)", row=1, col=1)
        fig.update_xaxes(title_text="사업 유형", row=1, col=2)
        fig.update_yaxes(title_text="점수", row=1, col=2)
        fig.update_xaxes(title_text="평가 항목", row=2, col=1)
        fig.update_yaxes(title_text="점수", row=2, col=1)
        fig.update_xaxes(title_text="년도", row=2, col=2)
        fig.update_yaxes(title_text="누적 손익 (원)", row=2, col=2)
        
        return fig
    
    def _generate_integrated_report(self, revenue_analysis: Dict, 
                                  score_result: Dict, 
                                  integrated_comparison: Dict) -> str:
        """통합 분석 리포트 생성"""
        
        metrics = integrated_comparison['metrics']
        final_rec = integrated_comparison['final_recommendation']
        confidence = integrated_comparison['confidence']
        match = integrated_comparison['recommendations_match']
        
        # 색상 설정
        final_color = "#1f77b4" if final_rec == 'DR' else "#ff7f0e"
        final_name = "국민DR" if final_rec == 'DR' else "SMP"
        
        report = f"""
        <div style="font-family: 'Noto Sans KR', Arial, sans-serif; line-height: 1.6;">
        
        <h3 style="text-align: center; color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 1rem; margin-bottom: 2rem;">
            🔗 V2G 사업 통합 분석 결과
        </h3>
        
        <!-- 최종 추천 결과 -->
        <div style="background: linear-gradient(135deg, {final_color}, {final_color}dd); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
            <h4 style="color: white; margin-bottom: 1rem; font-size: 1.6rem;">🏆 최종 추천 사업</h4>
            <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem;">{final_name}</div>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">신뢰도: <strong>{confidence}</strong></div>
                <div style="font-size: 1rem;">
                    {'✅ 수익성과 종합점수 모두 일치' if match else '⚠️ 수익성과 종합점수 불일치 - 종합 판단 적용'}
                </div>
            </div>
        </div>
        
        <!-- 비교 분석 요약 -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
            <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 12px; padding: 1.5rem;">
                <h5 style="color: #1976d2; margin-bottom: 1rem; text-align: center;">💰 수익성 분석</h5>
                <div style="text-align: center;">
                    <div style="margin-bottom: 0.5rem;">
                        <strong>DR ROI:</strong> {metrics['dr_roi']:.1f}%
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong>SMP ROI:</strong> {metrics['smp_roi']:.1f}%
                    </div>
                    <div style="font-weight: bold; color: {'#1976d2' if integrated_comparison['revenue_recommendation'] == 'DR' else '#f57c00'};">
                        추천: {integrated_comparison['revenue_recommendation']}
                    </div>
                </div>
            </div>
            
            <div style="background: #fff3e0; border: 2px solid #ff9800; border-radius: 12px; padding: 1.5rem;">
                <h5 style="color: #f57c00; margin-bottom: 1rem; text-align: center;">🎯 종합 점수</h5>
                <div style="text-align: center;">
                    <div style="margin-bottom: 0.5rem;">
                        <strong>DR 점수:</strong> {metrics['dr_score']:.1f}점
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong>SMP 점수:</strong> {metrics['smp_score']:.1f}점
                    </div>
                    <div style="font-weight: bold; color: {'#1976d2' if integrated_comparison['score_recommendation'] == 'DR' else '#f57c00'};">
                        추천: {integrated_comparison['score_recommendation']}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 가중 종합 점수 -->
        <div style="background: #f8f9fa; border: 2px solid #6c757d; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
            <h5 style="color: #495057; margin-bottom: 1rem; text-align: center;">⚖️ 가중 종합 점수 (수익성 60% + 종합점수 40%)</h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; text-align: center;">
                <div>
                    <div style="font-size: 1.1rem; color: #1f77b4; font-weight: bold;">국민DR</div>
                    <div style="font-size: 1.3rem; font-weight: bold;">{metrics['dr_weighted']:.1f}점</div>
                </div>
                <div style="display: flex; align-items: center; justify-content: center;">
                    <div style="font-size: 1.2rem; font-weight: bold;">VS</div>
                </div>
                <div>
                    <div style="font-size: 1.1rem; color: #ff7f0e; font-weight: bold;">SMP</div>
                    <div style="font-size: 1.3rem; font-weight: bold;">{metrics['smp_weighted']:.1f}점</div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #dee2e6;">
                <strong>점수 차이: {metrics['weighted_gap']:.1f}점</strong>
            </div>
        </div>
        
        <!-- 상세 수익성 정보 -->
        <h4 style="color: #495057; margin: 2rem 0 1rem 0; border-bottom: 2px solid #dee2e6; padding-bottom: 0.5rem;">
            📊 상세 수익성 분석
        </h4>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
            <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 1rem;">
                <h6 style="color: #1f77b4; margin-bottom: 1rem;">🔵 국민DR 사업</h6>
                <ul style="margin: 0; padding-left: 1.2rem;">
                    <li>연간 수익: {revenue_analysis['DR']['revenue']['annual_revenue']:,}원</li>
                    <li>총 투자비: {revenue_analysis['DR']['costs']['total_investment']:,}원</li>
                    <li>연간 순이익: {revenue_analysis['DR']['roi_metrics']['annual_net_income']:,}원</li>
                    <li>투자회수기간: {revenue_analysis['DR']['roi_metrics']['payback_period']:.1f}년</li>
                    <li>NPV: {revenue_analysis['DR']['roi_metrics']['npv']:,}원</li>
                </ul>
            </div>
            
            <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 1rem;">
                <h6 style="color: #ff7f0e; margin-bottom: 1rem;">🟠 SMP 사업</h6>
                <ul style="margin: 0; padding-left: 1.2rem;">
                    <li>연간 수익: {revenue_analysis['SMP']['revenue']['annual_revenue']:,}원</li>
                    <li>총 투자비: {revenue_analysis['SMP']['costs']['total_investment']:,}원</li>
                    <li>연간 순이익: {revenue_analysis['SMP']['roi_metrics']['annual_net_income']:,}원</li>
                    <li>투자회수기간: {revenue_analysis['SMP']['roi_metrics']['payback_period']:.1f}년</li>
                    <li>NPV: {revenue_analysis['SMP']['roi_metrics']['npv']:,}원</li>
                </ul>
            </div>
        </div>
        
        <!-- 종합 평가 의견 -->
        <div style="background: #e8f5e8; border: 2px solid #4caf50; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
            <h5 style="color: #2e7d32; margin-bottom: 1rem;">💡 종합 평가 의견</h5>
            <p style="margin-bottom: 1rem; line-height: 1.7; color: #2e7d32;">
                <strong>통합 분석 결과</strong>, 수익성과 종합 적합성을 모두 고려할 때 
                <strong style="color: {final_color};">{final_name}</strong> 사업이 현재 조건에 가장 적합합니다.
            </p>
            
            {'<p style="margin-bottom: 1rem; line-height: 1.7; color: #2e7d32;"><strong>✅ 일치성 확인:</strong> 수익성 분석과 종합 점수 분석 모두 동일한 결과를 보여 신뢰도가 높습니다.</p>' if match else '<p style="margin-bottom: 1rem; line-height: 1.7; color: #2e7d32;"><strong>⚠️ 불일치 해석:</strong> 수익성과 종합 점수가 다른 결과를 보이므로, 가중 평균을 통한 종합 판단을 적용했습니다.</p>'}
            
            <p style="margin: 0; line-height: 1.7; color: #2e7d32;">
                <strong>신뢰도 "{confidence}"</strong>는 분석 결과의 명확성을 나타내며, 
                최종 의사결정 시 참고하시기 바랍니다.
            </p>
        </div>
        
        <!-- 추가 고려사항 -->
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1.5rem;">
            <h6 style="color: #856404; margin-bottom: 1rem;">🔍 추가 고려사항</h6>
            <ul style="margin: 0; color: #856404; line-height: 1.8;">
                <li>본 분석은 현재 시점의 조건을 기준으로 하며, 시장 상황 변화에 따라 결과가 달라질 수 있습니다.</li>
                <li>종합 점수는 정성적 요소를 포함하므로, 실제 사업 환경과 차이가 있을 수 있습니다.</li>
                <li>최종 투자 결정 시에는 추가적인 시장 조사와 전문가 자문을 권장합니다.</li>
            </ul>
        </div>
        
        </div>
        """
        
        return report

# 웹 인터페이스와 연동하는 래퍼 함수들
def run_score_analysis_from_web(score_inputs: Dict) -> Dict:
    """웹에서 점수 분석만 실행하는 함수"""
    analyzer = V2GScoreAnalyzer()
    
    score_input = V2GScoreInput(**score_inputs)
    result = analyzer.calculate_comprehensive_score(score_input)
    
    # 웹 응답용 데이터 구성
    return {
        'success': True,
        'result': result,
        'chart_json': analyzer.create_score_visualization(result).to_json(),
        'report': analyzer.generate_score_report(result)
    }

def run_integrated_analysis_from_web(basic_inputs: Dict, score_inputs: Dict) -> Dict:
    """웹에서 통합 분석을 실행하는 함수"""
    analyzer = V2GIntegratedAnalyzer()
    
    try:
        result = analyzer.run_integrated_analysis(basic_inputs, score_inputs)
        
        return {
            'success': True,
            'result': result,
            'integrated_chart_json': result['integrated_chart'].to_json(),
            'revenue_chart_json': result['revenue_chart'].to_json(),
            'score_chart_json': result['score_chart'].to_json(),
            'integrated_report': result['integrated_report']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# 테스트 함수
if __name__ == "__main__":
    # 테스트용 데이터
    basic_inputs = {
        'capacity': 1000,
        'location': '수도권',
        'utilization_dr': 0.7,
        'utilization_smp': 0.6
    }
    
    score_inputs = {
        'capacity_kw': 1000,
        'location': '수도권',
        'budget_billion': 15,
        'risk_preference': 'neutral',
        'regular_pattern_ratio': 0.7,
        'dr_dispatch_time_ratio': 0.6,
        'charging_spots': 50,
        'power_capacity_mva': 0.3,
        'total_ports': 100,
        'smart_ocpp_ports': 60,
        'v2g_ports': 30,
        'brand_type': 'others',
        'soh_under_70_ratio': 0.1,
        'soh_70_85_ratio': 0.3,
        'soh_85_95_ratio': 0.5,
        'soh_over_95_ratio': 0.1
    }
    
    # 통합 분석 실행
    analyzer = V2GIntegratedAnalyzer()
    result = analyzer.run_integrated_analysis(basic_inputs, score_inputs)
    
    # 결과 저장
    result['integrated_chart'].write_html("integrated_analysis.html")
    print("🔗 통합 분석 차트가 'integrated_analysis.html'로 저장되었습니다.")
    
    with open("integrated_report.html", "w", encoding="utf-8") as f:
        f.write(result['integrated_report'])
    print("📄 통합 리포트가 'integrated_report.html'로 저장되었습니다.")