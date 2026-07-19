# 📊 RRG Pro - Private Relative Rotation Graphs Dashboard

An institutional-grade, fully customizable Relative Rotation Graph (RRG) tool built with **Streamlit** and **Python**. This allows you to track and analyze sector rotation for Indian Markets (NSE), US S&P 500, Cryptocurrencies, or custom watchlists for **100% free**, bypassing expensive financial terminal subscriptions (such as Bloomberg, StockCharts, or Strike.money).

---

## ✨ Features
1. **Live Data-Driven RRG Chart:** Fetches real-time market data from Yahoo Finance and calculates JdK-style RS-Ratio and RS-Momentum on the fly.
2. **Interactive Plotly Visualization:** A beautiful scatter plot with colored quadrant sectors, customizable smoothing windows, lookbacks, and dynamic trails.
3. **Download RRG Standings:** One-click CSV exporter to save the latest relative strength metrics.
4. **Embedded High-Fidelity Landing Page:** Includes the premium, responsive Strike.money integration landing page inside the dashboard.
5. **Completely Free Hosting:** Designed to run seamlessly on Streamlit Community Cloud or locally.

---

## 🚀 Local Installation & Setup

To run this dashboard on your local computer, follow these simple steps:

### 1. Clone or Download this Project
Download all files inside a directory (e.g., `rrg-dashboard`). Ensure you have the following files inside:
* `app.py` (The Streamlit application code)
* `strike_money_rrg_partner.html` (The high-fidelity responsive landing page)
* `requirements.txt` (List of Python dependencies)

### 2. Install Dependencies
Open your terminal/command prompt, navigate to your project folder, and run:
```bash
pip install -r requirements.txt
```

### 3. Start the Dashboard
Launch the Streamlit server locally:
```bash
streamlit run app.py
```
This will automatically open the dashboard in your default web browser (usually at `http://localhost:8501`).

---

## ☁️ Deploy to GitHub & Streamlit Cloud (100% Free)

You can host this dashboard privately or publicly online so that you can access it from your phone, tablet, or laptop anytime.

### Step 1: Upload to GitHub
1. Go to [GitHub](https://github.com/) and create a new repository (you can set it to **Private**).
2. Upload these three files directly to your repository:
   * `app.py`
   * `strike_money_rrg_partner.html`
   * `requirements.txt`

### Step 2: Connect to Streamlit Cloud
1. Go to [Streamlit Community Cloud](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **New app**.
3. Select your repository, branch (`main` or `master`), and specify the Main file path as `app.py`.
4. Click **Deploy!**

Your professional, interactive Relative Rotation Graph dashboard will be live on a shareable URL in less than 2 minutes!

---

## 📖 Mathematical Formula Used
This dashboard employs the industry-standard **JdK Index Model** for mapping relative rotation:

1. **Relative Strength (RS):**
   $$RS_t = \frac{\text{Price of Asset}_t}{\text{Price of Benchmark}_t} \times 100$$

2. **RS-Ratio (Relative Strength Normalized):**
   $$RS\_Ratio_t = 100 + \left( \frac{RS_t - \text{Rolling Mean}(RS_t, n)}{\text{Rolling StdDev}(RS_t, n)} \right) \times 10$$

3. **RS-Momentum (Momentum of Relative Strength):**
   $$RS\_Momentum_t = 100 + \left( \frac{\text{ROC}(RS\_Ratio_t, 1) - \text{Rolling Mean}(\text{ROC}, n)}{\text{Rolling StdDev}(\text{ROC}, n)} \right) \times 10$$

*Where $n$ represents the user-selected Smoothing Window.*
