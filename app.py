from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_migrate import Migrate  
import os
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 直接初始化 SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # 添加这一行  # 确保在运行 Flask 命令时能够正确加载应用上下文

# 定义数据模型
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    type = db.Column(db.String(10), nullable=False)  # 'income' 或 'expense'
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50))  # 添加二级分类字段
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))

@app.route('/')
def index():
    # 获取所有年份和月份
    years = sorted(set(t.date.year for t in Transaction.query.all()), reverse=True)
    months = range(1, 13)
    
    # 获取筛选条件
    selected_year = request.args.get('year', datetime.now().year)
    selected_month = request.args.get('month', datetime.now().month)
    
    try:
        selected_year = int(selected_year)
        selected_month = int(selected_month)
    except (ValueError, TypeError):
        selected_year = datetime.now().year
        selected_month = datetime.now().month
    
    # 获取所有交易记录
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    
    # 筛选指定年月的交易记录
    filtered_transactions = []
    for transaction in transactions:
        if transaction.date.year == selected_year and transaction.date.month == selected_month:
            filtered_transactions.append(transaction)
    
    # 筛选指定年的交易记录（用于年度统计）
    yearly_transactions = []
    for transaction in transactions:
        if transaction.date.year == selected_year:
            yearly_transactions.append(transaction)
    
    # 准备月度饼状图数据 - 按一级分类
    income_data = {}
    expense_data = {}
    
    # 准备月度饼状图数据 - 按二级分类
    income_subcategory_data = {}
    expense_subcategory_data = {}
    
    # 准备年度饼状图数据 - 按一级分类
    yearly_income_data = {}
    yearly_expense_data = {}
    
    # 准备年度饼状图数据 - 按二级分类
    yearly_income_subcategory_data = {}
    yearly_expense_subcategory_data = {}
    
    # 处理月度数据
    for transaction in filtered_transactions:
        if transaction.type == 'income':
            # 一级分类数据
            if transaction.category in income_data:
                income_data[transaction.category] += transaction.amount
            else:
                income_data[transaction.category] = transaction.amount
                
            # 二级分类数据
            if transaction.subcategory:
                subcat_key = f"{transaction.category}-{transaction.subcategory}"
                if subcat_key in income_subcategory_data:
                    income_subcategory_data[subcat_key] += transaction.amount
                else:
                    income_subcategory_data[subcat_key] = transaction.amount
        else:
            # 一级分类数据
            if transaction.category in expense_data:
                expense_data[transaction.category] += transaction.amount
            else:
                expense_data[transaction.category] = transaction.amount
                
            # 二级分类数据
            if transaction.subcategory:
                subcat_key = f"{transaction.category}-{transaction.subcategory}"
                if subcat_key in expense_subcategory_data:
                    expense_subcategory_data[subcat_key] += transaction.amount
                else:
                    expense_subcategory_data[subcat_key] = transaction.amount
    
    # 处理年度数据
    for transaction in yearly_transactions:
        if transaction.type == 'income':
            # 一级分类数据
            if transaction.category in yearly_income_data:
                yearly_income_data[transaction.category] += transaction.amount
            else:
                yearly_income_data[transaction.category] = transaction.amount
                
            # 二级分类数据
            if transaction.subcategory:
                subcat_key = f"{transaction.category}-{transaction.subcategory}"
                if subcat_key in yearly_income_subcategory_data:
                    yearly_income_subcategory_data[subcat_key] += transaction.amount
                else:
                    yearly_income_subcategory_data[subcat_key] = transaction.amount
        else:
            # 一级分类数据
            if transaction.category in yearly_expense_data:
                yearly_expense_data[transaction.category] += transaction.amount
            else:
                yearly_expense_data[transaction.category] = transaction.amount
                
            # 二级分类数据
            if transaction.subcategory:
                subcat_key = f"{transaction.category}-{transaction.subcategory}"
                if subcat_key in yearly_expense_subcategory_data:
                    yearly_expense_subcategory_data[subcat_key] += transaction.amount
                else:
                    yearly_expense_subcategory_data[subcat_key] = transaction.amount
    
    # 计算月度总收入和总支出
    total_income = sum(income_data.values())
    total_expense = sum(expense_data.values())
    
    # 计算年度总收入和总支出
    yearly_total_income = sum(yearly_income_data.values())
    yearly_total_expense = sum(yearly_expense_data.values())
    
    return render_template('index.html', 
                          transactions=transactions,
                          filtered_transactions=filtered_transactions,
                          years=years,
                          months=months,
                          selected_year=selected_year,
                          selected_month=selected_month,
                          income_data=income_data,
                          expense_data=expense_data,
                          income_subcategory_data=income_subcategory_data,
                          expense_subcategory_data=expense_subcategory_data,
                          total_income=total_income,
                          total_expense=total_expense,
                          yearly_income_data=yearly_income_data,
                          yearly_expense_data=yearly_expense_data,
                          yearly_income_subcategory_data=yearly_income_subcategory_data,
                          yearly_expense_subcategory_data=yearly_expense_subcategory_data,
                          yearly_total_income=yearly_total_income,
                          yearly_total_expense=yearly_total_expense)

@app.route('/income')
def income():
    # 获取所有年份和月份
    years = sorted(set(t.date.year for t in Transaction.query.filter_by(type='income').all()), reverse=True)
    months = range(1, 13)
    
    # 获取筛选条件
    selected_year = request.args.get('year', datetime.now().year)
    selected_month = request.args.get('month', datetime.now().month)
    selected_category = request.args.get('category', '')
    selected_subcategory = request.args.get('subcategory', '')
    
    try:
        selected_year = int(selected_year)
        selected_month = int(selected_month)
    except (ValueError, TypeError):
        selected_year = datetime.now().year
        selected_month = datetime.now().month
    
    # 获取所有收入记录
    transactions = Transaction.query.filter_by(type='income').order_by(Transaction.date.desc()).all()
    
    # 筛选指定年月的交易记录
    filtered_transactions = []
    for transaction in transactions:
        if transaction.date.year == selected_year and transaction.date.month == selected_month:
            # 如果选择了类别，则进行筛选
            if selected_category and transaction.category != selected_category:
                continue
            # 如果选择了二级分类，则进行筛选
            if selected_subcategory and transaction.subcategory != selected_subcategory:
                continue
            filtered_transactions.append(transaction)
    
    # 按年份和月份分组
    grouped_transactions = {}
    for transaction in filtered_transactions:
        year_month = transaction.date.strftime('%Y-%m')
        if year_month not in grouped_transactions:
            grouped_transactions[year_month] = []
        grouped_transactions[year_month].append(transaction)
    
    # 获取所有可用的类别和二级分类
    all_categories = sorted(set(t.category for t in Transaction.query.filter_by(type='income').all()))
    all_subcategories = sorted(set(t.subcategory for t in Transaction.query.filter_by(type='income').all() if t.subcategory))
    
    return render_template('income.html', 
                          grouped_transactions=grouped_transactions,
                          years=years,
                          months=months,
                          selected_year=selected_year,
                          selected_month=selected_month,
                          all_categories=all_categories,
                          all_subcategories=all_subcategories,
                          selected_category=selected_category,
                          selected_subcategory=selected_subcategory)

@app.route('/expense')
def expense():
    # 获取所有年份和月份
    years = sorted(set(t.date.year for t in Transaction.query.filter_by(type='expense').all()), reverse=True)
    months = range(1, 13)
    
    # 获取筛选条件
    selected_year = request.args.get('year', datetime.now().year)
    selected_month = request.args.get('month', datetime.now().month)
    selected_category = request.args.get('category', '')
    selected_subcategory = request.args.get('subcategory', '')
    
    try:
        selected_year = int(selected_year)
        selected_month = int(selected_month)
    except (ValueError, TypeError):
        selected_year = datetime.now().year
        selected_month = datetime.now().month
    
    # 获取所有支出记录
    transactions = Transaction.query.filter_by(type='expense').order_by(Transaction.date.desc()).all()
    
    # 筛选指定年月的交易记录
    filtered_transactions = []
    for transaction in transactions:
        if transaction.date.year == selected_year and transaction.date.month == selected_month:
            # 如果选择了类别，则进行筛选
            if selected_category and transaction.category != selected_category:
                continue
            # 如果选择了二级分类，则进行筛选
            if selected_subcategory and transaction.subcategory != selected_subcategory:
                continue
            filtered_transactions.append(transaction)
    
    # 计算当月总支出
    monthly_total = sum(t.amount for t in filtered_transactions)
    
    # 计算当年总支出
    yearly_transactions = [t for t in transactions if t.date.year == selected_year]
    yearly_total = sum(t.amount for t in yearly_transactions)
    
    # 计算各类别占比
    category_stats = {}
    subcategory_stats = {}
    
    # 计算各类别的金额和占比
    for transaction in filtered_transactions:
        # 处理类别统计
        if transaction.category in category_stats:
            category_stats[transaction.category]['amount'] += transaction.amount
        else:
            category_stats[transaction.category] = {
                'amount': transaction.amount,
                'transactions': []
            }
        category_stats[transaction.category]['transactions'].append(transaction)
        
        # 处理二级类别统计
        if transaction.subcategory:
            subcat_key = f"{transaction.category}-{transaction.subcategory}"
            if subcat_key in subcategory_stats:
                subcategory_stats[subcat_key]['amount'] += transaction.amount
            else:
                subcategory_stats[subcat_key] = {
                    'amount': transaction.amount,
                    'category': transaction.category,
                    'subcategory': transaction.subcategory,
                    'transactions': []
                }
            subcategory_stats[subcat_key]['transactions'].append(transaction)
    
    # 计算百分比
    for category, data in category_stats.items():
        data['monthly_percentage'] = (data['amount'] / monthly_total * 100) if monthly_total > 0 else 0
        data['yearly_percentage'] = (data['amount'] / yearly_total * 100) if yearly_total > 0 else 0
    
    for subcat_key, data in subcategory_stats.items():
        data['monthly_percentage'] = (data['amount'] / monthly_total * 100) if monthly_total > 0 else 0
        data['yearly_percentage'] = (data['amount'] / yearly_total * 100) if yearly_total > 0 else 0
    
    # 按年份和月份分组
    grouped_transactions = {}
    for transaction in filtered_transactions:
        year_month = transaction.date.strftime('%Y-%m')
        if year_month not in grouped_transactions:
            grouped_transactions[year_month] = []
        grouped_transactions[year_month].append(transaction)
    
    # 获取所有可用的类别和二级分类
    all_categories = sorted(set(t.category for t in Transaction.query.filter_by(type='expense').all()))
    all_subcategories = sorted(set(t.subcategory for t in Transaction.query.filter_by(type='expense').all() if t.subcategory))
    
    return render_template('expense.html', 
                          grouped_transactions=grouped_transactions,
                          years=years,
                          months=months,
                          selected_year=selected_year,
                          selected_month=selected_month,
                          all_categories=all_categories,
                          all_subcategories=all_subcategories,
                          selected_category=selected_category,
                          selected_subcategory=selected_subcategory,
                          category_stats=category_stats,
                          subcategory_stats=subcategory_stats,
                          monthly_total=monthly_total,
                          yearly_total=yearly_total)

# 添加交易记录路由
@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        transaction_type = request.form.get('type')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        amount = request.form.get('amount')
        description = request.form.get('description')
        
        # 获取日期信息
        year = int(request.form.get('year'))
        month = int(request.form.get('month'))
        day = int(request.form.get('day'))
        
        # 创建日期对象
        transaction_date = datetime(year, month, day)
        
        # 创建新交易记录
        transaction = Transaction(
            type=transaction_type,
            category=category,
            subcategory=subcategory,
            amount=float(amount),
            description=description,
            date=transaction_date
        )
        
        # 添加到数据库
        db.session.add(transaction)
        db.session.commit()
        
        flash('交易记录已添加', 'success')
        return redirect(url_for('index'))
    
    # 获取当前年月日
    current_year = datetime.now().year
    
    return render_template('add.html', 
                          years=range(2020, 2051), 
                          months=range(1, 13), 
                          days=range(1, 32), 
                          current_year=current_year, 
                          current_month=datetime.now().month,
                          datetime=datetime)  # 添加这一行

# 添加账单导入相关路由
@app.route('/download_template')
def download_template():
    # 创建一个内存中的CSV文件
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(['交易时间', '交易类型', '交易对方', '商品', '收/支', '金额(元)', 
                    '支付方式', '当前状态', '交易单号', '商户单号', '备注'])
    
    # 写入示例数据
    writer.writerow(['2023-01-01 12:00:00', '消费', '超市', '日用品', '支出', '100.00', 
                    '支付宝', '交易成功', '202301010001', 'M202301010001', '购买日用品'])
    
    # 将指针移到文件开头
    output.seek(0)
    
    # 发送文件
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='finance_template.csv'
    )

@app.route('/import_bill', methods=['GET', 'POST'])
def import_bill():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            try:
                # 读取CSV文件
                stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
                df = pd.read_csv(stream)
                
                # 导入计数器
                imported_count = 0
                
                # 处理每一行数据
                for _, row in df.iterrows():
                    # 解析日期时间
                    try:
                        transaction_date = datetime.strptime(str(row['交易时间']), '%Y-%m-%d %H:%M:%S')
                    except:
                        transaction_date = datetime.now()
                    
                    # 确定交易类型
                    income_expense = str(row.get('收/支', '')).strip()
                    if income_expense == '支出':
                        transaction_type = 'expense'
                    elif income_expense == '收入':
                        transaction_type = 'income'
                    else:
                        # 跳过非收入或支出的记录
                        continue
                    
                    # 确定分类 - 使用默认值防止空值
                    category = str(row.get('交易类型', '其他'))
                    if category == 'nan' or not category:
                        category = '其他'  # 设置默认分类
                        
                    subcategory = str(row.get('商品', ''))
                    if subcategory == 'nan':
                        subcategory = ''  # 二级分类可以为空
                    
                    # 获取金额 - 改进金额处理逻辑
                    try:
                        # 检查金额列是否存在
                        if '金额(元)' in row:
                            amount_str = str(row['金额(元)']).strip()
                            # 处理可能的格式问题，如逗号分隔符、货币符号等
                            amount_str = amount_str.replace(',', '').replace('¥', '').replace('￥', '')
                            if amount_str and amount_str.lower() != 'nan':
                                amount = float(amount_str)
                            else:
                                amount = 0.0
                        else:
                            amount = 0.0
                    except Exception as e:
                        print(f"金额转换错误: {e}, 原始值: {row.get('金额(元)', 'N/A')}")
                        amount = 0.0  # 转换失败时使用默认金额
                    
                    # 创建描述 - 处理可能的空值
                    trade_partner = str(row.get('交易对方', ''))
                    if trade_partner == 'nan':
                        trade_partner = ''
                        
                    payment_method = str(row.get('支付方式', ''))
                    if payment_method == 'nan':
                        payment_method = ''
                        
                    remark = str(row.get('备注', ''))
                    if remark == 'nan':
                        remark = ''
                    
                    # 获取交易单号用于去重
                    transaction_id = str(row.get('交易单号', ''))
                    if transaction_id == 'nan':
                        transaction_id = ''
                        
                    # 检查是否已存在相同交易单号的记录
                    if transaction_id:
                        existing_transaction = Transaction.query.filter(
                            Transaction.description.like(f"%{transaction_id}%")
                        ).first()
                        
                        if existing_transaction:
                            # 跳过已存在的记录
                            continue
                    
                    # 将交易单号添加到描述中
                    description = f"交易对方: {trade_partner}, 支付方式: {payment_method}, 交易单号: {transaction_id}, 备注: {remark}"
                    
                    # 创建新交易记录
                    transaction = Transaction(
                        type=transaction_type,
                        category=category,
                        subcategory=subcategory,
                        amount=amount,
                        description=description,
                        date=transaction_date
                    )
                    
                    # 添加到数据库
                    db.session.add(transaction)
                    imported_count += 1
                
                # 提交所有更改
                db.session.commit()
                
                flash(f'成功导入 {imported_count} 条交易记录', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                db.session.rollback()  # 发生错误时回滚事务
                flash(f'导入失败: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('请上传CSV文件', 'error')
            return redirect(request.url)
    
    return render_template('import_bill.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8992)
  