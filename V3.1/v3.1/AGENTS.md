# OpenShop LIFE Agent Guide

本專案只有一個主要 Skill（`SKILL.md`）與三位分工角色。**順序依老師提供的 SKILL.md 固定：**

1. Agent 1 市場分析：讀取使用者資料、檢查缺值與來源、候選地點情境排行，輸出 `01_market_report.json`。
2. Agent 2 法規合規：讀取第一角色的店型與地區；列出需要主管機關確認的事項，輸出 `02_legal_checklist.json`。
3. Agent 3 程序及審查：讀取前二者、編排開店流程、預算與風險稽核，輸出 `03_store_opening_plan.md` 和 `04_audit.json`。

六個互動主題（法規、員工、經營、地點、外送、內外帶）是產品模組，**不是宣稱六位獨立 AI 角色已自動啟動**。Web UI 的 Python 運行是流程展示，不能取代 AI Skill 的 A/B/C 自動啟動證據。
