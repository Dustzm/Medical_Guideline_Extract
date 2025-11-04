"""
OpenKG-ToolAgent集成mcp适配
医疗指南知识提取功能
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

from tool_service import knowledge_extract


def main():
    """命令行入口函数"""
    # 恢复标准输出以便显示结果和错误信息
    sys.stdout = original_stdout
    sys.stderr = original_stderr

    parser = argparse.ArgumentParser(description='医疗指南知识提取工具')
    parser.add_argument('content', nargs='*', help='要提取知识的医疗指南文本内容')
    parser.add_argument('--file', '-f', type=str, help='从文件读取医疗指南文本内容')
    parser.add_argument('--stdin', action='store_true', help='从标准输入读取医疗指南文本内容')
    parser.add_argument('--output', '-o', type=str, help='将结果输出到指定文件')

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

    # 调用knowledge_extract方法，屏蔽日志输出
    try:
        # 再次重定向输出以屏蔽运行时的日志
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull

            # 临时禁用日志输出
            logging.getLogger().setLevel(logging.CRITICAL + 1)

            result = knowledge_extract(content.strip())

            # 恢复输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # 准备输出内容，添加表头
        header = "entity\tproperty\tvalue\tentityTag\tvalueTag\tlevel"

        # 如果结果为空，只输出表头
        if not result.strip():
            output_content = header
        else:
            output_content = f"{header}\n{result.strip()}"

        # 输出结果
        if args.output:
            # 输出到文件
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                print(f"知识提取结果已保存到: {args.output}")
            except Exception as e:
                print(f"错误：写入文件时发生错误: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # 输出到标准输出
            print(output_content)

    except Exception as e:
        # 恢复输出
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        print(f"错误：调用知识提取服务时发生错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
