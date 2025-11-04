"""
OpenKG-ToolAgent集成mcp适配
文本内容类型判断，判断文本是否为医疗指南内容
"""
import argparse
import sys
import os
import logging
import io
import warnings

# 在导入模块之前先设置日志级别
logging.getLogger().setLevel(logging.CRITICAL + 1)
logging.getLogger('root').setLevel(logging.CRITICAL + 1)
logging.getLogger('backend').setLevel(logging.CRITICAL + 1)

# 禁用所有警告
warnings.filterwarnings("ignore")

# 保存原始输出
original_stdout = sys.stdout
original_stderr = sys.stderr

# 重定向所有输出到空设备
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tool_service import judge_content


def main():
    """命令行入口函数"""
    # 恢复标准输出以便显示结果和错误信息
    sys.stdout = original_stdout
    sys.stderr = original_stderr

    parser = argparse.ArgumentParser(description='判断文本是否为医疗指南内容')
    parser.add_argument('content', nargs='*', help='输入文本内容')
    parser.add_argument('--file', '-f', type=str, help='从文件读取文本内容')
    parser.add_argument('--stdin', action='store_true', help='从标准输入读取文本内容')

    args = parser.parse_args()

    # 获取文本内容
    if args.stdin:
        content = sys.stdin.read()
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"错误：文件 '{args.file}' 不存在", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"错误：读取文件时发生错误: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.content:
        # 将所有位置参数用空格连接成一个字符串
        content = ' '.join(args.content)
    else:
        print("错误：请提供文本内容，或使用--file参数指定文件、--stdin从标准输入读取", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # 调用judge_content方法，屏蔽日志输出
    try:
        # 再次重定向输出以屏蔽运行时的日志
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull

            # 临时禁用日志输出
            logging.getLogger().setLevel(logging.CRITICAL + 1)

            result = judge_content(content.strip())

            # 恢复输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # 只输出结果，不加任何前缀
        print(result)
    except Exception as e:
        # 恢复输出
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        print(f"错误：调用判断服务时发生错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
