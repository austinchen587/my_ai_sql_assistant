from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import time
import re
import pandas as pd
from io import StringIO
from ..ai_tools import get_cached_sql_agent

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """AI响应格式化器"""
    
    @staticmethod
    def format_ai_response(text):
        """格式化AI返回的文本，转换为美观的HTML格式"""
        if not text:
            return text
        
        # 处理表格数据
        formatted_text = ResponseFormatter._format_tables(text)
        
        # 处理列表和段落
        formatted_text = ResponseFormatter._format_lists_and_paragraphs(formatted_text)
        
        # 处理标题和重点
        formatted_text = ResponseFormatter._format_headings_and_emphasis(formatted_text)
        
        # 处理代码块
        formatted_text = ResponseFormatter._format_code_blocks(formatted_text)
        
        return formatted_text
    
    @staticmethod
    def _format_tables(text):
        """将文本中的表格数据转换为HTML表格"""
        lines = text.split('\n')
        formatted_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 检测表格开始（包含列分隔符和表头分隔线）
            if '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
                table_lines = [line]
                i += 1
                
                # 收集表格行
                while i < len(lines) and '|' in lines[i]:
                    if '---' in lines[i]:  # 跳过表头分隔线
                        i += 1
                        continue
                    table_lines.append(lines[i])
                    i += 1
                
                # 转换为HTML表格
                if len(table_lines) > 1:
                    html_table = ResponseFormatter._create_html_table(table_lines)
                    formatted_lines.append(html_table)
                continue
            
            # 检测CSV风格的数据表格（逗号分隔）
            elif ',' in line and any(char.isdigit() for char in line):
                # 检查接下来的几行是否也是相似格式
                csv_lines = [line]
                j = i + 1
                while j < len(lines) and j < i + 10:  # 最多检查10行
                    next_line = lines[j].strip()
                    if next_line and ',' in next_line:
                        csv_lines.append(next_line)
                        j += 1
                    else:
                        break
                
                if len(csv_lines) > 1:
                    try:
                        # 尝试解析为DataFrame
                        csv_data = '\n'.join(csv_lines)
                        df = pd.read_csv(StringIO(csv_data))
                        html_table = df.to_html(index=False, classes='table table-bordered table-striped')
                        formatted_lines.append(html_table)
                        i = j - 1  # 跳过已处理的CSV行
                    except:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
            
            i += 1
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def _create_html_table(table_lines):
        """从Markdown表格行创建HTML表格"""
        html = ['<div class="table-responsive"><table class="table table-bordered table-striped">']
        
        for idx, line in enumerate(table_lines):
            if idx == 0:
                html.append('<thead><tr>')
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                for cell in cells:
                    html.append(f'<th>{cell}</th>')
                html.append('</tr></thead><tbody>')
            else:
                html.append('<tr>')
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                for cell in cells:
                    # 尝试解析数字并右对齐
                    if cell.replace(',', '').replace('.', '').isdigit():
                        html.append(f'<td style="text-align: right;">{cell}</td>')
                    else:
                        html.append(f'<td>{cell}</td>')
                html.append('</tr>')
        
        html.append('</tbody></table></div>')
        return '\n'.join(html)
    
    @staticmethod
    def _format_lists_and_paragraphs(text):
        """格式化列表和段落"""
        lines = text.split('\n')
        formatted_lines = []
        in_list = False
        list_type = None
        
        for line in lines:
            stripped = line.strip()
            
            # 检测有序列表
            if re.match(r'^\d+\.\s', stripped):
                if not in_list or list_type != 'ol':
                    if in_list:
                        formatted_lines.append('</ul>' if list_type == 'ul' else '</ol>')
                    formatted_lines.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                formatted_lines.append(f'<li>{stripped[3:]}</li>')
            
            # 检测无序列表
            elif re.match(r'^[•\-*]\s', stripped):
                if not in_list or list_type != 'ul':
                    if in_list:
                        formatted_lines.append('</ol>' if list_type == 'ol' else '</ul>')
                    formatted_lines.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                formatted_lines.append(f'<li>{stripped[2:]}</li>')
            
            # 段落处理
            elif stripped:
                if in_list:
                    formatted_lines.append('</ol>' if list_type == 'ol' else '</ul>')
                    in_list = False
                    list_type = None
                
                # 检查是否是标题
                if re.match(r'^#{1,3}\s', stripped):
                    level = len(re.match(r'^(#+)', stripped).group(1))
                    content = stripped[level:].strip()
                    formatted_lines.append(f'<h{level} class="ai-heading">{content}</h{level}>')
                else:
                    formatted_lines.append(f'<p>{stripped}</p>')
            else:
                if in_list:
                    formatted_lines.append('</ol>' if list_type == 'ol' else '</ul>')
                    in_list = False
                    list_type = None
                formatted_lines.append('<br>')
        
        if in_list:
            formatted_lines.append('</ol>' if list_type == 'ol' else '</ul>')
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def _format_headings_and_emphasis(text):
        """格式化标题和强调文本"""
        # 加粗文本
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # 斜体文本
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        # 内联代码
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        return text
    
    @staticmethod
    def _format_code_blocks(text):
        """格式化代码块"""
        # 简单的代码块检测（以```开始和结束）
        lines = text.split('\n')
        formatted_lines = []
        in_code_block = False
        code_lines = []
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # 结束代码块
                    code_block = '<pre><code>' + '\n'.join(code_lines) + '</code></pre>'
                    formatted_lines.append(code_block)
                    code_lines = []
                    in_code_block = False
                else:
                    # 开始代码块
                    in_code_block = True
            elif in_code_block:
                code_lines.append(line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

@csrf_exempt
def ask_question(request):
    """处理AI问答请求"""
    if request.method == 'POST':
        start_time = time.time()
        try:
            # 解析JSON数据
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            
            if not question:
                return JsonResponse({
                    'success': False,
                    'error': '问题不能为空'
                }, status=400)
            
            logger.info(f"📥 收到问题: {question}")
            
            # 获取缓存的AI Agent并处理问题
            agent = get_cached_sql_agent()
            result = agent.invoke({"input": question})
            
            raw_answer = result.get('output', '抱歉，我无法回答这个问题。')
            
            # 格式化响应
            formatted_answer = ResponseFormatter.format_ai_response(raw_answer)
            
            response_time = time.time() - start_time
            logger.info(f"✅ 回答生成 - 耗时: {response_time:.2f}s")
            
            return JsonResponse({
                'success': True,
                'answer': formatted_answer,
                'raw_answer': raw_answer,  # 保留原始答案用于调试
                'question': question,
                'response_time': f"{response_time:.2f}s"
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '请求数据格式错误'
            }, status=400)
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"❌ 处理问题失败 - 耗时: {error_time:.2f}s, 错误: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'处理问题时发生错误: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': '仅支持POST请求'
    }, status=405)
