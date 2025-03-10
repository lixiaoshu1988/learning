from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_migrate import Migrate  

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

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        type = request.form['type']
        category = request.form['category']
        subcategory = request.form.get('subcategory', '')  # 获取二级分类
        amount_str = request.form['amount']
        description = request.form.get('description', '')
        year = request.form.get('year')
        month = request.form.get('month')
        
        # 验证金额字段
        if not amount_str:
            flash('金额不能为空！', 'error')
            return redirect(url_for('add_transaction'))
        
        try:
            amount = float(amount_str)
        except ValueError:
            flash('请输入有效的金额！', 'error')
            return redirect(url_for('add_transaction'))
        
        # 处理年份和月份
        try:
            if year and month:
                # 设置为当月的第一天
                date = datetime(int(year), int(month), 1)
            else:
                # 如果未提供年份或月份，使用当前日期
                now = datetime.now()
                date = datetime(now.year, now.month, 1)
        except ValueError:
            flash('年份或月份格式无效！', 'error')
            return redirect(url_for('add_transaction'))
        
        transaction = Transaction(
            type=type,
            category=category,
            subcategory=subcategory,  # 添加二级分类
            amount=amount,
            description=description,
            date=date
        )
        
        db.session.add(transaction)
        db.session.commit()
        flash('交易记录已添加！', 'success')
        
        # 根据交易类型重定向到相应页面
        if type == 'income':
            return redirect(url_for('income'))
        else:
            return redirect(url_for('expense'))
    
    # 获取当前年份和最近几年的选项
    current_year = datetime.now().year
    years = range(current_year - 5, current_year + 1)
    months = range(1, 13)
    
    # 将 datetime 对象传递给模板
    return render_template('add.html', 
                          years=years, 
                          months=months, 
                          current_year=current_year, 
                          current_month=datetime.now().month,
                          datetime=datetime)  # 添加这一行

# 添加账单导入路由
# 在文件顶部添加必要的导入
import os
import logging
from flask import send_file

# 设置日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'import.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('finance_app')

# 修改导入账单路由
@app.route('/import_bill', methods=['POST'])
def import_bill():
    if 'bill_file' not in request.files:
        flash('没有选择文件', 'danger')
        return redirect(url_for('add_transaction'))
    
    file = request.files['bill_file']
    if file.filename == '':
        flash('没有选择文件', 'danger')
        return redirect(url_for('add_transaction'))
    
    bill_type = request.form.get('bill_type')
    
    # 创建导入会话ID，用于标识本次导入
    import_session_id = datetime.now().strftime('%Y%m%d%H%M%S')
    logger.info(f"===== 开始导入会话 {import_session_id} =====")
    logger.info(f"文件名: {file.filename}, 账单类型: {bill_type}")
    
    if file and file.filename.endswith('.csv'):
        try:
            # 读取CSV文件内容
            stream = io.StringIO(file.stream.read().decode("utf-8", errors='ignore'), newline=None)
            csv_data = csv.reader(stream)
            
            # 获取所有行用于调试
            rows = list(csv_data)
            
            # 检查是否有数据
            if len(rows) <= 1:  # 只有标题行或没有数据
                logger.error(f"CSV文件没有数据或格式不正确")
                flash('CSV文件没有数据或格式不正确', 'danger')
                return redirect(url_for('add_transaction'))
            
            # 记录CSV文件的标题行
            logger.info(f"CSV标题行: {rows[0]}")
            
            # 跳过标题行
            rows = rows[1:]
            
            success_count = 0
            error_count = 0
            error_details = []
            
            for row_index, row in enumerate(rows):
                try:
                    # 检查行数据是否足够
                    if len(row) < 6:
                        error_msg = f"第{row_index+2}行数据不足: {row}"
                        logger.warning(error_msg)
                        error_details.append(error_msg)
                        error_count += 1
                        continue
                    
                    # 根据账单类型解析数据
                    if bill_type == 'alipay':
                        try:
                            # 支付宝账单格式解析
                            # 尝试不同的日期格式
                            try:
                                transaction_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                try:
                                    transaction_date = datetime.strptime(row[0], '%Y/%m/%d %H:%M:%S')
                                except ValueError:
                                    transaction_date = datetime.strptime(row[0], '%Y.%m.%d %H:%M:%S')
                            
                            # 检查收支类型
                            if '收入' in row[4]:
                                transaction_type = 'income'
                            elif '支出' in row[4]:
                                transaction_type = 'expense'
                            else:
                                transaction_type = 'expense'  # 默认为支出
                            
                            # 处理金额
                            amount_str = row[5].replace('¥', '').replace(',', '').strip()
                            amount = float(amount_str)
                            
                            # 获取分类
                            description = row[3] if len(row) > 3 else ""
                            category, subcategory = map_alipay_category(description)
                            
                        except Exception as e:
                            error_msg = f"支付宝格式解析错误(第{row_index+2}行): {str(e)}\n原始数据: {row}"
                            logger.error(error_msg)
                            error_details.append(error_msg)
                            error_count += 1
                            continue
                            
                    elif bill_type == 'wechat':
                        try:
                            # 微信账单格式解析
                            try:
                                transaction_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                try:
                                    transaction_date = datetime.strptime(row[0], '%Y/%m/%d %H:%M:%S')
                                except ValueError:
                                    transaction_date = datetime.strptime(row[0], '%Y.%m.%d %H:%M:%S')
                            
                            # 检查收支类型
                            if '收入' in row[4]:
                                transaction_type = 'income'
                            elif '支出' in row[4]:
                                transaction_type = 'expense'
                            else:
                                transaction_type = 'expense'  # 默认为支出
                            
                            # 处理金额
                            amount_str = row[5].replace('¥', '').replace(',', '').strip()
                            amount = float(amount_str)
                            
                            # 获取分类
                            description = row[3] if len(row) > 3 else ""
                            category, subcategory = map_wechat_category(description)
                            
                        except Exception as e:
                            error_details.append(f"微信格式解析错误(第{row_index+2}行): {str(e)}\n原始数据: {row}")
                            error_count += 1
                            continue
                    
                    # 使用SQLAlchemy添加到数据库
                    transaction = Transaction(
                        type=transaction_type,
                        category=category,
                        subcategory=subcategory,
                        amount=amount,
                        description=description,
                        date=transaction_date
                    )
                    
                    db.session.add(transaction)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"处理第{row_index+2}行时出错: {str(e)}\n原始数据: {row}"
                    logger.error(error_msg)
                    error_details.append(error_msg)
                    continue
            
            # 提交所有成功的记录
            if success_count > 0:
                db.session.commit()
                result_msg = f'成功导入 {success_count} 条记录' + (f', {error_count} 条记录导入失败' if error_count > 0 else '')
                logger.info(result_msg)
                flash(result_msg, 'success')
                
                # 如果有错误，提示用户查看日志
                if error_count > 0:
                    flash(f'您可以在<a href="{url_for("view_import_logs")}">日志页面</a>查看导入失败的详细信息', 'info')
            else:
                # 记录详细错误信息
                logger.error(f"导入失败，所有记录均未导入")
                logger.error(f"===== 失败详情 =====")
                for detail in error_details:
                    logger.error(detail)
                flash('导入失败，请检查文件格式是否正确。您可以在日志页面查看详细错误信息。', 'danger')
                
            logger.info(f"===== 导入会话 {import_session_id} 结束 =====")
            return redirect(url_for('index'))
        
        except Exception as e:
            db.session.rollback()
            logger.exception(f"导入过程中发生错误: {str(e)}")
            flash(f'导入过程中发生错误: {str(e)}', 'danger')
            return redirect(url_for('add_transaction'))
    
    logger.warning(f"上传的文件不是CSV格式")
    flash('请上传CSV格式的文件', 'danger')
    return redirect(url_for('add_transaction'))

# 添加查看导入日志的路由
@app.route('/logs')
def view_import_logs():
    log_file = os.path.join(log_dir, 'import.log')
    
    # 如果日志文件不存在，创建一个空文件
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("暂无导入日志\n")
    
    # 读取日志文件内容
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.readlines()
    
    # 最新的日志在前面
    log_content.reverse()
    
    return render_template('logs.html', log_content=log_content)

# 添加下载日志文件的路由
@app.route('/download_logs')
def download_logs():
    log_file = os.path.join(log_dir, 'import.log')
    
    # 如果日志文件不存在，创建一个空文件
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("暂无导入日志\n")
    
    return send_file(log_file, as_attachment=True, download_name='import_logs.txt')

# 辅助函数：根据支付宝交易信息映射到自定义类别
def map_alipay_category(description):
    # 这里可以根据关键词匹配来确定类别
    description = description.lower() if description else ""
    
    # 食品类别的二级分类
    if any(keyword in description for keyword in ['超市', '大润发', '永辉']):
        return '食品', '超市'
    elif any(keyword in description for keyword in ['外卖', '美团', '饿了么']):
        return '食品', '外卖'
    elif any(keyword in description for keyword in ['餐厅', '餐饮', '饭店']):
        return '食品', '餐厅'
    elif any(keyword in description for keyword in ['零食', '饮料']):
        return '食品', '零食饮料'
        
    # 购物类别的二级分类
    elif any(keyword in description for keyword in ['淘宝', '天猫', '京东']):
        return '购物', '网购'
    elif any(keyword in description for keyword in ['服装', '衣服', '鞋子']):
        return '购物', '服饰'
    elif any(keyword in description for keyword in ['电子', '数码', '手机']):
        return '购物', '数码电子'
    elif any(keyword in description for keyword in ['日用', '家居']):
        return '购物', '日用家居'
        
    # 宠物类别的二级分类
    elif any(keyword in description for keyword in ['宠物', '猫', '狗']):
        if any(keyword in description for keyword in ['食品', '粮食']):
            return '宠物', '宠物食品'
        elif any(keyword in description for keyword in ['医疗', '兽医']):
            return '宠物', '宠物医疗'
        else:
            return '宠物', '其他宠物支出'
            
    # 住房类别的二级分类
    elif any(keyword in description for keyword in ['房租']):
        return '住房', '房租'
    elif any(keyword in description for keyword in ['水电', '电费', '水费']):
        return '住房', '水电费'
    elif any(keyword in description for keyword in ['物业', '管理费']):
        return '住房', '物业费'
    elif any(keyword in description for keyword in ['维修', '装修']):
        return '住房', '维修装修'
        
    # 交通类别的二级分类
    elif any(keyword in description for keyword in ['地铁', '公交', '公共交通']):
        return '交通', '公共交通'
    elif any(keyword in description for keyword in ['打车', '滴滴', '出租车']):
        return '交通', '打车'
    elif any(keyword in description for keyword in ['加油', '汽油']):
        return '交通', '加油'
    elif any(keyword in description for keyword in ['停车']):
        return '交通', '停车费'
        
    # 休闲娱乐类别的二级分类
    elif any(keyword in description for keyword in ['电影', '影院', '电影院']):
        return '休闲娱乐', '电影'
    elif any(keyword in description for keyword in ['游戏', '游戏充值']):
        return '休闲娱乐', '游戏'
    elif any(keyword in description for keyword in ['旅游', '景点', '门票']):
        return '休闲娱乐', '旅游'
    elif any(keyword in description for keyword in ['健身', '运动']):
        return '休闲娱乐', '健身运动'
        
    # 医疗保健类别的二级分类
    elif any(keyword in description for keyword in ['医院', '诊所']):
        return '医疗保健', '就医'
    elif any(keyword in description for keyword in ['药店', '药房', '药']):
        return '医疗保健', '药品'
    elif any(keyword in description for keyword in ['体检']):
        return '医疗保健', '体检'
        
    # 工作学习类别的二级分类
    elif any(keyword in description for keyword in ['书籍', '书店']):
        return '工作学习', '书籍'
    elif any(keyword in description for keyword in ['学习', '培训', '课程']):
        return '工作学习', '培训课程'
    elif any(keyword in description for keyword in ['办公', '文具']):
        return '工作学习', '办公用品'
        
    # 金融保险类别的二级分类
    elif any(keyword in description for keyword in ['保险']):
        return '金融保险', '保险'
    elif any(keyword in description for keyword in ['理财', '投资']):
        return '金融保险', '理财投资'
    elif any(keyword in description for keyword in ['手续费', '服务费']):
        return '金融保险', '手续费'
        
    # 人情往来类别的二级分类
    elif any(keyword in description for keyword in ['红包']):
        return '人情往来', '红包'
    elif any(keyword in description for keyword in ['礼金', '礼物']):
        return '人情往来', '礼金礼物'
    elif any(keyword in description for keyword in ['请客']):
        return '人情往来', '请客'
        
    # 育儿类别的二级分类
    elif any(keyword in description for keyword in ['儿童', '婴儿']):
        if any(keyword in description for keyword in ['食品', '奶粉']):
            return '育儿', '儿童食品'
        elif any(keyword in description for keyword in ['玩具']):
            return '育儿', '儿童玩具'
        elif any(keyword in description for keyword in ['教育', '培训']):
            return '育儿', '儿童教育'
        else:
            return '育儿', '其他育儿支出'
    
    # 默认返回其他类别
    else:
        return '其他', '未分类'

# 辅助函数：根据微信交易信息映射到自定义类别
def map_wechat_category(description):
    # 与支付宝类似的映射逻辑
    return map_alipay_category(description)  # 可以复用支付宝的映射逻辑

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8992)
  