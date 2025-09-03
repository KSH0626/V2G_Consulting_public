import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from v2g_business_analyzer import V2GBusinessAnalyzer, V2GBusinessConsultant
from advances_analysis import AdvancedV2GAnalyzer, BusinessScenario, create_scenario_from_web_input

class V2GDashboard:
    """V2G 사업 분석 대시보드 - 웹 입력 변수 완전 반영"""
    
    def __init__(self):
        self.analyzer = V2GBusinessAnalyzer()
        self.consultant = V2GBusinessConsultant()
        self.advanced_analyzer = AdvancedV2GAnalyzer()
    
    def create_dashboard(self):
        """Streamlit 대시보드 생성 - 동적 입력 반영"""
        st.set_page_config(
            page_title="V2G 사업 비교 분석 컨설팅",
            page_icon="⚡",
            layout="wide"
        )
        
        st.title("⚡ V2G 사업 비교 분석 컨설팅 시스템")
        st.markdown("---")
        
        # 사이드바 - 입력 파라미터
        with st.sidebar:
            st.header("📊 분석 조건 설정")
            
            # 웹 입력 변수들
            capacity = st.slider(
                "설비 용량 (kW)",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                help="설비 용량이 클수록 투자비와 수익이 비례적으로 증가합니다."
            )
            
            location = st.selectbox(
                "사업 지역",
                ["수도권", "충청권", "영남권", "호남권", "강원권", "제주권"],
                help="지역별로 전력 수급 상황과 가격 조정 계수가 다릅니다."
            )
            
            utilization_dr = st.slider(
                "DR 활용률 (%)",
                min_value=30,
                max_value=95,
                value=70,
                step=5,
                help="DR 시장 참여 시 실제 방전 활용 비율"
            ) / 100
            
            utilization_smp = st.slider(
                "SMP 활용률 (%)",
                min_value=30,
                max_value=85,
                value=60,
                step=5,
                help="SMP 시장 참여 시 실제 방전 활용 비율"
            ) / 100
            
            st.markdown("---")
            
            # 고급 옵션
            with st.expander("🔧 고급 설정"):
                operation_years = st.slider("분석 기간 (년)", 5, 20, 10)
                discount_rate = st.slider("할인율 (%)", 1.0, 10.0, 5.0) / 100
                
            analyze_button = st.button("🔍 분석 실행", type="primary", use_container_width=True)
        
        # 실시간 입력 정보 표시
        st.info(f"🎯 **현재 분석 조건**: {location} 지역, {capacity:,}kW, DR 활용률 {utilization_dr*100:.0f}%, SMP 활용률 {utilization_smp*100:.0f}%")
        
        # 메인 컨텐츠
        if analyze_button:
            with st.spinner("🔄 분석 중... 입력된 조건을 바탕으로 계산하고 있습니다."):
                # 실제 웹 입력 변수들을 모든 분석에 전달
                analysis_result = self.analyzer.generate_comparison_report(
                    capacity, location, utilization_dr, utilization_smp
                )
                
                # 결과 표시
                self.display_results(analysis_result, capacity, location, utilization_dr, utilization_smp)
                
                # 고급 분석 섹션
                self.display_advanced_analysis(capacity, location, utilization_dr, utilization_smp)
    
    def display_results(self, analysis_result, capacity, location, utilization_dr, utilization_smp):
        """분석 결과 표시 - 웹 입력 변수 정보 포함"""
        dr_data = analysis_result['DR']
        smp_data = analysis_result['SMP']
        
        # 입력 조건 요약
        st.subheader("📋 분석 조건 요약")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("설비 용량", f"{capacity:,} kW")
        with col2:
            st.metric("사업 지역", location)
        with col3:
            st.metric("DR 활용률", f"{utilization_dr*100:.0f}%")
        with col4:
            st.metric("SMP 활용률", f"{utilization_smp*100:.0f}%")
        
        st.markdown("---")
        
        # 핵심 지표 카드
        st.subheader("💰 핵심 성과 지표")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "DR 연간 수익",
                f"{dr_data['revenue']['annual_revenue']:,}원",
                f"월평균 {dr_data['revenue']['annual_revenue']/12:,.0f}원"
            )
        
        with col2:
            st.metric(
                "SMP 연간 수익",
                f"{smp_data['revenue']['annual_revenue']:,}원",
                f"월평균 {smp_data['revenue']['annual_revenue']/12:,.0f}원"
            )
        
        with col3:
            st.metric(
                "DR ROI (10년)",
                f"{dr_data['roi_metrics']['roi']:.1f}%",
                f"회수기간 {dr_data['roi_metrics']['payback_period']:.1f}년"
            )
        
        with col4:
            st.metric(
                "SMP ROI (10년)",
                f"{smp_data['roi_metrics']['roi']:.1f}%",
                f"회수기간 {smp_data['roi_metrics']['payback_period']:.1f}년"
            )
        
        # 추천 결과
        if dr_data['roi_metrics']['roi'] > smp_data['roi_metrics']['roi']:
            st.success(f"🏆 **추천 사업: 국민DR** (ROI {dr_data['roi_metrics']['roi']:.1f}% > {smp_data['roi_metrics']['roi']:.1f}%)")
            st.write(f"현재 조건 ({location} 지역, {capacity:,}kW, DR {utilization_dr*100:.0f}% 활용)에서는 국민DR이 더 유리합니다.")
        else:
            st.success(f"🏆 **추천 사업: SMP** (ROI {smp_data['roi_metrics']['roi']:.1f}% > {dr_data['roi_metrics']['roi']:.1f}%)")
            st.write(f"현재 조건 ({location} 지역, {capacity:,}kW, SMP {utilization_smp*100:.0f}% 활용)에서는 SMP가 더 유리합니다.")
        
        st.markdown("---")
        
        # 차트 섹션
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 월별 수익 비교")
            months = ['1월', '2월', '3월', '4월', '5월', '6월', 
                     '7월', '8월', '9월', '10월', '11월', '12월']
            
            fig_monthly = go.Figure()
            fig_monthly.add_trace(go.Scatter(
                x=months,
                y=dr_data['revenue']['monthly_revenues'],
                mode='lines+markers',
                name=f'국민DR (활용률 {utilization_dr*100:.0f}%)',
                line=dict(color='#1f77b4', width=3)
            ))
            fig_monthly.add_trace(go.Scatter(
                x=months,
                y=smp_data['revenue']['monthly_revenues'],
                mode='lines+markers',
                name=f'SMP (활용률 {utilization_smp*100:.0f}%)',
                line=dict(color='#ff7f0e', width=3)
            ))
            fig_monthly.update_layout(
                title=f"월별 수익 변화 - {location} 지역, {capacity:,}kW",
                xaxis_title="월",
                yaxis_title="수익 (원)",
                hovermode='x unified'
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        with col2:
            st.subheader("💰 투자 회수 분석")
            years = list(range(1, 11))
            
            # 누적 수익 계산
            dr_annual_net = dr_data['roi_metrics']['annual_net_income']
            smp_annual_net = smp_data['roi_metrics']['annual_net_income']
            dr_investment = dr_data['costs']['total_investment']
            smp_investment = smp_data['costs']['total_investment']
            
            dr_cumulative = [-dr_investment]
            smp_cumulative = [-smp_investment]
            
            for year in years:
                dr_cumulative.append(dr_cumulative[-1] + dr_annual_net)
                smp_cumulative.append(smp_cumulative[-1] + smp_annual_net)
            
            fig_roi = go.Figure()
            fig_roi.add_trace(go.Scatter(
                x=[0] + years,
                y=dr_cumulative,
                mode='lines+markers',
                name='국민DR',
                line=dict(color='#1f77b4', width=3)
            ))
            fig_roi.add_trace(go.Scatter(
                x=[0] + years,
                y=smp_cumulative,
                mode='lines+markers',
                name='SMP',
                line=dict(color='#ff7f0e', width=3)
            ))
            fig_roi.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_roi.update_layout(
                title=f"누적 손익 분석 - {capacity:,}kW",
                xaxis_title="년도",
                yaxis_title="누적 손익 (원)",
                hovermode='x unified'
            )
            st.plotly_chart(fig_roi, use_container_width=True)
        
        # 상세 분석 섹션
        st.markdown("---")
        st.subheader("📋 상세 분석 결과")
        
        tab1, tab2, tab3 = st.tabs(["💰 수익 구조", "💸 비용 분석", "⚖️ 비교 분석"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**국민DR 수익 구조**")
                dr_revenue_breakdown = {
                    '기본요금': dr_data['revenue']['basic_fee'],
                    '용량요금': dr_data['revenue']['capacity_fee'],
                    '실적요금': dr_data['revenue']['reduction_fee']
                }
                
                fig_dr_pie = px.pie(
                    values=list(dr_revenue_breakdown.values()),
                    names=list(dr_revenue_breakdown.keys()),
                    title=f"DR 수익 구성 ({location} 지역 기준)"
                )
                st.plotly_chart(fig_dr_pie, use_container_width=True)
                
                st.write(f"**활용률 {utilization_dr*100:.0f}% 기준 수익 상세:**")
                for key, value in dr_revenue_breakdown.items():
                    st.write(f"- {key}: {value:,}원 ({value/dr_data['revenue']['annual_revenue']*100:.1f}%)")
            
            with col2:
                st.write("**SMP 수익 분석**")
                st.write(f"**활용률 {utilization_smp*100:.0f}% 기준:**")
                st.write(f"- 연간 총 수익: {smp_data['revenue']['annual_revenue']:,}원")
                st.write(f"- 평균 판매 단가: {smp_data['revenue']['average_price']:.1f}원/kWh")
                st.write(f"- 월평균 수익: {smp_data['revenue']['annual_revenue']/12:,.0f}원")
                
                # 월별 변동성 차트
                smp_monthly = smp_data['revenue']['monthly_revenues']
                fig_smp_var = go.Figure()
                fig_smp_var.add_trace(go.Bar(
                    x=months,
                    y=smp_monthly,
                    name='월별 SMP 수익',
                    marker_color='orange'
                ))
                fig_smp_var.update_layout(
                    title=f"SMP 월별 수익 변동 (활용률 {utilization_smp*100:.0f}%)",
                    xaxis_title="월",
                    yaxis_title="수익 (원)"
                )
                st.plotly_chart(fig_smp_var, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**국민DR 투자 비용 구성**")
                dr_costs = dr_data['costs']['cost_breakdown']
                
                # 비용을 용량으로 나누어 단위당 비용 표시
                unit_costs = {k: v for k, v in dr_costs.items()}
                fig_dr_cost = px.bar(
                    x=list(unit_costs.keys()),
                    y=list(unit_costs.values()),
                    title=f"DR 비용 구성 (단위: 원/kW)"
                )
                fig_dr_cost.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_dr_cost, use_container_width=True)
                
                st.write(f"**총 투자비 ({capacity:,}kW 기준):**")
                st.write(f"- 총 투자비: {dr_data['costs']['total_investment']:,}원")
                st.write(f"- kW당 투자비: {dr_data['costs']['total_investment']/capacity:,.0f}원/kW")
            
            with col2:
                st.write("**SMP 투자 비용 구성**")
                smp_costs = smp_data['costs']['cost_breakdown']
                
                unit_costs = {k: v for k, v in smp_costs.items()}
                fig_smp_cost = px.bar(
                    x=list(unit_costs.keys()),
                    y=list(unit_costs.values()),
                    title=f"SMP 비용 구성 (단위: 원/kW)"
                )
                fig_smp_cost.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_smp_cost, use_container_width=True)
                
                st.write(f"**총 투자비 ({capacity:,}kW 기준):**")
                st.write(f"- 총 투자비: {smp_data['costs']['total_investment']:,}원")
                st.write(f"- kW당 투자비: {smp_data['costs']['total_investment']/capacity:,.0f}원/kW")
        
        with tab3:
            st.write("**현재 조건에서의 비교 분석**")
            
            # 비교 테이블
            comparison_data = {
                '지표': [
                    '연간 수익', '총 투자비', 'ROI (10년)', '투자회수기간', 
                    '연간 순이익', 'NPV', 'IRR', '활용률'
                ],
                '국민DR': [
                    f"{dr_data['revenue']['annual_revenue']:,}원",
                    f"{dr_data['costs']['total_investment']:,}원",
                    f"{dr_data['roi_metrics']['roi']:.1f}%",
                    f"{dr_data['roi_metrics']['payback_period']:.1f}년",
                    f"{dr_data['roi_metrics']['annual_net_income']:,}원",
                    f"{dr_data['roi_metrics']['npv']:,}원",
                    f"{dr_data['roi_metrics']['irr']:.1f}%",
                    f"{utilization_dr*100:.0f}%"
                ],
                'SMP': [
                    f"{smp_data['revenue']['annual_revenue']:,}원",
                    f"{smp_data['costs']['total_investment']:,}원",
                    f"{smp_data['roi_metrics']['roi']:.1f}%",
                    f"{smp_data['roi_metrics']['payback_period']:.1f}년",
                    f"{smp_data['roi_metrics']['annual_net_income']:,}원",
                    f"{smp_data['roi_metrics']['npv']:,}원",
                    f"{smp_data['roi_metrics']['irr']:.1f}%",
                    f"{utilization_smp*100:.0f}%"
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
            
            # 장단점 비교
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🔵 국민DR 장단점**")
                st.success("**장점:**")
                st.write("• 정부 정책 기반의 안정적 수익")
                st.write("• 예측 가능한 요금 체계")
                st.write("• 낮은 시장 변동성 리스크")
                
                st.error("**단점:**")
                st.write("• 상대적으로 낮은 수익 천장")
                st.write("• 정책 변경 리스크")
                
            with col2:
                st.write("**🟠 SMP 장단점**")
                st.success("**장점:**")
                st.write("• 시장 가격 기반 높은 수익 가능성")
                st.write("• 시간대별 가격 차익 활용")
                st.write("• 시장 성장에 따른 수익 증대")
                
                st.error("**단점:**")
                st.write("• 높은 가격 변동성")
                st.write("• 시장 경쟁 심화 리스크")
                st.write("• 예측하기 어려운 수익성")
    
    def display_advanced_analysis(self, capacity, location, utilization_dr, utilization_smp):
        """고급 분석 표시 - 웹 입력 변수 기반"""
        st.markdown("---")
        st.subheader("🔬 고급 분석")
        
        # 현재 입력 조건으로 시나리오 생성
        current_scenario = BusinessScenario(
            name=f"{location}_{capacity}kW_시나리오",
            capacity_kw=capacity,
            location=location,
            investment_budget=capacity * 1400000,  # kW당 140만원 기본
            target_roi=15.0,
            risk_tolerance='medium',
            utilization_dr=utilization_dr,
            utilization_smp=utilization_smp
        )
        
        tab1, tab2 = st.tabs(["📊 민감도 분석", "⚠️ 리스크 분석"])
        
        with tab1:
            st.write("**주요 변수별 ROI 민감도**")
            
            # 민감도 분석 변수 설정
            sensitivity_vars = {
                'utilization_dr': [0.5, 0.6, 0.7, 0.8, 0.9],
                'utilization_smp': [0.4, 0.5, 0.6, 0.7, 0.8],
                'capacity': [capacity * 0.5, capacity * 0.75, capacity, capacity * 1.25, capacity * 1.5]
            }
            
            sensitivity_results = self.advanced_analyzer.sensitivity_analysis(current_scenario, sensitivity_vars)
            
            # 민감도 분석 차트
            fig_sensitivity = make_subplots(
                rows=1, cols=3,
                subplot_titles=['DR 활용률 민감도', 'SMP 활용률 민감도', '설비 용량 민감도']
            )
            
            for i, (var_name, results) in enumerate(sensitivity_results.items(), 1):
                values = [r['value'] for r in results]
                dr_rois = [r['dr_roi'] for r in results]
                smp_rois = [r['smp_roi'] for r in results]
                
                fig_sensitivity.add_trace(
                    go.Scatter(x=values, y=dr_rois, mode='lines+markers', 
                              name='DR ROI', line=dict(color='blue'), showlegend=(i==1)),
                    row=1, col=i
                )
                
                fig_sensitivity.add_trace(
                    go.Scatter(x=values, y=smp_rois, mode='lines+markers', 
                              name='SMP ROI', line=dict(color='red'), showlegend=(i==1)),
                    row=1, col=i
                )
            
            fig_sensitivity.update_layout(
                title=f"민감도 분석 결과 - 기준: {location} 지역, {capacity:,}kW",
                height=400
            )
            st.plotly_chart(fig_sensitivity, use_container_width=True)
            
            # 민감도 분석 테이블
            for var_name, results in sensitivity_results.items():
                st.write(f"**{var_name} 변동 영향:**")
                
                sensitivity_df = pd.DataFrame([
                    {
                        '값': f"{r['value']:.0f}" if var_name == 'capacity' else f"{r['value']:.1f}",
                        'DR ROI': f"{r['dr_roi']:.1f}%",
                        'SMP ROI': f"{r['smp_roi']:.1f}%",
                        'ROI 차이': f"{r['dr_roi'] - r['smp_roi']:.1f}%p"
                    }
                    for r in results
                ])
                st.dataframe(sensitivity_df, use_container_width=True)
        
        with tab2:
            st.write("**몬테카르로 시뮬레이션 기반 리스크 분석**")
            
            # 리스크 분석 실행
            risk_result = self.advanced_analyzer.risk_analysis(current_scenario)
            
            # 리스크 지표 표시
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🔵 국민DR 리스크 지표**")
                dr_risk = risk_result['dr_risk_metrics']
                
                risk_df = pd.DataFrame({
                    '지표': ['평균 ROI', '표준편차', '95% VaR', '99% VaR', '수익 확률'],
                    '값': [
                        f"{dr_risk['mean_roi']:.1f}%",
                        f"{dr_risk['std_roi']:.1f}%",
                        f"{dr_risk['var_95']:.1f}%",
                        f"{dr_risk['var_99']:.1f}%",
                        f"{dr_risk['prob_positive']:.1%}"
                    ]
                })
                st.dataframe(risk_df, use_container_width=True)
            
            with col2:
                st.write("**🟠 SMP 리스크 지표**")
                smp_risk = risk_result['smp_risk_metrics']
                
                risk_df = pd.DataFrame({
                    '지표': ['평균 ROI', '표준편차', '95% VaR', '99% VaR', '수익 확률'],
                    '값': [
                        f"{smp_risk['mean_roi']:.1f}%",
                        f"{smp_risk['std_roi']:.1f}%",
                        f"{smp_risk['var_95']:.1f}%",
                        f"{smp_risk['var_99']:.1f}%",
                        f"{smp_risk['prob_positive']:.1%}"
                    ]
                })
                st.dataframe(risk_df, use_container_width=True)
            
            # 리스크 해석
            st.info(f"""
            **📊 리스크 분석 해석:**
            
            • **95% VaR**: 최악의 5% 시나리오에서도 이 수준 이상의 ROI 보장
            • **수익 확률**: 투자 후 수익을 낼 확률
            • **표준편차**: ROI 변동성 (낮을수록 안정적)
            
            **현재 조건 ({location} 지역, {capacity:,}kW)에서:**
            - 국민DR은 {'높은' if dr_risk['prob_positive'] > 0.8 else '보통' if dr_risk['prob_positive'] > 0.6 else '낮은'} 수익 확률 ({dr_risk['prob_positive']:.1%})
            - SMP는 {'높은' if smp_risk['prob_positive'] > 0.8 else '보통' if smp_risk['prob_positive'] > 0.6 else '낮은'} 수익 확률 ({smp_risk['prob_positive']:.1%})
            """)

# 대시보드 실행 함수
def run_dashboard():
    """대시보드 실행"""
    dashboard = V2GDashboard()
    dashboard.create_dashboard()

# 웹 기반 분석을 위한 함수들
def analyze_with_web_inputs(capacity, location, utilization_dr, utilization_smp):
    """웹 입력을 받아서 분석 실행"""
    analyzer = V2GBusinessAnalyzer()
    consultant = V2GBusinessConsultant()
    
    # 웹 입력 변수들을 직접 전달
    analysis_result, fig, text_report = consultant.run_consultation(
        capacity_kw=capacity,
        location=location,
        utilization_dr=utilization_dr,
        utilization_smp=utilization_smp
    )
    
    return analysis_result, fig, text_report

def create_web_scenario(name, capacity, location, budget, target_roi, risk_tolerance, 
                       dr_utilization=0.7, smp_utilization=0.6):
    """웹 입력으로부터 시나리오 생성"""
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

if __name__ == "__main__":
    # Railway에서는 이 부분이 직접 실행되지 않으므로
    # Streamlit이 파일을 직접 실행할 수 있도록 함수 호출을 제거
    dashboard = V2GDashboard()
    dashboard.create_dashboard()

