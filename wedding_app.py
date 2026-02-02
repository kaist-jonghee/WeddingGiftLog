import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="결혼식 축의금 장부 (Session)", layout="wide")

# --- 1. 세션 스테이트 초기화 (CSV 파일 대신 메모리 사용) ---
if 'df' not in st.session_state:
    # 빈 데이터프레임을 세션에 생성 (이 탭에서만 유효함)
    st.session_state.df = pd.DataFrame(
        columns=['삭제', 'No', '이름', '소속', '금액(만원)', '비고', '입력시간']
    )

# --- 함수 정의 ---

def get_next_no():
    """다음 번호 생성"""
    if st.session_state.df.empty:
        return 1
    else:
        return int(st.session_state.df['No'].max()) + 1

def add_entry(name, affiliation, amount, memo):
    """데이터 추가 (세션 변수에 저장)"""
    new_no = get_next_no()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    final_affiliation = affiliation if affiliation.strip() else "-"
    final_memo = memo if memo.strip() else "-"
    
    # 새로운 행 생성
    new_row = pd.DataFrame({
        '삭제': [False],
        'No': [new_no],
        '이름': [name],
        '소속': [final_affiliation],
        '금액(만원)': [amount],
        '비고': [final_memo],
        '입력시간': [current_time]
    })
    
    # 세션의 데이터프레임에 합치기
    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)

# --- UI 구성 ---

st.title("💍 결혼식 축의금 장부 (Private Session)")
st.caption("주의: 이 페이지를 '새로고침' 하거나 닫으면 데이터가 사라집니다. 수시로 다운로드 하세요!")
st.markdown("---")

col1, col2 = st.columns([1, 2])

# [왼쪽] 입력 폼
with col1:
    st.subheader("📥 신규 추가")
    st.caption("입력 순서: 이름 -> (Tab) -> 금액 -> (Enter)")
    
    with st.form("entry_form", clear_on_submit=True):
        name = st.text_input("이름 (필수)")
        amount_str = st.text_input("금액 (단위: 만원)", placeholder="예: 5 또는 10.5")
        affiliation = st.text_input("소속")
        memo = st.text_input("비고 (특이사항)")
        
        submitted = st.form_submit_button("기록하기 (Enter)", type="primary")

        if submitted:
            if name == "":
                st.error("이름을 입력해주세요.")
            elif amount_str == "":
                st.warning("금액을 입력해주세요.")
            else:
                try:
                    amount = float(amount_str)
                    add_entry(name, affiliation, amount, memo)
                    st.success(f"✅ 추가됨: {name}")
                    st.rerun()
                except ValueError:
                    st.error("금액은 숫자만 입력해주세요.")

# [오른쪽] 현황판
with col2:
    st.subheader("📊 실시간 현황")
    
    # 1. 계산 및 데이터 준비
    # 누적계는 저장하지 않고 보여줄 때만 매번 다시 계산 (데이터 무결성 위해)
    if not st.session_state.df.empty:
        # 화면 표시용 복사본 생성
        display_df = st.session_state.df.copy()
        
        # 누적계 계산
        display_df['누적계(만원)'] = display_df['금액(만원)'].cumsum()
        
        # 통계
        total_count = len(display_df)
        total_amount = display_df['금액(만원)'].sum()
        last_row = display_df.iloc[-1]
        
        # 상단 요약 패널
        with st.container(border=True):
            tc1, tc2, tc3 = st.columns([1, 1, 1.5])
            tc1.metric("총 인원", f"{total_count}명")
            tc2.metric("총 모금액", f"{total_amount:,.1f} 만원")
            with tc3:
                st.caption("🚀 방금 입력된 내용")
                st.markdown(f"**{last_row['이름']}** ({last_row['소속']}) | 💰 **{last_row['금액(만원)']}**")

        # 경고창 공간 예약
        alert_placeholder = st.empty()

        # 2. 데이터 에디터 (표)
        # 최신순 정렬 (보여주기용)
        df_sorted = display_df.sort_values(by='No', ascending=False)
        
        edited_df = st.data_editor(
            df_sorted,
            height=450,
            hide_index=True,
            use_container_width=True,
            disabled=["No", "입력시간", "누적계(만원)"], 
            column_config={
                "삭제": st.column_config.CheckboxColumn(width="small"),
                "No": st.column_config.NumberColumn(width="small"),
                "이름": st.column_config.TextColumn(width="medium"),
                "금액(만원)": st.column_config.NumberColumn(format="%.1f 만원"),
                "누적계(만원)": st.column_config.NumberColumn(format="%.1f 만원"),
                "소속": st.column_config.TextColumn(width="small"),
                "비고": st.column_config.TextColumn(width="large"),
            }
        )

        # 3. 변경 사항 반영 로직
        
        # (A) 삭제 로직
        rows_to_delete = edited_df[edited_df['삭제'] == True]
        
        if not rows_to_delete.empty:
            with alert_placeholder.container():
                st.error(f"⚠️ {len(rows_to_delete)}개의 항목이 선택되었습니다. 삭제하시겠습니까?")
                if st.button("🗑️ 상단 확인: 네, 삭제합니다", type="primary"):
                    # 삭제되지 않은 행만 골라내서 세션에 덮어쓰기 (누적계 컬럼 제외)
                    # edited_df에는 누적계가 있으므로, 원본 구조(st.session_state.df)에 맞춰야 함
                    
                    # 1. 삭제 체크 안 된 것만 필터링
                    keep_df = edited_df[edited_df['삭제'] == False]
                    
                    # 2. 누적계 컬럼 제거 (원본 세션엔 없으므로)
                    if '누적계(만원)' in keep_df.columns:
                        keep_df = keep_df.drop(columns=['누적계(만원)'])
                    
                    # 3. 세션 업데이트 (No 기준 정렬 유지)
                    st.session_state.df = keep_df.sort_values(by='No').reset_index(drop=True)
                    
                    st.success("삭제되었습니다.")
                    st.rerun()

        # (B) 수정 로직 (삭제가 아닐 때)
        else:
            # 에디터에서 수정된 내용(edited_df)을 세션(st.session_state.df)에 반영
            # 비교를 위해 포맷 통일 (누적계 제외, No 정렬)
            
            # 현재 세션 데이터
            current_session = st.session_state.df.sort_values(by='No').reset_index(drop=True)
            
            # 에디터 데이터 (누적계 제거)
            edited_data = edited_df.drop(columns=['누적계(만원)'], errors='ignore')
            edited_data = edited_data.sort_values(by='No').reset_index(drop=True)
            
            # 내용이 다르면 세션 업데이트
            if not current_session.equals(edited_data):
                st.session_state.df = edited_data
                # 빈칸 처리 로직
                st.session_state.df[['이름', '소속', '비고']] = st.session_state.df[['이름', '소속', '비고']].fillna("-")
                st.session_state.df['소속'] = st.session_state.df['소속'].replace("", "-")
                st.session_state.df['비고'] = st.session_state.df['비고'].replace("", "-")
                
                st.toast("💾 수정사항이 메모리에 반영됨")
                st.rerun()

        # 4. 다운로드 (CSV 생성 시점에 정렬 및 누적계 포함)
        st.markdown("")
        
        # 다운로드용 데이터 생성
        download_df = st.session_state.df.copy()
        
        # (1) 삭제 컬럼 제거
        if '삭제' in download_df.columns:
            download_df = download_df.drop(columns=['삭제'])
            
        # (2) No 기준 오름차순 정렬 (1번부터)
        download_df = download_df.sort_values(by='No', ascending=True)
        
        # (3) 누적계 계산해서 포함
        download_df['누적계(만원)'] = download_df['금액(만원)'].cumsum()
        
        # (4) CSV 변환
        csv_data = download_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        
        st.download_button(
            label="💾 엑셀 파일 다운로드 (필수)", 
            data=csv_data, 
            file_name='wedding_list_final.csv', 
            mime='text/csv', 
            use_container_width=True,
            type="primary" # 다운로드가 중요하다는 것을 강조하기 위해 색상 변경
        )

    else:
        st.info("왼쪽에서 데이터를 입력해주세요.")