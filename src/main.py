#!/usr/bin/env python3
#!/usr/bin/env python3
import click
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from pathlib import Path

DB_PATH = Path.home() / ".b2b_niche_finder.db"
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS businesses
                 (id INTEGER PRIMARY KEY, name TEXT, address TEXT, phone TEXT, 
                  industry TEXT, website TEXT, rating REAL, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS analyses
                 (id INTEGER PRIMARY KEY, business_id INTEGER, pain_points TEXT,
                  saas_solution TEXT, roi_data TEXT, scripts TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def fetch_businesses(location: str, industry: str, radius: int = 5000) -> List[Dict]:
    if not GOOGLE_API_KEY:
        return [
            {"name": f"示例{industry}公司A", "address": f"{location}示例街1号", 
             "phone": "010-12345678", "rating": 4.2, "website": "example-a.com"},
            {"name": f"示例{industry}公司B", "address": f"{location}示例街2号", 
             "phone": "010-87654321", "rating": 4.5, "website": "example-b.com"}
        ]
    
    try:
        client = httpx.Client(timeout=30.0)
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_API_KEY}"
        geo_resp = client.get(geocode_url)
        geo_data = geo_resp.json()
        
        if not geo_data.get("results"):
            return []
        
        lat = geo_data["results"][0]["geometry"]["location"]["lat"]
        lng = geo_data["results"][0]["geometry"]["location"]["lng"]
        
        search_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&keyword={industry}&key={GOOGLE_API_KEY}"
        search_resp = client.get(search_url)
        places = search_resp.json().get("results", [])
        
        businesses = []
        for place in places[:10]:
            place_id = place["place_id"]
            detail_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,formatted_phone_number,website,rating&key={GOOGLE_API_KEY}"
            detail_resp = client.get(detail_url)
            detail = detail_resp.json().get("result", {})
            
            businesses.append({
                "name": detail.get("name", ""),
                "address": detail.get("formatted_address", ""),
                "phone": detail.get("formatted_phone_number", ""),
                "rating": detail.get("rating", 0),
                "website": detail.get("website", "")
            })
        
        client.close()
        return businesses
    except Exception as e:
        click.echo(f"抓取失败: {str(e)}", err=True)
        return []

def generate_questionnaire(industry: str) -> str:
    templates = {
        "制造业": "1. 您目前用Excel管理哪些流程？(生产计划/库存/订单)\n2. 每月在Excel上花费多少小时？\n3. 遇到过数据丢失或版本混乱吗？\n4. 多少人同时需要访问这些表格？\n5. 是否需要实时数据同步？",
        "物流": "1. 用Excel跟踪运输订单吗？\n2. 如何处理司机调度和路线规划？\n3. 客户能实时查询货物状态吗？\n4. Excel表格在多个部门间如何共享？\n5. 月均处理多少订单？",
        "default": "1. 哪些业务流程依赖Excel？\n2. 团队规模和协作需求？\n3. 数据量和更新频率？\n4. 当前痛点（效率/错误/协作）？\n5. 预算范围和ROI期望？"
    }
    return templates.get(industry, templates["default"])

def analyze_excel_pain_points(industry: str) -> Dict:
    pain_points = {
        "制造业": ["版本控制混乱", "多人协作冲突", "数据实时性差", "报表生成耗时"],
        "物流": ["订单跟踪滞后", "司机调度低效", "客户查询响应慢", "数据孤岛"],
        "default": ["手动输入错误", "数据分散", "协作困难", "无法移动访问"]
    }
    
    solutions = {
        "制造业": "生产管理SaaS：实时库存看板 + 自动排产 + 移动端审批",
        "物流": "TMS系统：GPS实时追踪 + 智能调度 + 客户自助查询门户",
        "default": "云端协作平台：多人实时编辑 + 权限管理 + API集成"
    }
    
    return {
        "pain_points": pain_points.get(industry, pain_points["default"]),
        "solution": solutions.get(industry, solutions["default"])
    }

def calculate_roi(industry: str, team_size: int = 10) -> Dict:
    hourly_cost = 50
    excel_hours_monthly = team_size * 20
    current_cost = excel_hours_monthly * hourly_cost
    
    saas_monthly_fee = team_size * 30
    time_saved_pct = 0.6
    saved_cost = current_cost * time_saved_pct
    net_benefit = saved_cost - saas_monthly_fee
    payback_months = saas_monthly_fee / net_benefit if net_benefit > 0 else 999
    
    return {
        "current_monthly_cost": current_cost,
        "saas_monthly_fee": saas_monthly_fee,
        "monthly_savings": saved_cost,
        "net_monthly_benefit": net_benefit,
        "payback_months": round(payback_months, 1),
        "annual_roi_pct": round((net_benefit * 12 / (saas_monthly_fee * 12)) * 100, 1)
    }

def generate_outreach_scripts(business_name: str, industry: str, pain_points: List[str]) -> Dict:
    email = f"""主题：帮助{business_name}告别Excel混乱

您好，

注意到贵司在{industry}领域的出色表现。许多同行企业反馈，Excel管理{pain_points[0]}问题严重影响效率。

我们的SaaS方案已帮助类似企业：
• 减少60%数据录入时间
• 消除版本冲突
• 实现移动端实时访问

提供15天免费试用，无需信用卡。方便本周三下午2点简短通话吗？

此致
[您的名字]"""

    phone = f"""话术框架：
1. 开场：您好，我是[公司]的[名字]，专注{industry}数字化
2. 痛点确认：贵司是否用Excel管理[具体流程]？遇到过{pain_points[0]}吗？
3. 价值主张：我们帮[同行案例]节省了X小时/月，ROI回报期3个月
4. 行动召唤：发份产品演示视频到您邮箱，2分钟了解核心功能？
5. 异议处理：
   - "没预算" → 先试用，证明价值后再谈
   - "太忙" → 正因为忙才需要自动化工具
   - "现有方案够用" → 对比下效率提升空间"""

    return {"email": email, "phone_script": phone}

@click.group()
def cli():
    """B2B SaaS机会发现工具"""
    init_db()

@cli.command()
@click.option("--location", prompt="目标城市", help="如：北京/上海")
@click.option("--industry", prompt="行业关键词", help="如：制造业/物流")
@click.option("--radius", default=5000, help="搜索半径(米)")
def scrape(location, industry, radius):
    """抓取本地企业信息"""
    click.echo(f"正在搜索 {location} 的 {industry} 企业...")
    businesses = fetch_businesses(location, industry, radius)
    
    if not businesses:
        click.echo("未找到企业或API配置错误（设置GOOGLE_MAPS_API_KEY环境变量）")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = 0
    for biz in businesses:
        try:
            c.execute("""INSERT INTO businesses (name, address, phone, industry, website, rating, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (biz["name"], biz["address"], biz["phone"], industry, 
                       biz["website"], biz["rating"], datetime.now().isoformat()))
            saved += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    
    click.echo(f"✓ 保存了 {saved} 家企业")
    for biz in businesses[:5]:
        click.echo(f"  • {biz['name']} - {biz['phone']}")

@cli.command()
@click.option("--industry", prompt="行业", help="生成问卷的行业")
def questionnaire(industry):
    """生成痛点调研问卷"""
    questions = generate_questionnaire(industry)
    click.echo(f"\n=== {industry} 痛点调研问卷 ===\n")
    click.echo(questions)
    
    output_file = f"questionnaire_{industry}_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(questions)
    click.echo(f"\n✓ 已保存到 {output_file}")

@cli.command()
@click.option("--business-id", type=int, prompt="企业ID", help="从数据库选择")
@click.option("--industry", prompt="行业", help="企业所属行业")
def analyze(business_id, industry):
    """分析Excel痛点并生成SaaS方案"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM businesses WHERE id=?", (business_id,))
    result = c.fetchone()
    
    if not result:
        click.echo("企业不存在")
        conn.close()
        return
    
    business_name = result[0]
    analysis = analyze_excel_pain_points(industry)
    roi = calculate_roi(industry)
    scripts = generate_outreach_scripts(business_name, industry, analysis["pain_points"])
    
    analysis_data = {
        "pain_points": analysis["pain_points"],
        "solution": analysis["solution"],
        "roi": roi,
        "scripts": scripts
    }
    
    c.execute("""INSERT INTO analyses (business_id, pain_points, saas_solution, roi_data, scripts, created_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (business_id, json.dumps(analysis["pain_points"]), analysis["solution"],
               json.dumps(roi), json.dumps(scripts), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    click.echo(f"\n=== {business_name} 分析报告 ===\n")
    click.echo(f"痛点识别：")
    for p in analysis["pain_points"]:
        click.echo(f"  • {p}")
    click.echo(f"\nSaaS方案：{analysis['solution']}")
    click.echo(f"\nROI计算：")
    click.echo(f"  当前月成本：¥{roi['current_monthly_cost']}")
    click.echo(f"  SaaS月费：¥{roi['saas_monthly_fee']}")
    click.echo(f"  月净收益：¥{roi['net_monthly_benefit']}")
    click.echo(f"  回本周期：{roi['payback_months']}个月")
    click.echo(f"  年化ROI：{roi['annual_roi_pct']}%")

@cli.command()
@click.option("--business-id", type=int, prompt="企业ID")
def scripts(business_id):
    """生成营销话术"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT b.name, b.industry, a.scripts 
                 FROM businesses b 
                 LEFT JOIN analyses a ON b.id = a.business_id 
                 WHERE b.id=?""", (business_id,))
    result = c.fetchone()
    conn.close()
    
    if not result or not result[2]:
        click.echo("请先运行 analyze 命令")
        return
    
    scripts_data = json.loads(result[2])
    click.echo(f"\n=== {result[0]} 营销话术 ===\n")
    click.echo("【邮件模板】")
    click.echo(scripts_data["email"])
    click.echo("\n【电话脚本】")
    click.echo(scripts_data["phone_script"])
    
    output_file = f"scripts_{result[0]}_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"邮件：\n{scripts_data['email']}\n\n电话：\n{scripts_data['phone_script']}")
    click.echo(f"\n✓ 已保存到 {output_file}")

@cli.command()
def list_businesses():
    """列出所有企业"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, industry, phone FROM businesses ORDER BY id DESC LIMIT 20")
    businesses = c.fetchall()
    conn.close()
    
    if not businesses:
        click.echo("暂无企业数据，请先运行 scrape 命令")
        return
    
    click.echo("\n企业列表：")
    for biz in businesses:
        click.echo(f"  [{biz[0]}] {biz[1]} ({biz[2]}) - {biz[3]}")

if __name__ == "__main__":
    cli()