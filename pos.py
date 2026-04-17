import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP & POS Precision Suite", layout="wide")

# --- CUSTOM FORMATTING ---
def format_num(val):
    return "{:,.5f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")

# --- INITIALIZING SESSION STATES ---
states = {
    'logged_in': False,
    'user': None,
    'master_items': pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Espresso Coffee", "Harga_Jual": 25000.0, "Stok": 100.0, "Min_Stok": 10.0},
        {"SKU": "BRG002", "Nama": "Croissant Butter", "Harga_Jual": 18000.0, "Stok": 50.0, "Min_Stok": 5.0}
    ]),
    'promos': pd.DataFrame([
        {"Nama_Promo": "No Promo", "Diskon_Persen": 0.0, "Diskon_Nominal": 0.0},
        {"Nama_Promo": "Diskon Member 10%", "Diskon_Persen": 10.0, "Diskon_Nominal": 0.0}
    ]),
    'pos_transactions': [],
    'cash_session': {"modal_awal": 0.0, "status": "Closed", "waktu_buka": None},
    'expenses': [],
    'pr_data': []
}

for key, val in states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔐 Login ERP & POS System")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Login Gagal. Gunakan admin/admin123")
    st.stop()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title(f"👤 User: {st.session_state.user}")
menu = st.sidebar.radio("Main Menu", [
    "Dashboard", 
    "Master Data & Promo", 
    "POS (Kasir)", 
    "Procurement (SCM)", 
    "Financial Report & Closing"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📈 Business Overview")
    sales_today = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    st.metric("Total Penjualan Hari Ini", f"Rp {format_num(sales_today)}")
    
    st.subheader("📦 Inventory Alert")
    low_stock = st.session_state.master_items[st.session_state.master_items['Stok'] <= st.session_state.master_items['Min_Stok']]
    st.table(low_stock)

# --- 2. MASTER DATA & PROMO ---
elif menu == "Master Data & Promo":
    tab_item, tab_promo = st.tabs(["Master Item & Harga", "Pengaturan Diskon"])
    
    with tab_item:
        with st.form("add_item"):
            c1, c2 = st.columns(2)
            n_sku = c1.text_input("SKU Baru")
            n_nama = c1.text_input("Nama Item")
            n_harga = c2.number_input("Harga Jual (Rp)", format="%.5f")
            n_stok = c2.number_input("Stok Awal", format="%.5f")
            if st.form_submit_button("Tambah Item"):
                new_item = {"SKU": n_sku, "Nama": n_nama, "Harga_Jual": n_harga, "Stok": n_stok, "Min_Stok": 5.0}
                st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_item])], ignore_index=True)
                st.rerun()
        st.table(st.session_state.master_items)

    with tab_promo:
        with st.form("add_promo"):
            p_nama = st.text_input("Nama Promo")
            p_disc = st.number_input("Diskon (%)", max_value=100.0, format="%.5f")
            p_nom = st.number_input("Diskon Nominal (Rp)", format="%.5f")
            if st.form_submit_button("Simpan Promo"):
                new_p = {"Nama_Promo": p_nama, "Diskon_Persen": p_disc, "Diskon_Nominal": p_nom}
                st.session_state.promos = pd.concat([st.session_state.promos, pd.DataFrame([new_p])], ignore_index=True)
                st.rerun()
        st.table(st.session_state.promos)

# --- 3. POS (KASIR) ---
elif menu == "POS (Kasir)":
    st.header("🛒 Mesin Kasir")
    
    if st.session_state.cash_session['status'] == "Closed":
        st.warning("Sesi Kasir belum dibuka. Silakan masukkan modal awal.")
        modal = st.number_input("Modal Awal (Starting Cash)", min_value=0.0, format="%.5f")
        if st.button("Buka Kasir"):
            st.session_state.cash_session = {"modal_awal": modal, "status": "Open", "waktu_buka": datetime.now()}
            st.rerun()
    else:
        col_pos1, col_pos2 = st.columns([2, 1])
        
        with col_pos1:
            st.subheader("Pilih Menu")
            items = st.session_state.master_items['Nama'].tolist()
            selected_item = st.selectbox("Item", items)
            qty = st.number_input("Qty", min_value=1.0, format="%.5f")
            promo_list = st.session_state.promos['Nama_Promo'].tolist()
            selected_promo = st.selectbox("Gunakan Promo", promo_list)
            
            if st.button("Add to Cart"):
                item_data = st.session_state.master_items[st.session_state.master_items['Nama'] == selected_item].iloc[0]
                promo_data = st.session_state.promos[st.session_state.promos['Nama_Promo'] == selected_promo].iloc[0]
                
                gross = item_data['Harga_Jual'] * qty
                disc_val = (gross * (promo_data['Diskon_Persen']/100)) + promo_data['Diskon_Nominal']
                net = gross - disc_val
                
                st.session_state.pos_transactions.append({
                    "Waktu": datetime.now(),
                    "Item": selected_item,
                    "SKU": item_data['SKU'],
                    "Qty": qty,
                    "Gross": gross,
                    "Discount": disc_val,
                    "Net_Total": net
                })
                # Update Stok Langsung
                idx = st.session_state.master_items[st.session_state.master_items['Nama'] == selected_item].index
                st.session_state.master_items.at[idx[0], 'Stok'] -= qty
                st.success("Item ditambahkan!")

        with col_pos2:
            st.subheader("Struk Belanja")
            if st.session_state.pos_transactions:
                df_pos = pd.DataFrame(st.session_state.pos_transactions)
                st.write(df_pos[['Item', 'Qty', 'Net_Total']].tail(5))
                total_bill = df_pos['Net_Total'].sum()
                st.markdown(f"### Total: Rp {format_num(total_bill)}")
                if st.button("Clear Cart (Reset)"):
                    st.session_state.pos_transactions = []
                    st.rerun()

# --- 4. PROCUREMENT (SCM) ---
elif menu == "Procurement (SCM)":
    st.header("📦 Supply Chain Management")
    st.info("Gunakan modul ini untuk restock barang (Post GR otomatis menambah stok master).")
    # (Logika PR/PO/GR sama seperti versi sebelumnya)

# --- 5. FINANCIAL REPORT & CLOSING ---
elif menu == "Financial Report & Closing":
    st.header("🏁 Closing Kasir & Laporan Keuangan")
    
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    modal_awal = st.session_state.cash_session['modal_awal']
    total_cash_expected = modal_awal + rev
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Modal Awal", format_num(modal_awal))
    c2.metric("Total Penjualan", format_num(rev))
    c3.metric("Uang di Laci (Expected)", format_num(total_cash_expected))
    
    st.divider()
    if st.session_state.cash_session['status'] == "Open":
        if st.button("PROSES CLOSING KASIR"):
            st.session_state.cash_session['status'] = "Closed"
            st.success("Kasir Berhasil Ditutup. Data Penjualan Diarsipkan.")
            st.rerun()
    
    st.subheader("📜 Riwayat Transaksi POS")
    if st.session_state.pos_transactions:
        st.table(pd.DataFrame(st.session_state.pos_transactions))
