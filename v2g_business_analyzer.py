import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")

class V2GBusinessAnalyzer:
    def __init__(self):
        """V2G 사업 분석기 초기화"""
        self.dr_rates = {
            '기본요금': 3000,  # 원/kW/월
            '감축실적요금': 150,  # 원/kWh
            '가용용량요금': 2000  # 원/kW/월
        }
        
        self.smp_base_price = 85  # 원/kWh (기준 SMP 가격)
        self.operation_hours = 8760  # 연간 운영시간
        
    def calculate_dr_revenue(self, capacity_kw, location, annual_utilization=0.7):
        """국민DR 사업 수익 계산 - 웹 입력 변수 반영"""
        # 지역별 DR 활용도 조정
        location_factor = {
            '수도권': 1.2,
            '충청권': 1.0,
            '영남권': 1.1,
            '호남권': 0.9,
            '강원권': 0.8,
            '제주권': 0.7
        }.get(location, 1.0)
        
        # 월별 DR 수익 계산
        monthly_basic = capacity_kw * self.dr_rates['기본요금']
        monthly_capacity = capacity_kw * self.dr_rates['가용용량요금'] * location_factor
        
        # 연간 감축실적 (시즌별 변동 반영)
        seasonal_factors = [1.3, 1.1, 0.8, 0.7, 0.9, 1.4, 1.5, 1.4, 1.0, 0.8, 1.0, 1.2]
        
        annual_revenue = 0
        monthly_revenues = []
        
        for month, factor in enumerate(seasonal_factors):
            # 웹 입력된 활용률을 시즌별로 조정
            monthly_utilization = annual_utilization * factor
            monthly_reduction = capacity_kw * 30 * 2 * monthly_utilization  # 월 30일, 하루 평균 2시간
            monthly_reduction_revenue = monthly_reduction * self.dr_rates['감축실적요금']
            
            total_monthly = monthly_basic + monthly_capacity + monthly_reduction_revenue
            monthly_revenues.append(total_monthly)
            annual_revenue += total_monthly
            
        return {
            'annual_revenue': annual_revenue,
            'monthly_revenues': monthly_revenues,
            'basic_fee': monthly_basic * 12,
            'capacity_fee': monthly_capacity * 12,
            'reduction_fee': sum(monthly_revenues) - (monthly_basic + monthly_capacity) * 12
        }
    
    def calculate_smp_revenue(self, capacity_kw, location, annual_utilization=0.6):
        """SMP 사업 수익 계산 - 웹 입력 변수 반영"""
        # 지역별 SMP 가격 조정
        location_smp_factor = {
            '수도권': 1.0,
            '충청권': 0.95,
            '영남권': 0.98,
            '호남권': 0.92,
            '강원권': 0.88,
            '제주권': 0.85
        }.get(location, 1.0)
        
        # 시간대별 SMP 가격 변동 (24시간)
        hourly_smp_factors = [
            0.7, 0.6, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1,  # 0-7시
            1.2, 1.1, 1.0, 1.0, 1.1, 1.2, 1.3, 1.4,  # 8-15시
            1.5, 1.6, 1.7, 1.5, 1.3, 1.1, 0.9, 0.8   # 16-23시
        ]
        
        # 월별 수익 계산
        monthly_revenues = []
        seasonal_demand_factors = [1.2, 1.1, 0.9, 0.8, 0.7, 1.3, 1.4, 1.3, 1.0, 0.9, 1.0, 1.1]
        
        for month, demand_factor in enumerate(seasonal_demand_factors):
            monthly_revenue = 0
            days_in_month = 30  # 평균 30일
            
            # 웹 입력된 활용률을 시즌별로 조정
            adjusted_utilization = annual_utilization * demand_factor
            
            for day in range(days_in_month):
                for hour, hour_factor in enumerate(hourly_smp_factors):
                    # 실제 방전 여부 (웹 입력 활용률 기반)
                    if np.random.random() < adjusted_utilization:
                        hourly_price = self.smp_base_price * hour_factor * location_smp_factor
                        hourly_revenue = capacity_kw * hourly_price
                        monthly_revenue += hourly_revenue
            
            monthly_revenues.append(monthly_revenue)
        
        annual_revenue = sum(monthly_revenues)
        
        return {
            'annual_revenue': annual_revenue,
            'monthly_revenues': monthly_revenues,
            'average_price': annual_revenue / (capacity_kw * annual_utilization * self.operation_hours) if annual_utilization > 0 else 0
        }
    
    def calculate_investment_costs(self, capacity_kw, business_type):
        """투자 비용 계산 - 용량과 지역에 따른 동적 계산"""
        # V2G 시스템 구축 비용 (원/kW) - 기본값
        base_costs = {
            'v2g_equipment': 800000,  # V2G 충방전 장비
            'infrastructure': 300000,  # 인프라 구축
            'installation': 200000,   # 설치비
            'certification': 100000   # 인증비용
        }
        
        # 사업 유형별 추가 비용
        additional_costs = {
            'DR': {
                'system_integration': 150000,  # DR 시스템 연동
                'monitoring': 100000,          # 모니터링 시스템
            },
            'SMP': {
                'trading_system': 200000,      # 전력거래 시스템
                'forecast_system': 120000,     # 예측 시스템
            }
        }
        
        # 용량별 규모의 경제 효과 (대용량일수록 단위당 비용 감소)
        if capacity_kw >= 5000:
            scale_factor = 0.85  # 15% 할인
        elif capacity_kw >= 2000:
            scale_factor = 0.9   # 10% 할인
        elif capacity_kw >= 1000:
            scale_factor = 0.95  # 5% 할인
        else:
            scale_factor = 1.0   # 할인 없음
        
        # 전체 비용 딕셔너리 생성
        all_costs = {**base_costs, **additional_costs[business_type]}
        
        # 용량과 규모 효과를 적용한 총 비용 계산
        total_base_cost = sum(base_costs.values()) * capacity_kw * scale_factor
        total_additional_cost = sum(additional_costs[business_type].values()) * capacity_kw * scale_factor
        
        # 비용 세부 내역 (규모 효과 적용)
        cost_breakdown = {k: v * scale_factor for k, v in all_costs.items()}
        
        return {
            'equipment_cost': total_base_cost,
            'additional_cost': total_additional_cost,
            'total_investment': total_base_cost + total_additional_cost,
            'cost_breakdown': cost_breakdown,
            'scale_factor': scale_factor,
            'unit_cost_per_kw': (total_base_cost + total_additional_cost) / capacity_kw
        }
    
    def calculate_roi_metrics(self, annual_revenue, investment_cost, operation_years=10):
        """투자 수익률 지표 계산"""
        # 연간 운영비용 (투자비의 5%)
        annual_opex = investment_cost * 0.05
        annual_net_income = annual_revenue - annual_opex
        
        # ROI 계산
        roi = (annual_net_income * operation_years - investment_cost) / investment_cost * 100
        
        # 투자 회수 기간
        payback_period = investment_cost / annual_net_income if annual_net_income > 0 else float('inf')
        
        # NPV 계산 (할인율 5%)
        discount_rate = 0.05
        npv = -investment_cost
        for year in range(1, operation_years + 1):
            npv += annual_net_income / (1 + discount_rate) ** year
        
        # IRR 근사 계산
        irr = annual_net_income / investment_cost * 100 if investment_cost > 0 else 0
        
        return {
            'roi': roi,
            'payback_period': payback_period,
            'npv': npv,
            'irr': irr,
            'annual_net_income': annual_net_income
        }
    
    def generate_comparison_report(self, capacity_kw, location, utilization_dr=0.7, utilization_smp=0.6):
        """종합 비교 리포트 생성 - 모든 웹 입력 변수 활용"""
        # DR 사업 분석 (웹 입력 변수 전달)
        dr_revenue = self.calculate_dr_revenue(capacity_kw, location, utilization_dr)
        dr_costs = self.calculate_investment_costs(capacity_kw, 'DR')
        dr_roi = self.calculate_roi_metrics(dr_revenue['annual_revenue'], dr_costs['total_investment'])
        
        # SMP 사업 분석 (웹 입력 변수 전달)
        smp_revenue = self.calculate_smp_revenue(capacity_kw, location, utilization_smp)
        smp_costs = self.calculate_investment_costs(capacity_kw, 'SMP')
        smp_roi = self.calculate_roi_metrics(smp_revenue['annual_revenue'], smp_costs['total_investment'])
        
        return {
            'DR': {
                'revenue': dr_revenue,
                'costs': dr_costs,
                'roi_metrics': dr_roi
            },
            'SMP': {
                'revenue': smp_revenue,
                'costs': smp_costs,
                'roi_metrics': smp_roi
            }
        }
    
    def visualize_comparison(self, analysis_result, capacity_kw, location):
        """비교 결과 시각화 - DR과 SMP 비용구조 모두 표시"""
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=('월별 수익 비교', '투자 회수 분석', 'ROI 지표 비교', 
                           'DR 비용 구조', 'SMP 비용 구조', '수익 구조 비교'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}, {"type": "bar"}],
                   [{"type": "pie"}, {"type": "pie"}, {"type": "bar"}]]
        )
        
        # 1. 월별 수익 비교
        months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
        
        fig.add_trace(
            go.Scatter(x=months, y=analysis_result['DR']['revenue']['monthly_revenues'],
                      mode='lines+markers', name='국민DR', line=dict(color='#1f77b4', width=3)),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=months, y=analysis_result['SMP']['revenue']['monthly_revenues'],
                      mode='lines+markers', name='SMP', line=dict(color='#ff7f0e', width=3)),
            row=1, col=1
        )
        
        # 2. 투자 회수 분석
        years = list(range(1, 11))
        dr_cumulative = []
        smp_cumulative = []
        
        dr_annual_net = analysis_result['DR']['roi_metrics']['annual_net_income']
        smp_annual_net = analysis_result['SMP']['roi_metrics']['annual_net_income']
        dr_investment = analysis_result['DR']['costs']['total_investment']
        smp_investment = analysis_result['SMP']['costs']['total_investment']
        
        dr_cum = -dr_investment
        smp_cum = -smp_investment
        
        for year in years:
            dr_cum += dr_annual_net
            smp_cum += smp_annual_net
            dr_cumulative.append(dr_cum)
            smp_cumulative.append(smp_cum)
        
        fig.add_trace(
            go.Scatter(x=years, y=dr_cumulative, mode='lines+markers', 
                      name='국민DR 누적수익', line=dict(color='#1f77b4', width=3)),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(x=years, y=smp_cumulative, mode='lines+markers', 
                      name='SMP 누적수익', line=dict(color='#ff7f0e', width=3)),
            row=1, col=2
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)
        
        # 3. ROI 지표 비교
        metrics = ['ROI (%)', 'IRR (%)', '회수기간 (년)']
        dr_values = [
            analysis_result['DR']['roi_metrics']['roi'],
            analysis_result['DR']['roi_metrics']['irr'],
            min(analysis_result['DR']['roi_metrics']['payback_period'], 15)
        ]
        smp_values = [
            analysis_result['SMP']['roi_metrics']['roi'],
            analysis_result['SMP']['roi_metrics']['irr'],
            min(analysis_result['SMP']['roi_metrics']['payback_period'], 15)
        ]
        
        fig.add_trace(
            go.Bar(x=metrics, y=dr_values, name='국민DR', 
                   marker_color='#1f77b4', marker_line=dict(color='#0d47a1', width=1)),
            row=1, col=3
        )
        
        fig.add_trace(
            go.Bar(x=metrics, y=smp_values, name='SMP', 
                   marker_color='#ff7f0e', marker_line=dict(color='#e65100', width=1)),
            row=1, col=3
        )
        
        # 4. DR 비용 구조 분석
        dr_cost_breakdown = analysis_result['DR']['costs']['cost_breakdown']
        
        # 동적 비용 계산 (DR)
        location_cost_factor = {
            '수도권': {'infrastructure': 1.3, 'installation': 1.2, 'certification': 1.1},
            '충청권': {'infrastructure': 1.0, 'installation': 1.0, 'certification': 1.0},
            '영남권': {'infrastructure': 1.1, 'installation': 1.05, 'certification': 1.05},
            '호남권': {'infrastructure': 0.9, 'installation': 0.95, 'certification': 0.95},
            '강원권': {'infrastructure': 0.8, 'installation': 0.9, 'certification': 0.9},
            '제주권': {'infrastructure': 0.7, 'installation': 0.85, 'certification': 0.85}
        }.get(location, {'infrastructure': 1.0, 'installation': 1.0, 'certification': 1.0})
        
        scale_factor = min(1.0, 1000 / capacity_kw) if capacity_kw > 1000 else 1.0
        
        dr_dynamic_costs = {}
        for cost_type, base_cost in dr_cost_breakdown.items():
            if cost_type in location_cost_factor:
                adjusted_cost = base_cost * location_cost_factor[cost_type] * scale_factor * capacity_kw
            else:
                adjusted_cost = base_cost * capacity_kw
            dr_dynamic_costs[cost_type] = adjusted_cost
        
        # DR 비용구조 한글 라벨과 색상
        dr_cost_labels_korean = {
            'v2g_equipment': 'V2G 장비',
            'infrastructure': '인프라 구축',
            'installation': '설치비',
            'certification': '인증비용',
            'system_integration': 'DR 시스템 연동',
            'monitoring': '모니터링 시스템'
        }
        
        dr_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        dr_pie_labels = [dr_cost_labels_korean.get(k, k) for k in dr_dynamic_costs.keys()]
        dr_pie_values = list(dr_dynamic_costs.values())
        dr_pie_colors = dr_colors[:len(dr_pie_values)]
        
        fig.add_trace(
            go.Pie(
                labels=dr_pie_labels,
                values=dr_pie_values,
                name="DR 비용구조",
                marker=dict(colors=dr_pie_colors, line=dict(color='#FFFFFF', width=2)),
                textinfo='label+percent',
                textposition='auto',
                textfont=dict(size=10),
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 5. SMP 비용 구조 분석
        smp_cost_breakdown = analysis_result['SMP']['costs']['cost_breakdown']
        
        smp_dynamic_costs = {}
        for cost_type, base_cost in smp_cost_breakdown.items():
            if cost_type in location_cost_factor:
                adjusted_cost = base_cost * location_cost_factor[cost_type] * scale_factor * capacity_kw
            else:
                adjusted_cost = base_cost * capacity_kw
            smp_dynamic_costs[cost_type] = adjusted_cost
        
        # SMP 비용구조 한글 라벨과 색상
        smp_cost_labels_korean = {
            'v2g_equipment': 'V2G 장비',
            'infrastructure': '인프라 구축',
            'installation': '설치비',
            'certification': '인증비용',
            'trading_system': '전력거래 시스템',
            'forecast_system': '예측 시스템'
        }
        
        smp_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFB347', '#BA68C8']
        
        smp_pie_labels = [smp_cost_labels_korean.get(k, k) for k in smp_dynamic_costs.keys()]
        smp_pie_values = list(smp_dynamic_costs.values())
        smp_pie_colors = smp_colors[:len(smp_pie_values)]
        
        fig.add_trace(
            go.Pie(
                labels=smp_pie_labels,
                values=smp_pie_values,
                name="SMP 비용구조",
                marker=dict(colors=smp_pie_colors, line=dict(color='#FFFFFF', width=2)),
                textinfo='label+percent',
                textposition='auto',
                textfont=dict(size=10),
                showlegend=False
            ),
            row=2, col=2
        )
        
        # 6. 수익 구조 비교
        dr_revenue = analysis_result['DR']['revenue']
        revenue_comparison = ['DR 기본요금', 'DR 용량요금', 'DR 실적요금', 'SMP 총수익']
        revenue_values = [
            dr_revenue['basic_fee'],
            dr_revenue['capacity_fee'], 
            dr_revenue['reduction_fee'],
            analysis_result['SMP']['revenue']['annual_revenue']
        ]
        revenue_colors = ['#1f77b4', '#1f77b4', '#1f77b4', '#ff7f0e']
        
        fig.add_trace(
            go.Bar(x=revenue_comparison, y=revenue_values, 
                   marker_color=revenue_colors,
                   name='수익 구조',
                   showlegend=False),
            row=2, col=3
        )
        
        # 레이아웃 업데이트
        fig.update_layout(
            title=f"V2G 사업 종합 분석 리포트 - {location}, {capacity_kw:,}kW",
            showlegend=True,
            height=800,
            font=dict(size=11)
        )
        
        # 각 subplot별 축 레이블 설정
        fig.update_xaxes(title_text="월", row=1, col=1)
        fig.update_yaxes(title_text="수익 (원)", row=1, col=1)
        fig.update_xaxes(title_text="년도", row=1, col=2)
        fig.update_yaxes(title_text="누적 손익 (원)", row=1, col=2)
        fig.update_xaxes(title_text="지표", row=1, col=3)
        fig.update_yaxes(title_text="값", row=1, col=3)
        fig.update_xaxes(title_text="수익 항목", row=2, col=3)
        fig.update_yaxes(title_text="수익 (원)", row=2, col=3)
        
        return fig
    
    def generate_text_report(self, analysis_result, capacity_kw, location):
        """텍스트 리포트 생성 - HTML 표 형식으로 변경"""
        dr_data = analysis_result['DR']
        smp_data = analysis_result['SMP']
        
        # HTML 표 형식으로 리포트 생성
        report = f"""
    <div style="font-family: 'HCR Batang', 'HCR바탕', serif; font-size: 1.1rem; line-height: 1.8;">
    
    <h3>=== V2G 사업 비교 분석 리포트 ===</h3>
    <p><strong>분석 대상:</strong> {location} 지역, {capacity_kw:,}kW 규모</p>
    
    <h4>📊 수익성 분석</h4>
    <table border="1" cellpadding="12" cellspacing="0" style="width: 100%; border-collapse: collapse; margin: 1rem 0; font-family: 'HCR Batang', 'HCR바탕', serif;">
        <thead>
            <tr style="background-color: #f8f9fa; font-weight: bold; text-align: center;">
                <th style="border: 1px solid #dee2e6; padding: 12px; font-size: 1.1rem;">구분</th>
                <th style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; font-size: 1.1rem;">국민DR 사업</th>
                <th style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; font-size: 1.1rem;">SMP 사업</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">연간 수익</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['revenue']['annual_revenue']:,}원</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['revenue']['annual_revenue']:,}원</td>
            </tr>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">월평균 수익</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['revenue']['annual_revenue']/12:,.0f}원</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['revenue']['annual_revenue']/12:,.0f}원</td>
            </tr>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">총 투자비</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['costs']['total_investment']:,}원</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['costs']['total_investment']:,}원</td>
            </tr>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">연간 순이익</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['roi_metrics']['annual_net_income']:,}원</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['roi_metrics']['annual_net_income']:,}원</td>
            </tr>
        </tbody>
    </table>
    
    <h4>💰 투자 수익률 지표</h4>
    <table border="1" cellpadding="12" cellspacing="0" style="width: 100%; border-collapse: collapse; margin: 1rem 0; font-family: 'HCR Batang', 'HCR바탕', serif;">
        <thead>
            <tr style="background-color: #f8f9fa; font-weight: bold; text-align: center;">
                <th style="border: 1px solid #dee2e6; padding: 12px; font-size: 1.1rem;">지표</th>
                <th style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; font-size: 1.1rem;">국민DR 사업</th>
                <th style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; font-size: 1.1rem;">SMP 사업</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">ROI (10년)</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['roi_metrics']['roi']:6.1f}%</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['roi_metrics']['roi']:6.1f}%</td>
            </tr>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">IRR</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['roi_metrics']['irr']:6.1f}%</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['roi_metrics']['irr']:6.1f}%</td>
            </tr>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">투자회수기간</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['roi_metrics']['payback_period']:6.1f}년</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['roi_metrics']['payback_period']:6.1f}년</td>
            </tr>
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: bold;">NPV (10년)</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #e3f2fd; text-align: center;">{dr_data['roi_metrics']['npv']:,}원</td>
                <td style="border: 1px solid #dee2e6; padding: 12px; background-color: #fff3e0; text-align: center;">{smp_data['roi_metrics']['npv']:,}원</td>
            </tr>
        </tbody>
    </table>
    
    <h4>🎯 추천 사업 모델</h4>
    """
        
        # 추천 로직
        dr_score = 0
        smp_score = 0
        
        # 수익성 비교
        if dr_data['revenue']['annual_revenue'] > smp_data['revenue']['annual_revenue']:
            dr_score += 2
            report += "<p>✓ 국민DR이 연간 수익이 높음</p>"
        else:
            smp_score += 2
            report += "<p>✓ SMP가 연간 수익이 높음</p>"
        
        # 투자회수기간 비교
        if dr_data['roi_metrics']['payback_period'] < smp_data['roi_metrics']['payback_period']:
            dr_score += 2
            report += "<p>✓ 국민DR이 투자회수기간이 짧음</p>"
        else:
            smp_score += 2
            report += "<p>✓ SMP가 투자회수기간이 짧음</p>"
        
        # 안정성 비교 (DR이 더 안정적)
        dr_score += 1
        report += "<p>✓ 국민DR이 정부정책 기반으로 더 안정적</p>"
        
        if dr_score > smp_score:
            recommendation = "국민DR 사업"
            report += f"""
    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 15px 0;">
        <h4 style="color: #155724; margin-bottom: 10px;">🏆 최종 추천: {recommendation}</h4>
        <p style="color: #155724; margin-bottom: 5px;">추천 점수 - 국민DR: {dr_score}점, SMP: {smp_score}점</p>
    </div>
    """
        else:
            recommendation = "SMP 사업"
            report += f"""
    <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 15px; margin: 15px 0;">
        <h4 style="color: #0c5460; margin-bottom: 10px;">🏆 최종 추천: {recommendation}</h4>
        <p style="color: #0c5460; margin-bottom: 5px;">추천 점수 - 국민DR: {dr_score}점, SMP: {smp_score}점</p>
    </div>
    """
        
        report += f"""
    <h4>📋 상세 분석 의견</h4>
    
    <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 15px 0;">
        <h5 style="color: #007bff; margin-bottom: 10px;">국민DR 사업의 특징:</h5>
        <ul style="margin-bottom: 0;">
            <li>정부 정책 기반의 안정적 수익 구조</li>
            <li>계약된 요금 체계로 예측 가능한 수익</li>
            <li>상대적으로 낮은 시장 변동성 리스크</li>
            <li>기본요금 + 용량요금 + 실적요금의 3단계 수익 구조</li>
        </ul>
    </div>
    
    <div style="background-color: #f8f9fa; border-left: 4px solid #fd7e14; padding: 15px; margin: 15px 0;">
        <h5 style="color: #fd7e14; margin-bottom: 10px;">SMP 사업의 특징:</h5>
        <ul style="margin-bottom: 0;">
            <li>시장가격 기반의 변동성 있는 수익 구조</li>
            <li>전력시장 상황에 따른 높은 수익 가능성</li>
            <li>시간대별, 계절별 가격 차익 활용 가능</li>
            <li>상대적으로 높은 시장 리스크</li>
        </ul>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 15px 0;">
        <p style="color: #856404; margin-bottom: 0; font-weight: bold;">
            현재 조건 ({location} 지역, {capacity_kw:,}kW)에서는 {recommendation}을(를) 추천합니다.
        </p>
    </div>
    
    </div>
    """
        
        return report

# 메인 실행 클래스
class V2GBusinessConsultant:
    def __init__(self):
        self.analyzer = V2GBusinessAnalyzer()
    
    def run_consultation(self, capacity_kw, location, utilization_dr=0.7, utilization_smp=0.6):
        """컨설팅 실행 - 웹 입력 변수 모두 활용"""
        print("=" * 60)
        print("V2G 사업 비교 분석 컨설팅 프로그램")
        print(f"분석 조건: {location} 지역, {capacity_kw:,}kW, DR 활용률: {utilization_dr*100:.0f}%, SMP 활용률: {utilization_smp*100:.0f}%")
        print("=" * 60)
        
        # 분석 실행 (모든 웹 입력 변수 전달)
        analysis_result = self.analyzer.generate_comparison_report(
            capacity_kw, location, utilization_dr, utilization_smp
        )
        
        # 텍스트 리포트 출력
        text_report = self.analyzer.generate_text_report(analysis_result, capacity_kw, location)
        print(text_report)
        
        # 그래프 생성
        fig = self.analyzer.visualize_comparison(analysis_result, capacity_kw, location)
        
        return analysis_result, fig, text_report

# 사용 예시 (기본값 제거, 파라미터 필수화)
if __name__ == "__main__":
    consultant = V2GBusinessConsultant()
    
    # 기본 예시 (웹에서 받을 변수들과 동일한 구조)
    capacity = 1000  # 웹 입력
    location = "수도권"  # 웹 입력
    dr_utilization = 0.75  # 웹 입력 (75%)
    smp_utilization = 0.65  # 웹 입력 (65%)
    
    result, chart, report = consultant.run_consultation(
        capacity_kw=capacity,
        location=location,
        utilization_dr=dr_utilization,
        utilization_smp=smp_utilization
    )
    
    # 결과를 HTML 파일로 저장
    chart.write_html("v2g_business_analysis.html")
    print(f"\n📁 차트가 'v2g_business_analysis.html'로 저장되었습니다.")
    print(f"📊 분석 조건: {location} 지역, {capacity:,}kW, DR {dr_utilization*100:.0f}%, SMP {smp_utilization*100:.0f}%")
    
    # 리포트를 텍스트 파일로 저장
    with open("v2g_business_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("📁 리포트가 'v2g_business_report.txt'로 저장되었습니다.")
