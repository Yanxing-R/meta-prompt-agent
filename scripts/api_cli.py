# scripts/api_cli.py
"""
Think Twice API命令行工具

该工具允许从命令行与Meta-Prompt Agent API进行交互。
"""

import argparse
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meta_prompt_agent.api.client import ThinkTwiceAPIClient

def setup_argparse():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Think Twice API命令行工具")
    
    # 基础参数
    parser.add_argument('--base-url', default="http://localhost:8000", help="API服务的基础URL")
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 系统信息
    info_parser = subparsers.add_parser('info', help='获取系统信息')
    
    # 生成简单提示
    simple_parser = subparsers.add_parser('simple', help='生成简单优化提示')
    simple_parser.add_argument('--request', '-r', required=True, help='原始请求文本')
    simple_parser.add_argument('--task-type', '-t', default="通用/问答", help='任务类型')
    
    # 生成高级提示
    advanced_parser = subparsers.add_parser('advanced', help='生成高级优化提示')
    advanced_parser.add_argument('--request', '-r', required=True, help='原始请求文本')
    advanced_parser.add_argument('--task-type', '-t', default="通用/问答", help='任务类型')
    advanced_parser.add_argument('--self-correction', '-s', action='store_true', help='启用自我校正')
    advanced_parser.add_argument('--depth', '-d', type=int, default=2, help='最大递归深度')
    advanced_parser.add_argument('--template', help='使用的模板名称')
    advanced_parser.add_argument('--vars', help='模板变量(JSON格式)')
    
    # 解释术语
    explain_parser = subparsers.add_parser('explain', help='解释术语')
    explain_parser.add_argument('--term', '-t', required=True, help='要解释的术语')
    explain_parser.add_argument('--context', '-c', required=True, help='术语的上下文')
    
    # 提交反馈
    feedback_parser = subparsers.add_parser('feedback', help='提交反馈')
    feedback_parser.add_argument('--id', required=True, help='提示ID')
    feedback_parser.add_argument('--request', required=True, help='原始请求')
    feedback_parser.add_argument('--prompt', required=True, help='生成的提示')
    feedback_parser.add_argument('--rating', type=int, required=True, choices=range(1, 6), help='评分(1-5)')
    feedback_parser.add_argument('--comment', help='评论')
    
    # 列出反馈
    list_feedback_parser = subparsers.add_parser('list-feedback', help='列出反馈')
    list_feedback_parser.add_argument('--limit', type=int, default=10, help='返回数量')
    list_feedback_parser.add_argument('--offset', type=int, default=0, help='偏移量')
    list_feedback_parser.add_argument('--min-rating', type=int, choices=range(1, 6), help='最低评分过滤')
    
    return parser

def main():
    """主函数"""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建API客户端
    client = ThinkTwiceAPIClient(base_url=args.base_url)
    
    try:
        # 根据命令执行不同操作
        if args.command == 'info':
            result = client.get_system_info()
        
        elif args.command == 'simple':
            result = client.generate_simple_prompt(
                raw_request=args.request,
                task_type=args.task_type
            )
        
        elif args.command == 'advanced':
            template_vars = {}
            if args.vars:
                try:
                    template_vars = json.loads(args.vars)
                except json.JSONDecodeError:
                    print("错误：模板变量必须是有效的JSON格式")
                    return
            
            result = client.generate_advanced_prompt(
                raw_request=args.request,
                task_type=args.task_type,
                enable_self_correction=args.self_correction,
                max_recursion_depth=args.depth,
                template_name=args.template,
                template_variables=template_vars if args.vars else None
            )
        
        elif args.command == 'explain':
            result = client.explain_term(
                term=args.term,
                context=args.context
            )
        
        elif args.command == 'feedback':
            result = client.submit_feedback(
                prompt_id=args.id,
                original_request=args.request,
                generated_prompt=args.prompt,
                rating=args.rating,
                comment=args.comment
            )
        
        elif args.command == 'list-feedback':
            result = client.get_feedback_list(
                limit=args.limit,
                offset=args.offset,
                min_rating=args.min_rating
            )
        
        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 如果有错误，退出状态码非零
        if result.get('error'):
            sys.exit(1)
    
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 