from flask import Flask, render_template, request, send_file, jsonify
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm, inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from PIL import Image
import io
import json
import uuid
import urllib.request
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_invoice_generator')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['FONT_FOLDER'] = 'static/fonts'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FONT_FOLDER'], exist_ok=True)

# 注册字体
def register_fonts():
    # 创建字体目录
    os.makedirs(app.config['FONT_FOLDER'], exist_ok=True)
    
    # 尝试注册CID字体（内置中文字体）
    try:
        # 注册CID字体 - 这些是ReportLab内置的中文字体
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))  # 中文宋体
        print("成功注册内置中文字体: STSong-Light")
        
        # 注册CID字体 - 这些是ReportLab内置的中文字体
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))  # 日文/中文明朝体
        print("成功注册内置中文字体: HeiseiMin-W3")
        
        # 注册CID字体 - 这些是ReportLab内置的中文字体
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))  # 日文/中文黑体
        print("成功注册内置中文字体: HeiseiKakuGo-W5")
        
        # 尝试注册TrueType字体 - 这些字体能更好地支持中英文混排
        try:
            # 优先注册思源黑体
            source_han_path = os.path.join(app.config['FONT_FOLDER'], 'SourceHanSansCN-Regular.otf')
            if os.path.exists(source_han_path):
                from reportlab.pdfbase.ttfonts import TTFont
                try:
                    # 注意：虽然使用TTFont类，但这是OTF格式，不是TTF格式
                    pdfmetrics.registerFont(TTFont('SourceHanSansCN', source_han_path))
                    print(f"成功注册思源黑体: SourceHanSansCN")
                except Exception as e:
                    print(f"注册思源黑体失败: {e}")
            
            # 注册Noto Sans SC字体
            noto_font_path = os.path.join(app.config['FONT_FOLDER'], 'NotoSansCJKsc-Regular.otf')
            if os.path.exists(noto_font_path):
                from reportlab.pdfbase.ttfonts import TTFont
                try:
                    # 注意：这个文件虽然扩展名是.ttf，但实际上是从.otf重命名而来
                    pdfmetrics.registerFont(TTFont('NotoSansCJKsc', noto_font_path))
                    print(f"成功注册Noto Sans CJK SC字体: NotoSansCJKsc")
                except Exception as e:
                    print(f"注册Noto Sans CJK SC字体失败: {e}")
            
            # 检查是否存在常见的中英文兼容字体
            font_paths = [
                # 尝试常见的系统字体路径
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                '/System/Library/Fonts/STHeiti Light.ttc',  # macOS
                '/Library/Fonts/Arial Unicode.ttf',  # 通用
                '/usr/share/fonts/truetype/arphic/uming.ttc',  # Linux
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # Linux
                'C:/Windows/Fonts/msyh.ttf',  # Windows
                'C:/Windows/Fonts/simhei.ttf',  # Windows
            ]
            
            # 尝试注册系统字体
            for font_path in font_paths:
                if os.path.exists(font_path):
                    # 从路径中提取字体名称
                    font_name = os.path.splitext(os.path.basename(font_path))[0]
                    # 注册TrueType字体
                    from reportlab.pdfbase.ttfonts import TTFont
                    pdfmetrics.registerFont(TTFont(f'Mixed-{font_name}', font_path))
                    print(f"成功注册TrueType字体: Mixed-{font_name}")
            
        except Exception as e:
            print(f"注册TrueType字体失败: {e}")
            print("将使用内置CID字体")
    except Exception as e:
        print(f"注册内置中文字体失败: {e}")

# 尝试下载中英文混排字体
def download_mixed_font():
    """下载支持中英文混排的字体"""
    # 创建字体目录
    os.makedirs(app.config['FONT_FOLDER'], exist_ok=True)
    
    # 检查Noto Sans SC字体是否已存在
    noto_font_path = os.path.join(app.config['FONT_FOLDER'], 'NotoSansCJKsc-Regular.otf')
    if os.path.exists(noto_font_path):
        print(f"Noto Sans SC字体文件已存在: {noto_font_path}")
    else:
        # 尝试下载Google Noto Sans SC字体（支持中英文混排）
        noto_font_url = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
        temp_font_path = os.path.join(app.config['FONT_FOLDER'], 'temp_font.otf')
        
        try:
            print(f"正在下载Noto Sans SC字体: {noto_font_url}")
            with urllib.request.urlopen(noto_font_url, timeout=10) as response, open(temp_font_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            # 保持.otf扩展名，不要重命名为.ttf
            shutil.move(temp_font_path, noto_font_path)
            print(f"Noto Sans SC字体下载成功: {noto_font_path}")
        except Exception as e:
            print(f"Noto Sans SC字体下载失败: {e}")
            # 清理临时文件
            if os.path.exists(temp_font_path):
                os.remove(temp_font_path)
    
    # 检查思源黑体是否已存在
    source_han_path = os.path.join(app.config['FONT_FOLDER'], 'SourceHanSansCN-Regular.otf')
    if os.path.exists(source_han_path):
        print(f"思源黑体文件已存在: {source_han_path}")
    else:
        # 尝试下载思源黑体（支持中英文混排）
        source_han_url = "https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf"
        temp_font_path = os.path.join(app.config['FONT_FOLDER'], 'temp_source_han.otf')
        
        try:
            print(f"正在下载思源黑体: {source_han_url}")
            with urllib.request.urlopen(source_han_url, timeout=10) as response, open(temp_font_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            # 直接使用.otf格式
            shutil.move(temp_font_path, source_han_path)
            print(f"思源黑体下载成功: {source_han_path}")
        except Exception as e:
            print(f"思源黑体下载失败: {e}")
            # 清理临时文件
            if os.path.exists(temp_font_path):
                os.remove(temp_font_path)

# 尝试注册字体
try:
    # 尝试下载字体
    download_mixed_font()
    # 注册字体
    register_fonts()
except Exception as e:
    print(f"注册字体时出错: {e}")
    print("PDF生成将使用默认字体，中文可能无法正确显示")

@app.route('/')
def index():
    return render_template('index.html')

# 辅助函数：增加字符间距
def draw_spaced_string(canvas_obj, x, y, text, font_name, font_size, spacing=None):
    """绘制具有增加字符间距的文本"""
    # 如果未指定spacing，使用默认值
    if spacing is None:
        spacing = CONTENT_SPACING
    
    # 检查文本是否包含中英文混排
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    has_english = any(('a' <= char <= 'z') or ('A' <= char <= 'Z') for char in text)
    
    # 如果是中英文混排，并且使用的是CID字体，尝试使用TrueType字体
    if has_chinese and (has_english or not has_chinese) and font_name == "STSong-Light":
        # 优先使用Source Han Sans CN字体
        from reportlab.pdfbase.pdfmetrics import getRegisteredFontNames
        registered_fonts = getRegisteredFontNames()
        
        if 'SourceHanSansCN' in registered_fonts:
            font_name = 'SourceHanSansCN'
        else:
            # 检查是否有其他已注册的TrueType字体
            mixed_fonts = [f for f in registered_fonts if f.startswith('Mixed-')]
            if mixed_fonts:
                # 使用第一个找到的混合字体
                font_name = mixed_fonts[0]
    
    # 创建文本对象
    text_obj = canvas_obj.beginText()
    text_obj.setTextOrigin(x, y)
    text_obj.setFont(font_name, font_size)
    text_obj.setCharSpace(spacing)
    text_obj.textOut(text)
    # 绘制文本对象
    canvas_obj.drawText(text_obj)

# 辅助函数：绘制右对齐且有字符间距的文本
def draw_right_aligned_spaced_string(canvas_obj, x, y, text, font_name, font_size, spacing=None):
    """绘制右对齐且具有增加字符间距的文本"""
    # 如果未指定spacing，使用默认值
    if spacing is None:
        spacing = CONTENT_SPACING
    
    # 检查文本是否包含中英文混排
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    has_english = any(('a' <= char <= 'z') or ('A' <= char <= 'Z') for char in text)
    
    # 如果是中英文混排，并且使用的是CID字体，尝试使用TrueType字体
    if has_chinese and (has_english or not has_chinese) and font_name == "STSong-Light":
        # 优先使用Source Han Sans CN字体
        from reportlab.pdfbase.pdfmetrics import getRegisteredFontNames
        registered_fonts = getRegisteredFontNames()
        
        if 'SourceHanSansCN' in registered_fonts:
            font_name = 'SourceHanSansCN'
        else:
            # 检查是否有其他已注册的TrueType字体
            mixed_fonts = [f for f in registered_fonts if f.startswith('Mixed-')]
            if mixed_fonts:
                # 使用第一个找到的混合字体
                font_name = mixed_fonts[0]
    
    # 计算文本宽度（不包括字符间距）
    text_width = canvas_obj.stringWidth(text, font_name, font_size)
    # 字符间距会增加总宽度 (字符数-1)*spacing
    additional_width = (len(text) - 1) * spacing
    # 计算起始位置（右对齐）
    start_x = x - (text_width + additional_width)
    
    # 创建文本对象
    text_obj = canvas_obj.beginText()
    text_obj.setTextOrigin(start_x, y)
    text_obj.setFont(font_name, font_size)
    text_obj.setCharSpace(spacing)
    text_obj.textOut(text)
    # 绘制文本对象
    canvas_obj.drawText(text_obj)

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        # 获取请求数据
        data = request.json
        
        # 检查是预览还是下载
        action = data.get('action', 'download')
        
        # 获取发票数据
        document_type = data.get('document_type', 'invoice')
        invoice_number = data.get('invoice_number', '')
        invoice_date = data.get('invoice_date', datetime.now().strftime('%Y-%m-%d'))
        bill_from = data.get('bill_from', '')
        address_from = data.get('address_from', '')
        bill_to = data.get('bill_to', '')
        address_to = data.get('address_to', '')
        logo_path = data.get('logo_path', '')
        tax_rate = float(data.get('tax_rate', 0))
        show_tax = data.get('show_tax', True)
        show_notes = data.get('show_notes', True)
        notes = data.get('notes', '')
        items = data.get('items', [])
        currency = data.get('currency', 'USD')  # 获取货币信息
        
        # 获取货币符号
        currency_symbol = {
            'USD': '$',
            'HKD': '$',
            'CNY': '¥'
        }.get(currency, '$')

        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 设置字体
        default_font = "Helvetica"  # 默认字体
        default_bold_font = "Helvetica-Bold"  # 相应的粗体字体
        chinese_font = "STSong-Light"  # 使用内置中文字体
        
        # 尝试使用思源黑体进行中英文混排
        try:
            # 检查思源黑体是否已注册
            from reportlab.pdfbase.pdfmetrics import getRegisteredFontNames
            registered_fonts = getRegisteredFontNames()
            
            if 'SourceHanSansCN' in registered_fonts:
                chinese_font = 'SourceHanSansCN'
                print(f"使用思源黑体进行中英文混排")
            elif 'NotoSansCJKsc' in registered_fonts:
                chinese_font = 'NotoSansCJKsc'
                print(f"使用Noto Sans CJK SC字体进行中英文混排")
            else:
                # 检查是否有其他已注册的TrueType字体
                mixed_fonts = [f for f in registered_fonts if f.startswith('Mixed-')]
                
                if mixed_fonts:
                    # 使用第一个找到的混合字体
                    chinese_font = mixed_fonts[0]
                    print(f"使用TrueType字体进行中英文混排: {chinese_font}")
        except Exception as e:
            print(f"获取TrueType字体失败: {e}")
            print("将使用内置CID字体")
        
        # 设置标题字距
        TITLE_SPACING = 0.5  # 标题字距
        CONTENT_SPACING = 0.2  # 减小正文字距
        # 创建段落样式 - 使用更大的行距
        styles = getSampleStyleSheet()
        chinese_style = ParagraphStyle(
            'ChineseStyle',
            fontName=chinese_font,
            fontSize=10,
            leading=16,  # 增加行距
            spaceBefore=6,
            spaceAfter=6
        )
        
        # 创建英文段落样式 - 使用更大的行距
        english_style = ParagraphStyle(
            'EnglishStyle',
            fontName=default_font,
            fontSize=10,
            leading=16,  # 增加行距
            spaceBefore=6,
            spaceAfter=6
        )
        
        # 创建表格标题样式
        table_header_style = ParagraphStyle(
            'TableHeaderStyle',
            fontName=default_bold_font,
            fontSize=10,
            leading=16,
            spaceBefore=6,
            spaceAfter=6
        )
        
        # Set basic information
        doc_title = "Receipt" if document_type == 'receipt' else "Invoice"
        c.setTitle(f"{doc_title} {invoice_number}")
        
        # 设置页面边距
        margin = 1.5 * cm
        content_width = width - 2 * margin
        
        # 计算顶部区域的高度
        top_section_height = 3.5 * cm
        
        # Add company logo (if available) - 移到右上角并调整对齐
        if logo_path and os.path.exists(os.path.join('static', logo_path)):
            # 调整logo位置到右上角，与发票信息顶部对齐
            c.drawImage(os.path.join('static', logo_path), 
                       width - margin - 3 * cm,  # 右侧位置
                       height - margin - 2.5 * cm,  # 与发票标题顶部对齐
                       width=3 * cm, 
                       height=3 * cm, 
                       preserveAspectRatio=True)
        
        # Add invoice title - 使用粗体，移到左上角
        c.setFont(default_bold_font, 24)
        draw_spaced_string(c, margin, height - margin - 1 * cm, doc_title.upper(), default_bold_font, 24, TITLE_SPACING)
        
        # Add invoice number and date - 移到左上角，使用增加字符间距的函数
        draw_spaced_string(c, margin, height - margin - 1.5 * cm, 
                          f"{doc_title} No: {invoice_number}", 
                          default_font, 10, TITLE_SPACING)
        
        # Add invoice date - 移到左上角，使用增加字符间距的函数
        date_label = "Receipt Date" if document_type == 'receipt' else "Invoice Date"
        draw_spaced_string(c, margin, height - margin - 2 * cm, 
                          f"{date_label}: {invoice_date}", 
                          default_font, 10, TITLE_SPACING)
        
        currency_label = "Currency" 
        draw_spaced_string(c, margin, height - margin - 2.5 * cm, 
                          f"{currency_label}: {currency}", 
                          default_font, 10, TITLE_SPACING)
        
        # 水平分隔线 - 调整位置
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.line(margin, height - margin - top_section_height, width - margin, height - margin - top_section_height)
        
        # 计算Bill From和Bill To的起始位置
        bill_section_y = height - margin - top_section_height - 1 * cm
        
        # Add bill from information - 使用中文字体
        c.setFont(default_bold_font, 11)
        # 使用 draw_spaced_string 函数设置字距
        draw_spaced_string(c, margin, bill_section_y, "Bill From:", default_bold_font, 11, TITLE_SPACING)
        c.setFont(chinese_font, 10)  # 使用中文字体
        
        # 计算地址起始位置
        address_y = bill_section_y - 0.6 * cm
        
        # 使用 draw_spaced_string 函数设置字距
        draw_spaced_string(c, margin, address_y, bill_from, chinese_font, 10, TITLE_SPACING)
        
        # Add address (line by line) - 使用中文字体和增加字距的函数
        address_from_lines = address_from.split('\n')
        current_y = address_y - 0.5 * cm
        for line in address_from_lines:
            draw_spaced_string(c, margin, current_y, line, chinese_font, 10, TITLE_SPACING)
            current_y -= 0.5 * cm
        
        # 记录Bill From部分的最终位置，用于后续计算
        bill_from_bottom_y = current_y
        
        # Add client information - 使用中文字体，确保与Bill From对齐
        c.setFont(default_bold_font, 11)
        draw_spaced_string(c, width / 2, bill_section_y, "Bill To:", default_bold_font, 11, TITLE_SPACING)
        c.setFont(chinese_font, 10)  # 使用中文字体
        
        # 使用 draw_spaced_string 函数设置字距
        draw_spaced_string(c, width / 2, address_y, bill_to, chinese_font, 10, TITLE_SPACING)
        
        # Add client address - 使用中文字体和增加字距的函数
        address_to_lines = address_to.split('\n')
        current_y = address_y - 0.5 * cm
        for line in address_to_lines:
            draw_spaced_string(c, width / 2, current_y, line, chinese_font, 10, TITLE_SPACING)
            current_y -= 0.5 * cm
        
        # 记录Bill To部分的最终位置，用于后续计算
        bill_to_bottom_y = current_y
        
        # 使用两个部分中较低的位置作为下一部分的起始位置
        next_section_y = min(bill_from_bottom_y, bill_to_bottom_y) - 1.5 * cm
        
        # 计算表格开始位置 - 确保有足够空间
        table_y_pos = next_section_y
        
        # Add items table
        if items:
            # Table title
            c.setFont(default_bold_font, 11)
            draw_spaced_string(c, margin, table_y_pos, "Items", default_bold_font, 11, TITLE_SPACING)
            
            # 定义表格列宽
            col_widths = [content_width * 0.5, content_width * 0.15, content_width * 0.15, content_width * 0.2]
            
            # 创建表格数据 - 使用字符串而不是Paragraph，以便更好地控制对齐
            table_data = [['Item', 'Quantity', 'Price', 'Amount']]
            
            for item in items:
                name = item.get('name', '')
                
                # 确保将字符串转换为浮点数
                quantity = float(item.get('quantity', 0))
                price = float(item.get('price', 0))
                amount = quantity * price
                
                # 使用字符串，后续在表格样式中设置对齐
                table_data.append([
                    name, 
                    str(quantity), 
                    f"{currency_symbol}{price:.2f}", 
                    f"{currency_symbol}{amount:.2f}"
                ])
            
            # Calculate subtotal
            subtotal = sum(float(item.get('quantity', 0)) * float(item.get('price', 0)) for item in items)
            
            # Calculate tax
            # 确保将字符串转换为浮点数
            tax_amount = subtotal * (tax_rate / 100)
            
            # Calculate total
            total = subtotal + tax_amount
            
            # 设置表格样式 - 更细的线条和更少的边框，增加内边距，设置数字列右对齐
            table_style = TableStyle([
                ('FONT', (0, 0), (-1, 0), default_bold_font),  # 表头使用粗体
                ('FONT', (0, 1), (0, -1), chinese_font),       # 第一列（项目名称）使用中文字体
                ('FONT', (1, 1), (-1, -1), default_font),      # 其他列使用默认字体
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),            # 第一列左对齐
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),          # 其他列右对齐
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (-1, 0), 0.3, colors.lightgrey),  # 表头下方的线更细
                ('LINEABOVE', (0, -1), (-1, -1), 0.3, colors.lightgrey),  # 最后一行上方的线更细
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # 增加表头底部内边距
                ('TOPPADDING', (0, 0), (-1, 0), 12),     # 增加表头顶部内边距
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),  # 增加单元格底部内边距
                ('TOPPADDING', (0, 1), (-1, -1), 8),     # 增加单元格顶部内边距
                ('LEFTPADDING', (0, 0), (-1, -1), 6),    # 增加左侧内边距
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),   # 增加右侧内边距
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),  # 移除表头背景色
            ])
            
            # 创建表格
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(table_style)
            
            # 绘制表格 - 确保有足够的高度
            table_height = len(table_data) * 1.0 * cm  # 增加每行高度
            table.wrapOn(c, content_width, table_height)
            table.drawOn(c, margin, table_y_pos - table_height - 0.5 * cm)
            
            # 计算总计部分的位置
            totals_y_pos = table_y_pos - table_height - 1.5 * cm
            
            # 添加小计、税费和总计 - 使用右对齐且有字符间距的函数
            draw_right_aligned_spaced_string(
                c, width - margin, totals_y_pos, 
                f"Subtotal: {currency_symbol}{subtotal:.2f}", 
                default_font, 10, TITLE_SPACING
            )
            
            if show_tax and tax_rate > 0:
                totals_y_pos -= 0.5 * cm
                draw_right_aligned_spaced_string(
                    c, width - margin, totals_y_pos, 
                    f"Tax ({tax_rate}%): {currency_symbol}{tax_amount:.2f}", 
                    default_font, 10, TITLE_SPACING
                )
            
            totals_y_pos -= 0.7 * cm
            draw_right_aligned_spaced_string(
                c, width - margin, totals_y_pos, 
                f"Total ({currency}): {currency_symbol}{total:.2f}", 
                default_bold_font, 11, TITLE_SPACING
            )
            

            
            # 计算备注部分的位置
            notes_y_pos = totals_y_pos - 2 * cm
            
            # Add notes - 使用中文字体
            if show_notes and notes:
                c.setFont(default_bold_font, 11)
                draw_spaced_string(c, margin, notes_y_pos, "Notes:", default_bold_font, 11, TITLE_SPACING)
                
                # 创建文本对象进行自动换行
                text_object = c.beginText(margin, notes_y_pos - 0.5 * cm)
                
                # 优先使用Source Han Sans CN字体
                notes_font = chinese_font
                notes_font_size = 9
                
                text_object.setFont(notes_font, notes_font_size)
                # 设置字符间距
                text_object.setCharSpace(CONTENT_SPACING)
                
                # 定义最大宽度为内容区域宽度
                max_width = content_width
                
                # 处理中文和英文混合文本的自动换行
                # 首先按换行符分割文本
                paragraphs = notes.split('\n')
                
                for paragraph in paragraphs:
                    if not paragraph:  # 跳过空段落
                        text_object.textLine('')
                        continue
                        
                    # 当前行文本和宽度
                    current_line = ""
                    current_width = 0
                    
                    # 逐字符处理，适用于中英文混合
                    for char in paragraph:
                        # 计算添加这个字符后的宽度
                        char_width = c.stringWidth(char, notes_font, notes_font_size)
                        # 考虑字符间距的影响
                        if current_line:  # 如果不是行首字符，加上字符间距
                            char_width += CONTENT_SPACING
                        
                        if current_width + char_width <= max_width:
                            current_line += char
                            current_width += char_width
                        else:
                            # 当前行已满，输出并开始新行
                            text_object.textLine(current_line)
                            current_line = char
                            current_width = c.stringWidth(char, notes_font, notes_font_size)  # 重置宽度，不包含间距
                    
                    # 输出最后一行
                    if current_line:
                        text_object.textLine(current_line)
                
                # 绘制文本
                c.drawText(text_object)
                
                # 计算文本高度并更新notes_y_pos
                text_height = text_object.getY() - (notes_y_pos - 0.5 * cm)
                notes_y_pos -= abs(text_height) + 1.2 * cm
            else:
                # 如果没有备注，直接在总计下方添加签署栏
                notes_y_pos = totals_y_pos - 3 * cm
            
            # 添加签名和日期行
            c.setFont(default_bold_font, 11)
            draw_spaced_string(c, margin, notes_y_pos, "Signature:", default_bold_font, 11, TITLE_SPACING)
            
            # 签名线
            c.line(margin + 2.5 * cm, notes_y_pos - 0.2 * cm, margin + 7 * cm, notes_y_pos - 0.2 * cm)
            
            # 日期行
            draw_spaced_string(c, margin + 8 * cm, notes_y_pos, "Date:", default_bold_font, 11, TITLE_SPACING)
            c.line(margin + 9.5 * cm, notes_y_pos - 0.2 * cm, margin + 14 * cm, notes_y_pos - 0.2 * cm)
        
        # Add footer
        c.setFont(default_font, 8)
        draw_spaced_string(c, margin, margin, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", default_font, 8, TITLE_SPACING)
        
        # 添加右侧页脚
        draw_right_aligned_spaced_string(c, width - margin, margin, "Generated by Freeland Media Limited", default_font, 8, TITLE_SPACING)
        
        # Save PDF
        c.save()
        
        # Move buffer content to the beginning
        buffer.seek(0)
        
        # Generate unique filename
        filename = f"{document_type}_{invoice_number}.pdf"
        
        # Save PDF to temporary file
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(temp_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        # 返回PDF文件URL
        pdf_url = f"/preview/{filename}" if action == 'preview' else f"/download/{filename}"
        
        return jsonify({
            'success': True,
            'pdf_url': pdf_url
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), 
                     as_attachment=True, 
                     download_name=filename)

@app.route('/preview/<filename>')
def preview(filename):
    # 预览时不设置Content-Disposition头，这样浏览器会在页面中显示PDF而不是下载
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), 
                     mimetype='application/pdf')

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['logo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file:
        # Generate unique filename
        filename = f"logo_{uuid.uuid4()}.png"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(file_path)
        
        # Return file path
        return jsonify({
            'success': True,
            'logo_path': f"uploads/{filename}"
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002) 