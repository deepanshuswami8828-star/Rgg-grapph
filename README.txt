PVR INOX RRG app (PVR INOX against NIFTY 50, daily / weekly / both)
====================================================================

Start it
  Double-click "Start RRG App.bat" (or the "PVR INOX RRG" icon on the Desktop).
  The app opens in the browser at http://localhost:8501.
  Keep the small black window open while using it; closing it stops the app.

Files
  rrg_app.py              the app (charts, slider, cycles, tables)
  make_rrg_pvrinox.py     the RRG formula the app uses (RS-Ratio, RS-Momentum)
  Start RRG App.bat       launcher
  .streamlit/config.toml  keeps the app in the light theme
  requirements.txt        Python packages the app needs
  *.csv                   offline fallback prices, used only if Yahoo Finance
                          cannot be reached (they end on 13 Aug 2026)

Formula
  RS-Ratio    = 100 x EMA(SMA(RS,5),5) / EMA(SMA(RS,5),30)
  RS-Momentum = 100 x EMA(RS-Ratio,3) / EMA(RS-Ratio,14)
  RS = PVR INOX close / NIFTY 50 close. Weekly uses each week's last close.

On another computer
  Install Python, then in this folder run:
      python -m pip install -r requirements.txt
      python -m streamlit run rrg_app.py
  (The .bat file points at this computer's Python; on another computer it falls
  back to "python" on the PATH.)
