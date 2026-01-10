"""
Clifton's Trading System Dashboard

Main entry point for the Streamlit web interface.
No code reading required - just open the URL and use the interface.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Clifton's Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📈 Systematic Trading Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("System Status")
    st.success("✅ System Online")
    st.info(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    
    st.markdown("---")
    st.header("Quick Navigation")
    st.markdown("""
    - 📋 **Daily Watchlist**: Today's trade signals
    - 📊 **Performance**: Strategy tracking
    - 📚 **Playbooks**: Strategy library
    - 📝 **Trade Journal**: Log your trades
    """)

# Main content area
st.header("Welcome to Your Trading System")

st.markdown("""
### System Overview

This dashboard provides a clean interface to:

1. **View Daily Signals** - See which setups triggered today
2. **Track Performance** - Monitor live vs backtested results
3. **Access Playbooks** - Review your strategy rules
4. **Log Trades** - Record entries and exits

---

### Current Status

**📊 Active Playbooks:** 0 (Add your first strategy!)  
**🎯 Today's Signals:** 0 (System needs configuration)  
**📈 Total Trades Logged:** 0

---

### Next Steps

1. Add your first trading playbook to `/strategies`
2. Configure signal generation script
3. Set up automated data updates
4. Start logging trades!

---

*System built with: Python, Streamlit, yfinance, GitHub Actions*  
*Maintained by: AI agents (90%) + Strategic direction (10%)*
""")

# Footer
st.markdown("---")
st.caption("Clifton's Systematic Trading System | Powered by AI Infrastructure")
