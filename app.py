import streamlit as st
import pandas as pd
import math
from datetime import date
from weasyprint import HTML

# --- 1. 頁面基本設定與專業外觀 ---
st.set_page_config(page_title="御晁工程報價系統", layout="wide")

# --- 2. 隱藏官方選單、頁首頁尾與右下角所有浮水印 (終極隱藏版) ---
hide_style = """
    <style>
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    div[class*="viewerBadge"] {display: none !important; opacity: 0 !important;}
    div[class*="CreatorProfile"] {display: none !important; opacity: 0 !important;}
    iframe[title*="badge"] {display: none !important;}
    iframe[src*="badge"] {display: none !important;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

# --- 3. 主程式直接啟動 (已移除密碼驗證) ---

# 基礎參數設定
SQ_CM_PER_PING = 33058
PRICE_PRO, PRICE_BASIC = 3000, 2000
PRICE_RUBBLE, PRICE_TRASH = 2200, 3000
PRICE_WOOD = 6

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏗️ 御晁工程有限公司 - 施工報價系統")
st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    "🛠️ 階段一：現場精算", 
    "📄 階段二：正式施工報價單(對外)", 
    "🕵️ 階段三：內部底價核算表(對內)"
])

with tab1:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        space_options = ["全室", "客廳", "廚房", "主衛浴", "客衛浴", "主臥室", "次臥室", "陽台", "樓梯", "外牆", "其他"]
        selected_space = st.selectbox("📍 施作空間", space_options)
    with col_b:
        demo_content = st.text_input("📝 拆除內容描述", value="天花板及隔間牆拆除清運")

    st.markdown("---")
    st.subheader("📐 現場丈量與材質選擇")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        material = st.selectbox("選擇拆除材質", [
            "4吋磚牆", "8吋磚牆", "RC牆", 
            "矽酸鈣板隔間/天花", "磁磚剃除", "泥作表面剃除", "其他材質"
        ])
        mud_thickness = 0.0
        if material == "泥作表面剃除":
            mud_thickness = st.number_input("📏 輸入泥作厚度 (cm)", min_value=0.5, value=2.0, step=0.5)

    with m_col2:
        length = st.number_input("長度 (cm)", min_value=0, value=500, step=10)
    with m_col3:
        height = st.number_input("高度 (cm)", min_value=0, value=300, step=10)
    with m_col4:
        calc_ping = round((length * height) / SQ_CM_PER_PING, 2)
        st.metric("換算坪數", f"{calc_ping} 坪")

    st.write("---")
    st.subheader("📊 預算細節編列 (內部成本核算)")
    b_col1, b_col2, b_col3 = st.columns(3)

    # 自動帶入邏輯
    if material == "4吋磚牆":
        default_rubble, default_pro = calc_ping * 0.75, math.ceil(calc_ping / 6)
    elif material == "8吋磚牆":
        default_rubble, default_pro = calc_ping * 1.5, math.ceil(calc_ping / 3)
    elif material == "RC牆":
        default_rubble, default_pro = calc_ping * 1.5, math.ceil(calc_ping / 2)
    elif material == "矽酸鈣板隔間/天花":
        default_rubble, default_pro = 0.0, math.ceil(calc_ping / 8)
    elif material == "磁磚剃除":
        default_rubble, default_pro = calc_ping * 0.1, math.ceil(calc_ping / 8)
    elif material == "泥作表面剃除":
        vol = calc_ping * 3.3058 * (mud_thickness / 100) * 1.2
        default_rubble, default_pro = round(vol, 2), math.ceil(calc_ping / 6)
    else:
        default_rubble, default_pro = 0.0, 1.0

    with b_col1:
        pro_workers = st.number_input("大工 (工)", value=float(default_pro), step=0.5)
        basic_workers = st.number_input("小工 (工)", value=1.0, step=0.5)
    with b_col2:
        rubble_in = st.number_input("紅磚/RC土石 (米³)", value=float(default_rubble), step=0.5)
        trash_in = st.number_input("一般垃圾 (米³)", value=float(0.0 if material not in ["矽酸鈣板隔間/天花", "磁磚剃除"] else calc_ping * 0.3), step=0.5)
        wood_in = st.number_input("廢木材 (公斤)", value=0, step=10)
    with b_col3:
        machine_in = st.number_input("機具費用 ($)", min_value=0, value=0)
        food_in = st.number_input("餐/飲/雜項 ($)", min_value=0, value=0)

    st.write("---")
    profit_margin = st.select_slider("💰 設定此項目的預期利潤率 (%)", options=[0, 10, 15, 20, 25, 30, 40, 50], value=30)

    cost_labor = (pro_workers * PRICE_PRO) + (basic_workers * PRICE_BASIC)
    cost_trash = (rubble_in * PRICE_RUBBLE) + (trash_in * PRICE_TRASH) + (wood_in * 6)
    cost_total = cost_labor + cost_trash + machine_in + food_in
    profit_amt = cost_total * (profit_margin / 100)
    final_price = cost_total + profit_amt

    c1, c2, c3 = st.columns(3)
    c1.metric("內部實支總成本", f"NT$ {int(cost_total):,}")
    c2.metric("預估毛利", f"NT$ {int(profit_amt):,}")
    c3.metric("建議單項報價", f"NT$ {int(final_price):,}")

    if st.button("➕ 加入清單", type="primary", use_container_width=True):
        memo_text = f"材質:{material} / 面積:{length}x{height}cm"
        if material == "泥作表面剃除":
            memo_text += f" (厚度:{mud_thickness}cm)"
            
        st.session_state.cart.append({
            "項次": len(st.session_state.cart) + 1,
            "品名內容": f"{selected_space} - {demo_content}",
            "數量": 1,
            "單位": "式",
            "內部底價": int(cost_total),
            "利潤額": int(profit_amt),
            "報價單價": int(final_price),
            "報價複價": int(final_price),
            "備註": memo_text,
            "利潤率": f"{profit_margin}%"
        })
        st.success("✅ 已加入清單！")

with tab2:
    st.subheader("📑 御晁工程有限公司 - 施工報價單 (對外)")
    h_col1, h_col2, h_col3, h_col4 = st.columns(4)
    client_name = h_col1.text_input("客戶名稱", value="", key="c_name")
    client_contact = h_col2.text_input("聯絡人 / 電話", value="", key="c_tel")
    quote_date_str = h_col3.date_input("報價日期", date.today(), key="q_date").strftime("%Y/%m/%d")
    tax_status = h_col4.selectbox("稅額設定", ["稅外加", "未稅", "含稅"], key="t_stat")
    
    st.write("---")
    
    if len(st.session_state.cart) > 0:
        df_quote = pd.DataFrame(st.session_state.cart)
        df_display = df_quote[["項次", "品名內容", "數量", "單位", "報價單價", "報價複價", "備註"]].copy()
        df_display.columns = ["項次", "品名內容", "數量", "單位", "單價", "複價", "備註"]
        df_display["單價"] = df_display["單價"].apply(lambda x: f"$ {int(x):,}")
        df_display["複價"] = df_display["複價"].apply(lambda x: f"$ {int(x):,}")
        
        st.table(df_display)
        
        sub_total = df_quote["報價複價"].sum()
        tax_amount = int(sub_total * 0.05) if tax_status == "稅外加" else 0
        grand_total = sub_total + tax_amount
        
        sum_c1, sum_c2 = st.columns([3, 1])
        with sum_c2:
            st.write(f"小計金額： NT$ {int(sub_total):,}")
            if tax_status == "稅外加":
                st.write(f"營業稅(5%)： NT$ {int(tax_amount):,}")
            st.write(f"### 總計金額： NT$ {int(grand_total):,}")

        if st.button("📄 產生專業版 PDF 報價單並下載", use_container_width=True):
            table_rows = ""
            for item in st.session_state.cart:
                table_rows += f"""
                <tr>
                    <td style="text-align: center;">{item['項次']}</td>
                    <td>{item['品名內容']}<br><small style="color: #7f8c8d;">{item['備註']}</small></td>
                    <td style="text-align: center;">{item['數量']}</td>
                    <td style="text-align: center;">{item['單位']}</td>
                    <td class="text-right">$ {item['報價單價']:,}</td>
                    <td class="text-right">$ {item['報價複價']:,}</td>
                </tr>
                """
            
            tax_row = f"""<div class="total-row"><span class="total-label">營業稅 (5%)：</span><span class="total-value">NT$ {int(tax_amount):,}</span></div>""" if tax_status == "稅外加" else ""

            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-Hant">
            <head><meta charset="UTF-8"><style>
                @page {{ size: A4; margin: 15mm; }} 
                body {{ font-family: 'Noto Sans CJK TC', sans-serif; color: #333; line-height: 1.4; }} 
                .header-bar {{ background-color: #1a5276; padding: 25px; color: white; margin: -15mm -15mm 15px -15mm; }} 
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 10pt; }} 
                th, td {{ padding: 10px; border-bottom: 1px solid #eee; }} 
                th {{ background: #f2f4f4; color: #1a5276; }} 
                .text-right {{ text-align: right; }} 
                .totals {{ width: 250px; float: right; margin-top: 10px; }} 
                .grand {{ border-top: 2px solid #1a5276; font-size: 13pt; color: #c0392b; font-weight: bold; }}
                .remark-box {{ clear: both; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 9pt; color: #555; }}
                .signature-section {{ margin-top: 40px; width: 100%; display: table; }}
                .sig-box {{ display: table-cell; width: 50%; vertical-align: bottom; }}
                .stamp-box {{ display: inline-block; width: 100px; height: 100px; border: 1px dashed #ccc; text-align: center; line-height: 100px; color: #ccc; }}
            </style></head>
            <body>
                <div class="header-bar"><h1>御晁工程有限公司</h1><div style="font-size: 11pt;">施工報價單 (Construction Quotation)</div></div>
                <div style="margin-bottom: 20px;">
                    <span style="display:inline-block; width:50%;">客戶名稱：{client_name if client_name else '_______________'}</span>
                    <span style="display:inline-block; width:45%; text-align:right;">報價日期：{quote_date_str}</span><br>
                    <span style="display:inline-block; width:50%;">聯絡資訊：{client_contact if client_contact else '_______________'}</span>
                    <span style="display:inline-block; width:45%; text-align:right;">稅額設定：{tax_status}</span>
                </div>
                <table><thead><tr><th>項次</th><th>品名 / 施作內容說明</th><th>數量</th><th>單位</th><th class="text-right">單價</th><th class="text-right">複價</th></tr></thead>
                <tbody>{table_rows}</tbody></table>
                <div class="totals">
                    <div class="total-row"><span class="total-label">合計金額：</span><span class="total-value">NT$ {int(sub_total):,}</span></div>
                    {tax_row}
                    <div class="total-row grand"><span>總計金額：</span><span style="float:right;">NT$ {int(grand_total):,}</span></div>
                </div>
                
                <div class="remark-box">
                    <p style="font-weight: bold; margin-bottom: 5px; color: #333;">備註事項：</p>
                    <div style="margin-left: 15px;">
                        1. 報價內容:甲方所有拆除物及廢棄物清運。<br>
                        2. 施工期間:甲乙雙方意向協議。<br>
                        3. 付款方式:甲乙雙方意向協議。<br>
                        4. 未經報價內容若追加減雙方須協調另行報價方可施工。<br>
                        5. 需先請淨空不在拆除範圍所有地面物件避免拆除過程無法順利進行。<br>
                        6. 以上拆除如需防護作業需另行報價。<br>
                        7. 以上報價總金額為統包價格。<br>
                        8. 以上工程施工期間未因不可抗拒之因素條件，需正常施工甲乙雙方不得無故拖延。
                    </div>
                </div>

                <div class="signature-section">
                    <div class="sig-box">
                        <div style="margin-bottom: 50px;">客戶確認簽章：____________________</div>
                        <div>日期：&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;年&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;月&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;日</div>
                    </div>
                    <div class="sig-box" style="text-align: right;">
                        <div style="margin-bottom: 5px;">御晁工程有限公司 (簽章)</div>
                        <div class="stamp-box">公司蓋印處</div>
                    </div>
                </div>
            </body></html>"""
            pdf_bytes = HTML(string=html_content).write_pdf()
            st.download_button("📥 下載 PDF 正式報價單", data=pdf_bytes, file_name=f"報價單_{client_name if client_name else '未命名'}.pdf", mime="application/pdf")

with tab3:
    st.subheader("🕵️ 御晁工程 - 內部底價與利潤核算表 (對內)")
    if len(st.session_state.cart) > 0:
        df_internal = pd.DataFrame(st.session_state.cart)
        
        if "利潤率" not in df_internal.columns:
            df_internal["利潤率"] = "N/A"
            
        df_internal_display = df_internal[["項次", "品名內容", "內部底價", "報價複價", "利潤額", "利潤率"]].copy()
        df_internal_display.columns = ["項次", "品名內容", "內部成本(底價)", "對外報價", "毛利額", "預計毛利率"]
        for col in ["內部成本(底價)", "對外報價", "毛利額"]:
            df_internal_display[col] = df_internal_display[col].apply(lambda x: f"$ {int(x):,}")
        st.table(df_internal_display)
        
        total_internal_cost = df_internal["內部底價"].sum()
        total_net_profit = df_internal["利潤額"].sum()
        avg_profit_rate = (total_net_profit / total_internal_cost * 100) if total_internal_cost > 0 else 0
        
        st.divider()
        st.markdown("### 💰 整場工程總結算")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("📦 整場總成本(底價)", f"$ {int(total_internal_cost):,}")
        sc2.metric("💵 整場總毛利", f"$ {int(total_net_profit):,}")
        sc3.metric("📈 平均毛利率", f"{avg_profit_rate:.1f}%")
        
        if st.button("🗑️ 清空所有資料", key="clear_all"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("目前尚無資料。")
