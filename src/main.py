#!/usr/bin/env python3
#!/usr/bin/env python3
import click
import sqlite3
import json
import re
from datetime import datetime
from pathlib import Path
import requests
from typing import List, Dict

DB_PATH = Path.home() / ".b2b_validator.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pain_points
                 (id INTEGER PRIMARY KEY, industry TEXT, pain_point TEXT, 
                  excel_workflow TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY, business_name TEXT, industry TEXT,
                  address TEXT, phone TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS solutions
                 (id INTEGER PRIMARY KEY, pain_point_id INTEGER, solution TEXT,
                  monthly_price INTEGER, roi_months INTEGER, created_at TEXT)''')
    conn.commit()
    conn.close()

@click.group()
def cli():
    """B2B SaaS Validator - 从B2C转向B2B机会"""
    init_db()

@cli.command()
@click.option('--industry', prompt='目标行业', help='如：水管工、物流、仓储')
def discover_pain(industry):
    """发现企业痛点"""
    pain_points = {
        '水管工': [
            '手动Excel记录客户预约，经常重复预订',
            '纸质工单管理，库存盘点耗时3小时/周',
            '员工调度用WhatsApp群组，效率低下'
        ],
        '物流': [
            'Excel追踪货物状态，客户频繁电话询问',
            '手动计算运费，报价错误率15%',
            '司机路线规划靠经验，油耗浪费20%'
        ],
        '仓储': [
            '库存盘点用Excel，年度盘点需停业2天',
            '出入库手工记录，月底对账差异率8%',
            '货位管理混乱，拣货时间是行业平均2倍'
        ],
        '餐饮': [
            'Excel管理供应商订单，缺货率12%',
            '员工排班表手动制作，每周耗时5小时',
            '会员积分Excel记录，客诉纠纷多'
        ]
    }
    
    points = pain_points.get(industry, ['未找到该行业数据，请尝试：水管工、物流、仓储、餐饮'])
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for p in points:
        c.execute('INSERT INTO pain_points (industry, pain_point, excel_workflow, created_at) VALUES (?, ?, ?, ?)',
                  (industry, p, 'Excel手动操作', datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    click.echo(f'\n✓ 发现 {industry} 行业痛点：')
    for i, p in enumerate(points, 1):
        click.echo(f'{i}. {p}')

@cli.command()
@click.argument('pain_point_id', type=int)
def analyze_workflow(pain_point_id):
    """分析Excel工作流"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT industry, pain_point FROM pain_points WHERE id=?', (pain_point_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        click.echo('痛点ID不存在')
        return
    
    industry, pain = row
    analysis = {
        '当前流程': '手动Excel录入 → 人工核对 → 纸质归档',
        '时间成本': '每周15-25小时',
        '错误率': '8-15%',
        '可自动化': '85%',
        'SaaS替代': f'简化为：自动录入 → 实时同步 → 云端存储'
    }
    
    click.echo(f'\n【{industry}】工作流分析：')
    click.echo(f'痛点：{pain}\n')
    for k, v in analysis.items():
        click.echo(f'{k}: {v}')

@cli.command()
@click.argument('pain_point_id', type=int)
@click.option('--price', default=200, help='月费（美元）')
def calculate_roi(pain_point_id, price):
    """计算ROI"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT pain_point FROM pain_points WHERE id=?', (pain_point_id,))
    row = c.fetchone()
    
    if not row:
        click.echo('痛点ID不存在')
        conn.close()
        return
    
    # 简化ROI计算
    time_saved_hours = 20  # 每月节省小时
    hourly_rate = 25  # 员工时薪
    monthly_saving = time_saved_hours * hourly_rate
    roi_months = round(price / (monthly_saving - price), 1)
    
    solution = f'自动化工具替代Excel，月费${price}'
    c.execute('INSERT INTO solutions (pain_point_id, solution, monthly_price, roi_months, created_at) VALUES (?, ?, ?, ?, ?)',
              (pain_point_id, solution, price, roi_months, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    click.echo(f'\nROI计算：')
    click.echo(f'月费：${price}')
    click.echo(f'月节省：${monthly_saving}（{time_saved_hours}小时 × ${hourly_rate}/小时）')
    click.echo(f'净收益：${monthly_saving - price}/月')
    click.echo(f'回本周期：{roi_months}个月')
    click.echo(f'\n80客户年收入：${price * 80 * 12:,}')

@cli.command()
@click.option('--industry', prompt='行业关键词', help='如：plumber、logistics')
@click.option('--location', prompt='城市', help='如：San Francisco')
@click.option('--limit', default=10, help='抓取数量')
def find_leads(industry, location, limit):
    """生成本地企业线索（Google Maps API模拟）"""
    # 实际使用需Google Maps API key，这里用模拟数据
    click.echo(f'\n正在搜索 {location} 的 {industry} 企业...')
    
    mock_leads = [
        {'name': f'{industry.title()} Pro #{i}', 'address': f'{i*100} Main St, {location}', 
         'phone': f'(555) {i:03d}-{i*11:04d}'} 
        for i in range(1, limit + 1)
    ]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for lead in mock_leads:
        c.execute('INSERT INTO leads (business_name, industry, address, phone, created_at) VALUES (?, ?, ?, ?, ?)',
                  (lead['name'], industry, lead['address'], lead['phone'], datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    click.echo(f'\n✓ 已保存 {len(mock_leads)} 条线索：')
    for lead in mock_leads[:5]:
        click.echo(f"  • {lead['name']} - {lead['phone']}")
    if len(mock_leads) > 5:
        click.echo(f'  ... 还有 {len(mock_leads) - 5} 条')

@cli.command()
@click.argument('lead_id', type=int)
@click.option('--solution-id', type=int, prompt='解决方案ID')
def generate_email(lead_id, solution_id):
    """生成外联邮件"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT business_name, industry FROM leads WHERE id=?', (lead_id,))
    lead = c.fetchone()
    c.execute('SELECT solution, monthly_price, roi_months FROM solutions WHERE id=?', (solution_id,))
    solution = c.fetchone()
    conn.close()
    
    if not lead or not solution:
        click.echo('ID不存在')
        return
    
    email = f"""主题：帮助 {lead[0]} 每月节省20小时

您好，

我注意到许多{lead[1]}企业仍在用Excel管理日常运营。我们开发了一个简单工具，可以：

• 自动化您的{lead[1]}工作流
• 每月节省20+小时人工时间
• {solution[2]}个月内回本

定价：${solution[1]}/月（无隐藏费用）

可以安排15分钟演示吗？

最好的问候
"""
    
    click.echo(f'\n{email}')
    
    # 保存到文件
    email_file = Path(f'email_lead_{lead_id}.txt')
    email_file.write_text(email)
    click.echo(f'\n✓ 已保存到 {email_file}')

@cli.command()
@click.option('--target-customers', default=80, help='目标客户数')
@click.option('--monthly-price', default=200, help='月费')
def pricing_calc(target_customers, monthly_price):
    """定价计算器"""
    annual_revenue = target_customers * monthly_price * 12
    
    click.echo(f'\n定价模型：')
    click.echo(f'月费：${monthly_price}')
    click.echo(f'目标客户：{target_customers}')
    click.echo(f'年收入：${annual_revenue:,}')
    click.echo(f'\n建议定价范围：')
    for price in [100, 150, 200, 300, 500]:
        revenue = target_customers * price * 12
        click.echo(f'  ${price}/月 → ${revenue:,}/年')

@cli.command()
def mvp_builder():
    """MVP构建指南"""
    mvp = {
        '第1周': '用户调研 - 访谈5个目标客户',
        '第2周': '核心功能 - 实现最关键的1个自动化',
        '第3周': '极简UI - Streamlit/Gradio快速原型',
        '第4周': '测试部署 - 给3个beta客户试用',
        '技术栈': 'Python + SQLite + Streamlit',
        '成本': '<$100（域名+托管）'
    }
    
    click.echo('\nMVP构建路线图：')
    for k, v in mvp.items():
        click.echo(f'{k}: {v}')

@cli.command()
def list_data():
    """查看所有数据"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    click.echo('\n=== 痛点 ===')
    for row in c.execute('SELECT id, industry, pain_point FROM pain_points ORDER BY id DESC LIMIT 10'):
        click.echo(f'[{row[0]}] {row[1]}: {row[2]}')
    
    click.echo('\n=== 线索 ===')
    for row in c.execute('SELECT id, business_name, phone FROM leads ORDER BY id DESC LIMIT 10'):
        click.echo(f'[{row[0]}] {row[1]} - {row[2]}')
    
    click.echo('\n=== 解决方案 ===')
    for row in c.execute('SELECT id, solution, monthly_price FROM solutions ORDER BY id DESC LIMIT 10'):
        click.echo(f'[{row[0]}] {row[1]} (${row[2]}/月)')
    
    conn.close()

if __name__ == '__main__':
    cli()