# Clifton's Systematic Trading System

Autonomous trading signal generation system powered by book-tested playbooks.

## System Overview

This repository houses a complete systematic trading infrastructure that:
- Stores historical market data
- Implements multiple trading playbooks from respected authors
- Generates daily trade signals automatically
- Provides a clean dashboard interface (no code reading required)
- Tracks performance vs backtested expectations

## Folder Structure
```
Trading-System/
├── data/                          # Historical price data & daily signals
│   ├── historical/                # Stored price data (CSV files)
│   ├── signals/                   # Daily generated signals
│   └── trades/                    # Trade journal entries
│
├── strategies/                    # Playbook definitions from trading books
│   ├── playbook_template.py       # Template for new strategies
│   └── [individual strategy files]
│
├── scripts/                       # Automation & analysis code
│   ├── backtesting/               # Backtest engines
│   ├── signal_generation/         # Daily signal generators
│   └── data_management/           # Data download & storage
│
├── dashboard/                     # Streamlit web interface
│   ├── app.py                     # Main dashboard application
│   └── pages/                     # Individual dashboard pages
│
├── .github/                       # GitHub Actions automation
│   └── workflows/                 # Automated daily tasks
│
└── requirements.txt               # Python dependencies
```

## Daily Workflow

**Automated (runs at 6 AM EST):**
1. Download latest market data
2. Run all playbook filters
3. Generate signals CSV
4. Update dashboard

**Your Input (5 minutes):**
1. Check dashboard for today's setups
2. Review which playbooks are active
3. Execute trades that match your criteria

## Strategy Sources

Playbooks implemented from:
- [Book 1 - to be added]
- [Book 2 - to be added]
- [Book 3 - to be added]

## Setup Instructions

[To be added as system is built]

---

Built with: Python, yfinance, Streamlit, GitHub Actions
Maintained by: AI agents (90%) + Clifton (10% strategic direction)
```

   - Commit this file

---

### **Step 2: Add Subfolders to Data Directory**

Now create the data subfolders:

1. `data/historical/.gitkeep`
2. `data/signals/.gitkeep`
3. `data/trades/.gitkeep`

---

### **Step 3: Create Initial Template Files**

Let's add some starter files so the structure is ready to use:

#### **A. Create requirements.txt** (Python dependencies)

Create new file: `requirements.txt`
```
# Core Data & Analysis
pandas==2.1.4
numpy==1.26.2
yfinance==0.2.33

# Visualization
matplotlib==3.8.2
plotly==5.18.0

# Dashboard
streamlit==1.29.0

# Backtesting
vectorbt==0.26.0

# Utilities
python-dateutil==2.8.2
pytz==2023.3
