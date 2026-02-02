import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 파일 이름
FILE_NAME = 'wedding_ledger.csv'

# 페이지 설정
st.set_page_config(page_title="결혼식 축의금 장부", layout="wide")

# --- 함수 정의 ---

def load_data():
    """CSV 파일을 불러오고 데이터 전처리를 수행합니다."""
    if not os.path.exists(FILE_NAME):
        # 파일이 없으면 빈 데이터프레임 생성
        return pd.DataFrame(columns=['No', '이름', '소속', '금액(만원)', '누적계(만원)', '비고', '입력시간'])
    else:
        df = pd.read_csv(FILE_NAME)
        
        # 컬럼 방어 및 빈칸 처리
        if '비고' not in df.columns: df['비고'] = "-"
        if '누적계(만원)' not in df.columns: df['누적계(만원)'] = 0
        if '소속' not in df.columns: df['소속'] = "-"

        df[['이름', '소속', '비고']] = df[['이름', '소속', '비고']].fillna("-")
        df['소속'] = df['소속'].replace("", "-")
        df['비고'] = df['비고'].replace("", "-")
        
        return df

def save_to_csv(df):
    """누적계 계산 후 CSV 저장 (삭제 컬럼은 저장하지 않음)"""
    # 1. 누적계 재계산
    df['누적계(만원)'] = df['금액(만원)'].cumsum()
    
    # 2. '삭제' 컬럼 제거 후 저장
    save_df = df.copy()
    if '삭제' in save_df.columns:
        save_df = save_df.drop(columns=['삭제'])
        
    save_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')

def get_next_no(df):
    """번호 생성 로직"""
    if df.empty:
        return 1
    else:
        return int(df['No'].max()) + 1

def add_entry(name, affiliation, amount, memo):
    """데이터 추가"""
    df = load_data()
    new_no = get_next_no(df)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    final_affiliation = affiliation if affiliation.strip() else "-"
    final_memo = memo if memo.strip() else "-"
    
    new_data = pd.DataFrame({
        'No': [new_no],
        '이름': [name],
        '소속': [final_affiliation],
        '금액(만원)': [amount],
        '누적계(만원)': [0],
        '비고': [final_memo],
        '입력시간': [current_time]
    })
    
    if not df.empty:
        if '삭제' in df.columns:
            df = df.drop(columns=['삭제'])
        updated_df = pd.concat([df, new_data], ignore_index=True)
    else:
        updated_df = new_data
        
    save_to_csv(updated_df)

# --- UI 구성 ---

st.title("💍 결혼식 축의금 장부")
st.markdown("---")

col1, col2 = st.columns([1, 2])

# [왼쪽] 입력 폼
with col1:
    st.subheader("📥 신규 추가")
    st.caption("입력 순서: 이름 -> (Tab) -> 금액 -> (Enter)")
    
    with st.form("entry_form", clear_on_submit=True):
        name = st.text_input("이름 (필수)")
        amount_str = st.text_input("금액 (단위: 만원)", placeholder="예: 5 또는 0")
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
                    
                    # [수정됨] 0원 체크 로직 삭제 -> 0원도 입력 가능하도록 변경
                    add_entry(name, affiliation, amount, memo)
                    
                    st.success(f"✅ 저장 완료: {name}")
                    st.rerun()
                        
                except ValueError:
                    st.error("금액은 숫자만 입력해주세요.")

# [오른쪽] 현황판
with col2:
    st.subheader("📊 실시간 현황")
    
    df = load_data()
    
    if not df.empty:
        if '삭제' not in df.columns:
            df['삭제'] = False
            
        # 컬럼 순서: 삭제를 맨 앞으로
        cols = ['삭제', 'No', '이름', '금액(만원)', '누적계(만원)', '소속', '비고', '입력시간']
        cols = [c for c in cols if c in df.columns] 
        df = df[cols]

        # 요약 패널
        df['누적계(만원)'] = df['금액(만원)'].cumsum()
        total_count = len(df)
        total_amount = df['금액(만원)'].sum()
        last_row = df.iloc[-1]
        
        with st.container(border=True):
            tc1, tc2, tc3 = st.columns([1, 1, 1.5])
            tc1.metric("총 인원", f"{total_count}명")
            tc2.metric("총 모금액", f"{total_amount:,.1f} 만원")
            with tc3:
                st.caption("🚀 방금 입력된 내용")
                st.markdown(f"**{last_row['이름']}** ({last_row['소속']}) | 💰 **{last_row['금액(만원)']}**")

        # 경고창 공간 예약
        alert_placeholder = st.empty()

        # 데이터 에디터
        df_display = df.sort_values(by='No', ascending=False)
        
        edited_df = st.data_editor(
            df_display,
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

        # 삭제 로직
        rows_to_delete = edited_df[edited_df['삭제'] == True]
        
        if not rows_to_delete.empty:
            with alert_placeholder.container():
                st.error(f"⚠️ {len(rows_to_delete)}개의 항목이 선택되었습니다. 삭제하시겠습니까?")
                if st.button("🗑️ 상단 확인: 네, 삭제합니다", type="primary"):
                    final_df = edited_df[edited_df['삭제'] == False]
                    save_to_csv(final_df.sort_values(by='No'))
                    st.success("삭제되었습니다.")
                    st.rerun()
        
        # 수정 로직
        else:
            df_core = df.sort_values(by='No').drop(columns=['누적계(만원)', '삭제']).reset_index(drop=True)
            edited_core = edited_df.sort_values(by='No').drop(columns=['누적계(만원)', '삭제']).reset_index(drop=True)
            
            if not df_core.equals(edited_core):
                save_to_csv(edited_df.sort_values(by='No'))
                st.toast("💾 수정사항 저장됨!")
                st.rerun()

        # 다운로드
        st.markdown("")
        download_df = edited_df.drop(columns=['삭제'], errors='ignore').sort_values(by="No", ascending=True)
        csv_data = download_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("💾 엑셀 파일 다운로드", csv_data, 'wedding_list_final.csv', 'text/csv', use_container_width=True)

    else:
        st.info("왼쪽에서 데이터를 입력해주세요.")