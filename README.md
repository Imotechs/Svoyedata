# 🏦 Svoye Zhil’ye Mortgage & Banking Analytics Platform

> **Automated data integration and analytics system** for aggregating, analyzing, and visualizing mortgage-related statistics from the **Central Bank of Russia (CBR)**.

---

## Overview

**Svoye Zhil’ye Analytics** is a full-stack data platform that automatically collects, stores, and visualizes analytical data from the **Bank of Russia**.  
It powers the “Analytics” section of the Svoye Zhil’ye portal, allowing citizens, analysts, and institutions to explore trends in mortgage lending and the banking sector across all Russian regions.

The system supports:
- Automatic monthly data fetching from the **CBR mortgage statistics**.
- Structured database storage with regional and metric granularity.
- REST API endpoints for accessing and aggregating data.
- An interactive **React.js dashboard** for visual analytics (charts, maps, and tables).

---


| Component | Description |
|------------|-------------|
| **FastAPI backend** | Handles scheduled fetching, parsing, and serving of mortgage data via REST APIs. |
| **Pandas + BeautifulSoup + HTTPX** | Used to fetch and parse XLSX files directly from CBR’s website. |
| **SQLAlchemy ORM** | Defines models for Regions, Metrics, and MetricValues with relationships. |
| **PostgreSQL** | Stores all parsed mortgage analytics data for historical and regional comparison. |
| **React.js (MUI + Recharts)** | Presents an interactive analytics dashboard for users to visualize data trends. |
| **Scheduler** | Automatically triggers monthly updates to keep analytics up-to-date. |

---

## Key Features

### Automated Data Collection
- Dynamically locates and downloads XLSX reports from the **CBR mortgage portal**.
- Parses and normalizes headers (via a flexible `HEADER_MAP`).
- Detects regions and federal districts automatically.
- Stores cleaned, structured data into the database.

### Powerful API Layer
- `/api/v1/cbr/data` — Query data by region, metric, or date.  
- `/api/v1/cbr/metrics` — Get all available metrics with units.  
- `/api/v1/cbr/regions` — Retrieve all known regions.  
- `/api/v1/cbr/trend/{metric_key}` — View historical trends for a given metric.  
- `/api/v1/cbr/fetch` — Trigger a manual re-fetch for a specific month/year.

###  Intelligent Scheduler
- Background job automatically fetches new data at the start of each month.
- Ensures the analytics remain continuously up-to-date without manual intervention.

### Interactive Frontend Dashboard
Built with **React**, **MUI**, **Recharts**, and **React Query**:
- Dropdown filters for regions and metrics.
- Trend charts showing historical changes.
- Summary cards with key insights.
- Interactive tables with search and sort.
- Responsive design suitable for all devices.

---

## Getting Started

### Backend Setup
```bash
git clone https://github.com/yourusername/svoyedata.git
cd SvoyeData
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

