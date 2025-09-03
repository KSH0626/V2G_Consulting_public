import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

@dataclass
class V2GScoreInput:
    """V2G 종합 점수 분석을 위한 입력 데이터 클래스"""
    # 기본 정보
    capacity_kw: float
    location: str
    budget_billion: float  # 억원 단위
    
    # 리스크 선호도
    risk_preference: str  # 'stable', 'neutral', 'high_risk'
    
    # 주차 패턴
    regular_pattern_ratio: float  # 일정 패턴 비율 (0~1)
    dr_dispatch_time_ratio: float  # DR 발령시간 비율 (0~1)
    
    # 부지 및 인프라
    charging_spots: int  # 충전부지 면수
    power_capacity_mva: float  # 수전용량 (MVA)
    
    # 충전기 비율
    total_ports: int  # 전체 포트수
    smart_ocpp_ports: int  # 스마트 및 OCPP 포트수
    v2g_ports: int  # V2G 포트수
    
    # 브랜드 신뢰성
    brand_type: str  # 'b2g_large', 'others'
    
    # 배터리 SOH 분포
    soh_under_70_ratio: float  # SOH 70% 이하 비율
    soh_70_85_ratio: float  # SOH 70-85% 비율
    soh_85_95_ratio: float  # SOH 85-95% 비율
    soh_over_95_ratio: float  # SOH 95% 초과 비율

class V2GScoreAnalyzer:
    """V2G 사업 종합 점수화 분석기"""
    
    def __init__(self):
        # 지역별 우위도 매핑
        self.dr_preferred_regions = [
            '수도권', '세종', '광주', '대전', '대구', '강원권'
        ]
        self.smp_preferred_regions = [
            '인천', '부산', '울산', '경상권', '충청권', '전라권', '제주권'
        ]
        
        # 영남권, 호남권을 포함한 매핑
        self.region_mapping = {
            '영남권': '경상권',
            '호남권': '전라권'
        }
    
    def calculate_region_score(self, location: str) -> Tuple[int, int]:
        """지역 차별화 점수 계산 [20점]"""
        # 지역명 매핑
        mapped_location = self.region_mapping.get(location, location)
        
        if location in self.dr_preferred_regions or mapped_location in self.dr_preferred_regions:
            return 20, 10  # DR 우위 지역
        elif location in self.smp_preferred_regions or mapped_location in self.smp_preferred_regions:
            return 10, 20  # SMP 우위 지역
        else:
            # 매핑되지 않은 지역은 중립으로 처리
            return 15, 15
    
    def calculate_scale_score(self, capacity_kw: float) -> Tuple[int, int]:
        """업체 규모 점수 계산 [25점]"""
        if capacity_kw <= 3000:
            return 25, 4
        elif 3000 < capacity_kw <= 8000:
            return 17, 13
        elif 8000 < capacity_kw <= 15000:  # 1.5MW = 15000kW
            return 11, 19
        else:  # > 1.5MW
            return 6, 25
    
    def calculate_risk_score(self, risk_preference: str) -> Tuple[int, int]:
        """리스크 선호도 점수 계산 [12점]"""
        risk_scores = {
            'stable': (12, 0),
            'neutral': (6, 6),
            'high_risk': (0, 12)
        }
        return risk_scores.get(risk_preference, (6, 6))  # 기본값: 중립
    
    def calculate_parking_pattern_score(self, regular_pattern_ratio: float, 
                                      dr_dispatch_time_ratio: float) -> Tuple[float, float]:
        """주차 패턴 점수 계산 [16점]"""
        # DR 발령시간에 따른 가중치 결정
        if dr_dispatch_time_ratio > 0.5:
            dr_weight, smp_weight = 0.8, 0.2
        elif 0.25 <= dr_dispatch_time_ratio <= 0.5:
            dr_weight, smp_weight = 0.5, 0.5
        else:  # < 0.25
            dr_weight, smp_weight = 0.2, 0.8
        
        # 일정 패턴과 유동적 패턴 모두 동일한 가중치 적용
        total_points = 16
        dr_score = total_points * dr_weight
        smp_score = total_points * smp_weight
        
        return dr_score, smp_score
    
    def calculate_infrastructure_score(self, charging_spots: int, 
                                     power_capacity_mva: float) -> Tuple[int, int]:
        """부지 및 인프라 점수 계산 [5점]"""
        # AND 조건으로 매칭
        if charging_spots > 200 and power_capacity_mva > 1.0:
            return 1, 5
        elif 120 < charging_spots <= 200 and 0.6 < power_capacity_mva <= 1.0:
            return 2, 4
        elif 80 < charging_spots <= 120 and 0.4 < power_capacity_mva <= 0.6:
            return 3, 3
        elif 40 < charging_spots <= 80 and 0.2 < power_capacity_mva <= 0.4:
            return 4, 2
        elif charging_spots <= 40 and power_capacity_mva <= 0.2:
            return 5, 1
        else:
            # 조건이 맞지 않는 경우 중간값
            return 3, 3
    
    def calculate_charger_ratio_score(self, total_ports: int, smart_ocpp_ports: int, 
                                    v2g_ports: int) -> Tuple[int, int]:
        """충전기 비율 점수 계산 [5점]"""
        # DR 비율 계산 (스마트 및 OCPP)
        r_dr = smart_ocpp_ports / total_ports if total_ports > 0 else 0
        
        # SMP 비율 계산 (V2G)
        r_smp = v2g_ports / total_ports if total_ports > 0 else 0
        
        def get_ratio_score(ratio: float) -> int:
            if ratio > 0.6:
                return 5
            elif 0.4 < ratio <= 0.6:
                return 4
            elif 0.3 < ratio <= 0.4:
                return 3
            elif 0.2 < ratio <= 0.3:
                return 2
            else:  # <= 0.2
                return 1
        
        dr_score = get_ratio_score(r_dr)
        smp_score = get_ratio_score(r_smp)
        
        return dr_score, smp_score
    
    def calculate_brand_score(self, brand_type: str) -> Tuple[int, int]:
        """브랜드 신뢰성 점수 계산 [3점]"""
        if brand_type == 'b2g_large':  # B2G 및 대기업
            return 3, 0
        else:  # 그외
            return 1, 3
    
    def calculate_battery_degradation_score(self, soh_under_70: float, soh_70_85: float, 
                                          soh_85_95: float, soh_over_95: float) -> Tuple[int, int]:
        """배터리 열화 부담 점수 계산 [14점]"""
        # 비율 합계 검증 및 정규화
        total_ratio = soh_under_70 + soh_70_85 + soh_85_95 + soh_over_95
        if total_ratio > 0:
            soh_under_70 /= total_ratio
            soh_70_85 /= total_ratio
            soh_85_95 /= total_ratio
            soh_over_95 /= total_ratio
        
        # 평균 SOH 계산
        avg_soh = (soh_under_70 * 0.7 + 
                   soh_70_85 * 0.775 + 
                   soh_85_95 * 0.9 + 
                   soh_over_95 * 0.975)
        
        # 점수 부여
        dr_score = 14  # DR은 항상 만점
        
        if avg_soh > 0.95:
            smp_score = 14
        elif 0.85 < avg_soh <= 0.95:
            smp_score = 10
        elif 0.70 < avg_soh <= 0.85:
            smp_score = 5
        else:  # <= 0.70
            smp_score = 0
        
        return dr_score, smp_score
    
    def calculate_budget_score(self, budget_billion: float) -> Tuple[int, int]:
        """예산 점수 계산 [10점]"""
        if budget_billion < 10:
            return 10, 0
        elif 10 <= budget_billion < 30:
            return 8, 2
        elif 30 <= budget_billion < 80:
            return 6, 4
        elif 80 <= budget_billion < 150:
            return 5, 5
        elif 150 <= budget_billion < 300:
            return 4, 6
        elif 300 <= budget_billion < 500:
            return 2, 8
        else:  # >= 500
            return 0, 10
    
    def calculate_comprehensive_score(self, input_data: V2GScoreInput) -> Dict:
        """종합 점수 계산"""
        # 각 항목별 점수 계산
        region_dr, region_smp = self.calculate_region_score(input_data.location)
        scale_dr, scale_smp = self.calculate_scale_score(input_data.capacity_kw)
        risk_dr, risk_smp = self.calculate_risk_score(input_data.risk_preference)
        parking_dr, parking_smp = self.calculate_parking_pattern_score(
            input_data.regular_pattern_ratio, input_data.dr_dispatch_time_ratio)
        infra_dr, infra_smp = self.calculate_infrastructure_score(
            input_data.charging_spots, input_data.power_capacity_mva)
        charger_dr, charger_smp = self.calculate_charger_ratio_score(
            input_data.total_ports, input_data.smart_ocpp_ports, input_data.v2g_ports)
        brand_dr, brand_smp = self.calculate_brand_score(input_data.brand_type)
        battery_dr, battery_smp = self.calculate_battery_degradation_score(
            input_data.soh_under_70_ratio, input_data.soh_70_85_ratio,
            input_data.soh_85_95_ratio, input_data.soh_over_95_ratio)
        budget_dr, budget_smp = self.calculate_budget_score(input_data.budget_billion)
        
        # 세부 점수 딕셔너리
        detailed_scores = {
            'region': {'dr': region_dr, 'smp': region_smp, 'max': 20},
            'scale': {'dr': scale_dr, 'smp': scale_smp, 'max': 25},
            'risk': {'dr': risk_dr, 'smp': risk_smp, 'max': 12},
            'parking': {'dr': parking_dr, 'smp': parking_smp, 'max': 16},
            'infrastructure': {'dr': infra_dr, 'smp': infra_smp, 'max': 5},
            'charger': {'dr': charger_dr, 'smp': charger_smp, 'max': 5},
            'brand': {'dr': brand_dr, 'smp': brand_smp, 'max': 3},
            'battery': {'dr': battery_dr, 'smp': battery_smp, 'max': 14},
            'budget': {'dr': budget_dr, 'smp': budget_smp, 'max': 10}
        }
        
        # 총점 계산
        total_dr = sum(scores['dr'] for scores in detailed_scores.values())
        total_smp = sum(scores['smp'] for scores in detailed_scores.values())
        
        return {
            'total_scores': {
                'dr': round(total_dr, 1),
                'smp': round(total_smp, 1)
            },
            'detailed_scores': detailed_scores,
            'recommendation': 'DR' if total_dr > total_smp else 'SMP',
            'score_gap': abs(total_dr - total_smp),
            'input_summary': {
                'capacity_kw': input_data.capacity_kw,
                'location': input_data.location,
                'budget_billion': input_data.budget_billion,
                'risk_preference': input_data.risk_preference
            }
        }
    
    def create_score_visualization(self, score_result: Dict) -> go.Figure:
        """점수 결과 레이더 차트 생성"""
        detailed = score_result['detailed_scores']
        
        # 카테고리 이름 (한글)
        categories = [
            '지역 차별화', '업체 규모', '리스크 선호도', '주차 패턴',
            '부지 인프라', '충전기 비율', '브랜드 신뢰성', '배터리 열화', '예산'
        ]
        
        # 각 카테고리별 DR/SMP 점수
        dr_scores = []
        smp_scores = []
        max_scores = []
        
        for key in ['region', 'scale', 'risk', 'parking', 'infrastructure', 
                   'charger', 'brand', 'battery', 'budget']:
            dr_scores.append(detailed[key]['dr'])
            smp_scores.append(detailed[key]['smp'])
            max_scores.append(detailed[key]['max'])
        
        # 레이더 차트 생성
        fig = go.Figure()
        
        # DR 점수
        fig.add_trace(go.Scatterpolar(
            r=dr_scores,
            theta=categories,
            fill='toself',
            name='국민DR',
            line_color='#1f77b4',
            fillcolor='rgba(31, 119, 180, 0.3)'
        ))
        
        # SMP 점수
        fig.add_trace(go.Scatterpolar(
            r=smp_scores,
            theta=categories,
            fill='toself',
            name='SMP',
            line_color='#ff7f0e',
            fillcolor='rgba(255, 127, 14, 0.3)'
        ))
        
        # 최대 점수 기준선
        fig.add_trace(go.Scatterpolar(
            r=max_scores,
            theta=categories,
            mode='lines',
            name='최대점수',
            line=dict(color='gray', dash='dash'),
            showlegend=True
        ))
        
        # 레이아웃 설정
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(max_scores)]
                )
            ),
            title={
                'text': f"V2G 사업 종합 점수 분석<br>" +
                       f"<sub>DR: {score_result['total_scores']['dr']:.1f}점 vs " +
                       f"SMP: {score_result['total_scores']['smp']:.1f}점</sub>",
                'x': 0.5,
                'font': {'size': 16}
            },
            showlegend=True,
            height=600,
            font=dict(family="Arial, sans-serif", size=12)
        )
        
        return fig
    
    def generate_score_report(self, score_result: Dict) -> str:
        """점수 결과 HTML 리포트 생성"""
        detailed = score_result['detailed_scores']
        total_dr = score_result['total_scores']['dr']
        total_smp = score_result['total_scores']['smp']
        recommendation = score_result['recommendation']
        
        # 카테고리별 이름 매핑
        category_names = {
            'region': '지역 차별화',
            'scale': '업체 규모',
            'risk': '리스크 선호도',
            'parking': '주차 패턴',
            'infrastructure': '부지 인프라',
            'charger': '충전기 비율',
            'brand': '브랜드 신뢰성',
            'battery': '배터리 열화',
            'budget': '예산'
        }
        
        report = f"""
        <div style="font-family: 'Noto Sans KR', Arial, sans-serif; line-height: 1.6;">
        
        <h3 style="text-align: center; color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 1rem;">
            🎯 V2G 사업 종합 점수 분석 결과
        </h3>
        
        <!-- 총점 요약 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
            <h4 style="color: white; margin-bottom: 1rem; font-size: 1.4rem;">📊 종합 점수</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;">
                    <div style="font-size: 2rem; font-weight: bold; color: #1f77b4;">DR</div>
                    <div style="font-size: 1.8rem; font-weight: bold;">{total_dr:.1f}점</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;">
                    <div style="font-size: 1.2rem; font-weight: bold;">VS</div>
                    <div style="font-size: 1rem;">점수차: {abs(total_dr - total_smp):.1f}점</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;">
                    <div style="font-size: 2rem; font-weight: bold; color: #ff7f0e;">SMP</div>
                    <div style="font-size: 1.8rem; font-weight: bold;">{total_smp:.1f}점</div>
                </div>
            </div>
        </div>
        
        <!-- 추천 결과 -->
        <div style="background: {'#d4edda' if recommendation == 'DR' else '#fff3cd'}; 
                    border: 2px solid {'#c3e6cb' if recommendation == 'DR' else '#ffeaa7'}; 
                    border-radius: 10px; padding: 1.5rem; margin-bottom: 2rem; text-align: center;">
            <h4 style="color: {'#155724' if recommendation == 'DR' else '#856404'}; margin-bottom: 0.5rem;">
                🏆 추천 사업 모델: {'국민DR' if recommendation == 'DR' else 'SMP'}
            </h4>
            <p style="margin: 0; color: {'#155724' if recommendation == 'DR' else '#856404'};">
                종합 점수 기준으로 {'국민DR' if recommendation == 'DR' else 'SMP'} 사업이 현재 조건에 더 적합합니다.
            </p>
        </div>
        
        <!-- 세부 점수 표 -->
        <h4 style="color: #495057; margin: 2rem 0 1rem 0; border-bottom: 2px solid #dee2e6; padding-bottom: 0.5rem;">
            📋 항목별 세부 점수
        </h4>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: left; font-weight: 600;">평가 항목</th>
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; background: #e3f2fd; font-weight: 600;">국민DR</th>
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; background: #fff3e0; font-weight: 600;">SMP</th>
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; font-weight: 600;">만점</th>
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; font-weight: 600;">우위</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for key, name in category_names.items():
            dr_score = detailed[key]['dr']
            smp_score = detailed[key]['smp']
            max_score = detailed[key]['max']
            
            # 우위 판단
            if dr_score > smp_score:
                advantage = "🔵 DR"
                advantage_color = "#1f77b4"
            elif smp_score > dr_score:
                advantage = "🟠 SMP"
                advantage_color = "#ff7f0e"
            else:
                advantage = "🟡 동점"
                advantage_color = "#ffc107"
            
            report += f"""
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: 500;">{name}</td>
                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center; background: #e3f2fd;">
                        <strong>{dr_score:.1f}점</strong>
                    </td>
                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center; background: #fff3e0;">
                        <strong>{smp_score:.1f}점</strong>
                    </td>
                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center;">{max_score}점</td>
                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center; color: {advantage_color}; font-weight: bold;">
                        {advantage}
                    </td>
                </tr>
            """
        
        # 총점 행 추가
        total_advantage = "🔵 DR" if total_dr > total_smp else "🟠 SMP" if total_smp > total_dr else "🟡 동점"
        total_color = "#1f77b4" if total_dr > total_smp else "#ff7f0e" if total_smp > total_dr else "#ffc107"
        
        report += f"""
                <tr style="background: #f1f3f4; font-weight: bold; font-size: 1.1rem;">
                    <td style="border: 2px solid #495057; padding: 15px; font-weight: bold;">🎯 총점</td>
                    <td style="border: 2px solid #495057; padding: 15px; text-align: center; background: #e3f2fd; font-size: 1.2rem;">
                        <strong>{total_dr:.1f}점</strong>
                    </td>
                    <td style="border: 2px solid #495057; padding: 15px; text-align: center; background: #fff3e0; font-size: 1.2rem;">
                        <strong>{total_smp:.1f}점</strong>
                    </td>
                    <td style="border: 2px solid #495057; padding: 15px; text-align: center;">100점</td>
                    <td style="border: 2px solid #495057; padding: 15px; text-align: center; color: {total_color}; font-weight: bold; font-size: 1.1rem;">
                        {total_advantage}
                    </td>
                </tr>
            </tbody>
        </table>
        
        <!-- 분석 의견 -->
        <div style="background: #f8f9fa; border-left: 4px solid #2563eb; padding: 1.5rem; border-radius: 0 8px 8px 0; margin-bottom: 2rem;">
            <h5 style="color: #2563eb; margin-bottom: 1rem;">💡 종합 분석 의견</h5>
            <p style="margin-bottom: 0.5rem; line-height: 1.7; color: #495057;">
                현재 입력 조건에서는 <strong style="color: {total_color};">{'국민DR' if recommendation == 'DR' else 'SMP'}</strong> 사업이 
                <strong>{abs(total_dr - total_smp):.1f}점 차이</strong>로 우위를 보입니다.
            </p>
            <p style="margin-bottom: 0; line-height: 1.7; color: #495057;">
                이는 단순 수익성을 넘어선 <strong>종합적 사업 적합성</strong>을 고려한 결과로, 
                리스크, 인프라, 브랜드 신뢰성 등 다양한 요소를 반영한 것입니다.
            </p>
        </div>
        
        </div>
        """
        
        return report

# 사용 예시 및 테스트 함수
def create_sample_score_input() -> V2GScoreInput:
    """샘플 입력 데이터 생성"""
    return V2GScoreInput(
        capacity_kw=1000,
        location="수도권",
        budget_billion=15,  # 15억원
        risk_preference="neutral",
        regular_pattern_ratio=0.7,
        dr_dispatch_time_ratio=0.6,
        charging_spots=50,
        power_capacity_mva=0.3,
        total_ports=100,
        smart_ocpp_ports=60,
        v2g_ports=30,
        brand_type="others",
        soh_under_70_ratio=0.1,
        soh_70_85_ratio=0.3,
        soh_85_95_ratio=0.5,
        soh_over_95_ratio=0.1
    )

if __name__ == "__main__":
    # 테스트 실행
    analyzer = V2GScoreAnalyzer()
    sample_input = create_sample_score_input()
    
    # 점수 계산
    result = analyzer.calculate_comprehensive_score(sample_input)
    
    # 결과 출력
    print("=" * 60)
    print("V2G 종합 점수 분석 결과")
    print("=" * 60)
    print(f"DR 총점: {result['total_scores']['dr']:.1f}점")
    print(f"SMP 총점: {result['total_scores']['smp']:.1f}점")
    print(f"추천 사업: {result['recommendation']}")
    print(f"점수 차이: {result['score_gap']:.1f}점")
    
    # 차트 생성
    fig = analyzer.create_score_visualization(result)
    fig.write_html("v2g_score_analysis.html")
    print("\n📊 차트가 'v2g_score_analysis.html'로 저장되었습니다.")
    
    # 리포트 생성
    report = analyzer.generate_score_report(result)
    with open("v2g_score_report.html", "w", encoding="utf-8") as f:
        f.write(report)
    print("📄 리포트가 'v2g_score_report.html'로 저장되었습니다.")