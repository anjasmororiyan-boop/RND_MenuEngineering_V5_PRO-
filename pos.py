import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP SariKue Signature v16", layout="wide")

# --- SMART FORMATTING FUNCTION ---
def smart_format(val):
    if val is None: return "0"
    try:
        val_float = float(val)
        if val_float.is_integer():
            return "{:,.0f}".format(val_float).replace(",", ".")
        formatted = "{:,.5f}".format(val_float).rstrip('0').rstrip('.')
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

# --- 2. INITIALIZING SESSION STATES ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'default_initialized' not in st.session_state:
    st.session_state.master_units = ["Kg", "Liter", "Pcs", "Gram", "Box"]
    st.session_state.expense_categories = ["Gaji", "Listrik/Air", "Sewa", "Marketing", "Maintenance"]
    
    st.session_state.master_vendors = pd.DataFrame([
        {"Nama": "PT. Sumber Pangan", "Status": "Active"},
        {"Nama": "UD. Makmur Jaya", "Status": "Active"}
    ])
    
    st.session_state.master_warehouses = pd.DataFrame([
        {"Nama": "Gudang Utama", "Status": "Active"},
        {"Nama": "Central Kitchen", "Status": "Active"}
    ])
    
    st.session_state.master_bahan_baku = pd.DataFrame([
        {"SKU": "RAW001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Stok": 50.0, "Min_Stok": 10.0, "Status": "Active"}
    ])
    
    st.session_state.master_penjualan = pd.DataFrame([
        {"SKU": "SALE001", "Nama": "Roti Tawar", "Harga_Jual": 15000.0, "Status": "Active"}
    ])
    
    st.session_state.pr_data = []
    st.session_state.pr_items_temp = []
    st.session_state.pos_transactions = []
    st.session_state.expenses_data = []
    st.session_state.cash_session = {"modal_awal": 0.0, "status": "Closed"}
    st.session_state.default_initialized = True

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔐 Login ERP System")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Login Gagal. Periksa Username/Password.")
    st.stop()

# --- 4. SIDEBAR NAVIGASI ---
menu = st.sidebar.radio("Navigasi Utama", [
    "Dashboard", 
    "Master Data Management", 
    "Procurement (PR Multi-Item)", 
    "POS (Kasir)", 
    "Laporan Keuangan"
])

# --- 5. LOGIKA MENU ---

# A. DASHBOARD
if menu == "Dashboard":
    st.header("📊 Dashboard Overview")
    st.subheader("Stok Bahan Baku")
    st.dataframe(st.session_state.master_bahan_baku, use_container_width=True)

# B. MASTER DATA MANAGEMENT
elif menu == "Master Data Management":
    st.header("⚙️ Pusat Kendali Master Data")
    t_raw, t_sale, t_vendor, t_wh = st.tabs(["🌾 Bahan Baku", "💰 Menu Jual", "🏢 Vendor", "🏠 Warehouse"])
    
    with t_raw:
        st.subheader("Bahan Baku")
        with st.expander("➕ Tambah / Edit Bahan"):
            with st.form("fm_raw"):
                c1, c2 = st.columns(2)
                e_sku = c1.text_input("SKU (Input SKU lama untuk Update)")
                e_nama = c1.text_input("Nama")
                e_sat = c2.selectbox("Satuan", st.session_state.master_units)
                e_min = c2.number_input("Min Stok", format="%.2f")
                e_status = c2.selectbox("Status", ["Active", "Inactive"])
                if st.form_submit_button("Simpan"):
                    mask = st.session_state.master_bahan_baku['SKU'] == e_sku
                    if mask.any():
                        st.session_state.master_bahan_baku.loc[mask, ['Nama', 'Satuan', 'Min_Stok', 'Status']] = [e_nama, e_sat, e_min, e_status]
                        st.success(f"Update {e_sku} berhasil.")
                    else:
                        new_row = {"SKU": e_sku, "Nama": e_nama, "Satuan": e_sat, "Stok": 0.0, "Min_Stok": e_min, "Status": e_status}
                        st.session_state.master_bahan_baku = pd.concat([st.session_state.master_bahan_baku, pd.DataFrame([new_row])], ignore_index=True)
                        st.success("Item baru ditambahkan.")
                    st.rerun()
        st.dataframe(st.session_state.master_bahan_baku, use_container_width=True)

    with t_sale:
        st.subheader("Menu Penjualan")
        with st.expander("➕ Tambah / Edit Menu"):
            with st.form("fm_sale"):
                s_sku = st.text_input("SKU Produk")
                s_nama = st.text_input("Nama Menu")
                s_price = st.number_input("Harga Jual", format="%.2f")
                s_status = st.selectbox("Status", ["Active", "Inactive"])
                if st.form_submit_button("Simpan Menu"):
                    mask = st.session_state.master_penjualan['SKU'] == s_sku
                    if mask.any():
                        st.session_state.master_penjualan.loc[mask, ['Nama', 'Harga_Jual', 'Status']] = [s_nama, s_price, s_status]
                        st.success(f"Update {s_sku} berhasil.")
                    else:
                        new_sale = {"SKU": s_sku, "Nama": s_nama, "Harga_Jual": s_price, "Status": s_status}
                        st.session_state.master_penjualan = pd.concat([st.session_state.master_penjualan, pd.DataFrame([new_sale])], ignore_index=True)
                        st.success("Menu baru ditambahkan.")
                    st.rerun()
        st.dataframe(st.session_state.master_penjualan, use_container_width=True)

    with t_vendor:
        st.subheader("Master Vendor")
        st.dataframe(st.session_state.master_vendors, use_container_width=True)

    with t_wh:
        st.subheader("Master Warehouse")
        st.dataframe(st.session_state.master_warehouses, use_container_width=True)

# C. PROCUREMENT (PR MULTI-ITEM)
elif menu == "Procurement (PR Multi-Item)":
    st.header("📋 Purchase Requisition (PR)")
    tab_pr, tab_mon = st.tabs(["📝 Buat PR Baru", "📄 Monitoring"])
    
    with tab_pr:
        with st.container(border=True):
            col_h1, col_h2 = st.columns(2)
            active_v = st.session_state.master_vendors[st.session_state.master_vendors['Status'] == "Active"]
            pr_vendor = col_h1.selectbox("Vendor", active_v['Nama'].tolist())
            active_w = st.session_state.master_warehouses[st.session_state.master_warehouses['Status'] == "Active"]
            pr_wh = col_h2.selectbox("Ke Warehouse", active_w['Nama'].tolist())

        active_raw = st.session_state.master_bahan_baku[st.session_state.master_bahan_baku['Status'] == "Active"]
        if active_raw.empty:
            st.warning("Tidak ada bahan baku aktif.")
        else:
            p_item = st.selectbox("Pilih Bahan Baku", active_raw['Nama'].tolist())
            it_info = active_raw[active_raw['Nama'] == p_item].iloc[0]
            
            with st.form("add_item_pr", clear_on_submit=True):
                c_q, c_p = st.columns(2)
                q_in = c_q.number_input(f"Qty ({it_info['Satuan']})", min_value=0.1)
                p_in = c_p.number_input("Estimasi Harga", min_value=0.0)
                if st.form_submit_button("➕ Tambahkan"):
                    st.session_state.pr_items_temp.append({
                        "Kode": it_info['SKU'], "Item": p_item, "Satuan": it_info['Satuan'],
                        "Qty": q_in, "Harga": p_in, "Total": q_in * p_in
                    })
                    st.rerun()
            
            if st.session_state.pr_items_temp:
                df_temp = pd.DataFrame(st.session_state.pr_items_temp)
                st.table(df_temp)
                if st.button("🚀 SUBMIT PR"):
                    pr_id = f"PR-{datetime.now().strftime('%y%m%d%H%M')}"
                    for row in st.session_state.pr_items_temp:
                        st.session_state.pr_data.append({
                            "PR_ID": pr_id, "Vendor": pr_vendor, "WH": pr_wh,
                            "Item": row['Item'], "Qty": row['Qty'], "Status": "Pending"
                        })
                    st.session_state.pr_items_temp = []
                    st.success(f"PR {pr_id} Terkirim!")
                    st.rerun()

    with tab_mon:
        if st.session_state.pr_data:
            st.dataframe(pd.DataFrame(st.session_state.pr_data), use_container_width=True)
        else:
            st.info("Belum ada data PR.")

# D. POS (KASIR)
elif menu == "POS (Kasir)":
    st.header("💰 Kasir Penjualan")
    if st.session_state.cash_session['status'] == "Closed":
        modal = st.number_input("Modal Awal", min_value=0.0)
        if st.button("Buka Sesi Kasir"):
            st.session_state.cash_session = {"modal_awal": modal, "status": "Open"}
            st.rerun()
    else:
        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            active_menu = st.session_state.master_penjualan[st.session_state.master_penjualan['Status'] == "Active"]
            if active_menu.empty:
                st.warning("Tidak ada menu aktif.")
            else:
                with st.form("pos_form"):
                    s_name = st.selectbox("Menu", active_menu['Nama'].tolist())
                    s_qty = st.number_input("Qty", min_value=1)
                    if st.form_submit_button("Add to Bill"):
                        price = active_menu[active_menu['Nama'] == s_name].iloc[0]['Harga_Jual']
                        st.session_state.pos_transactions.append({
                            "Item": s_name, "Qty": s_qty, "Total": s_qty * price
                        })
                        st.rerun()
        with col_p2:
            st.subheader("Bill")
            if st.session_state.pos_transactions:
                df_bill = pd.DataFrame(st.session_state.pos_transactions)
                st.table(df_bill)
                st.write(f"**Total: Rp {smart_format(df_bill['Total'].sum())}**")
                if st.button("Close Sesi & Save"):
                    st.session_state.cash_session['status'] = "Closed"
                    st.success("Sesi Ditutup")
                    st.rerun()

# E. LAPORAN KEUANGAN
elif menu == "Laporan Keuangan":
    st.header("📈 Financial Reports")
    revenue = sum(t['Total'] for t in st.session_state.pos_transactions)
    opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    
    col_met1, col_met2 = st.columns(2)
    col_met1.metric("Revenue", f"Rp {smart_format(revenue)}")
    col_met2.metric("Net Profit", f"Rp {smart_format(revenue - opex)}")
    
    with st.expander("Catat Biaya Operasional"):
        with st.form("exp_form"):
            cat = st.selectbox("Kategori", st.session_state.expense_categories)
            nom = st.number_input("Nominal", min_value=0.0)
            if st.form_submit_button("Simpan Biaya"):
                st.session_state.expenses_data.append({"Kategori": cat, "Nominal": nom})
                st.rerun()
    
    if st.session_state.expenses_data:
        st.subheader("History Biaya")
        st.table(pd.DataFrame(st.session_state.expenses_data))
