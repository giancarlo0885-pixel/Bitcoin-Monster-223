# Garibaldi Crypto Prediction Bot

Railway-ready Streamlit app.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Railway deploy
1. Upload these extracted files to GitHub repository root.
2. On Railway, create a new service from GitHub.
3. Railway should detect Python.
4. Start command:
```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

This is educational software, not financial advice and not an automated trading system.
