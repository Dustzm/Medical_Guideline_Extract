"""
演示如何通过代码调用命令行执行judge
"""
import subprocess
import sys
import os
from pathlib import Path


def call_judge_command(content=None, file_path=None, stdin_content=None):
    """
    通过代码调用命令行执行judge

    Args:
        content (str, optional): 直接提供的文本内容
        file_path (str, optional): 文件路径
        stdin_content (str, optional): 通过标准输入提供的内容

    Returns:
        str: 命令输出结果
    """
    # 获取judge.py的路径
    current_dir = Path(__file__).parent
    judge_script = current_dir / "judge.py"

    # 构建命令
    cmd = [sys.executable, str(judge_script)]

    # 准备标准输入
    stdin_input = None

    if content:
        cmd.append(content)
    elif file_path:
        cmd.extend(["--file", file_path])
    elif stdin_content:
        cmd.append("--stdin")
        stdin_input = stdin_content
    else:
        raise ValueError("必须提供content、file_path或stdin_content中的一个")

    # 执行命令
    try:
        process = subprocess.run(
            cmd,
            input=stdin_input,
            text=True,
            capture_output=True,
            encoding='utf-8',
            cwd=Path(__file__).parent.parent.parent  # 项目根目录
        )
        return process.stdout
    except Exception as e:
        return f"错误: {str(e)}"


def call_extract_command(content=None, file_path=None, stdin_content=None, output_file=None):
    """
    通过代码调用命令行执行extract

    Args:
        content (str, optional): 直接提供的文本内容
        file_path (str, optional): 文件路径
        stdin_content (str, optional): 通过标准输入提供的内容
        output_file (str, optional): 输出文件路径

    Returns:
        str: 命令输出结果
    """
    # 获取extract.py的路径
    current_dir = Path(__file__).parent
    extract_script = current_dir / "extract.py"

    # 构建命令
    cmd = [sys.executable, str(extract_script)]

    # 准备标准输入
    stdin_input = None

    if content:
        cmd.append(content)
    elif file_path:
        cmd.extend(["--file", file_path])
    elif stdin_content:
        cmd.append("--stdin")
        stdin_input = stdin_content
    else:
        raise ValueError("必须提供content、file_path或stdin_content中的一个")

    # 添加输出文件参数
    if output_file:
        cmd.extend(["--output", output_file])

    # 执行命令
    try:
        process = subprocess.run(
            cmd,
            input=stdin_input,
            text=True,
            capture_output=True,
            encoding='utf-8',
            cwd=Path(__file__).parent.parent.parent  # 项目根目录
        )
        return process.stdout
    except Exception as e:
        return f"错误: {str(e)}"


def test_judge_with_content():
    """测试直接提供内容的方式"""
    print("=== 测试judge直接提供内容 ===")

    # 测试医疗指南内容
    medical_text = """
    急性心肌梗死诊断和治疗指南
    1. 诊断标准
    - 持续性胸痛超过30分钟
    - 心电图显示ST段抬高
    - 心肌酶谱升高

    2. 治疗方案
    - 立即给予阿司匹林300mg嚼服
    - 尽快进行PCI介入治疗
    - 给予抗凝治疗
    """

    stdout = call_judge_command(content=medical_text)

    print(f"输入: {medical_text.strip()}")
    print(f"输出: {stdout}")
    print()


def test_extract_with_content():
    """测试extract直接提供内容的方式"""
    print("=== 测试extract直接提供内容 ===")

    # 测试医疗指南内容
    medical_text = """
    急性心肌梗死诊断和治疗指南
    诊断标准：持续性胸痛超过30分钟，心电图显示ST段抬高，心肌酶谱升高。
    治疗方案：立即给予阿司匹林300mg嚼服，尽快进行PCI介入治疗，给予抗凝治疗。
    """

    stdout = call_extract_command(content=medical_text)

    print(f"输入: {medical_text.strip()}")
    print(f"输出: {stdout}")
    print()


def test_extract_with_file():
    """测试extract文件输入和输出到文件"""
    print("=== 测试extract文件输入输出 ===")

    # 创建临时测试文件
    test_file = Path(__file__).parent / "test_extract_input.txt"
    output_file = Path(__file__).parent / "test_extract_output.txt"
    test_content = """
    高血压防治指南2024年版
    本指南适用于成年高血压患者的诊断和治疗。

    诊断标准：
    - 收缩压≥140mmHg和/或舒张压≥90mmHg
    - 多次测量确认诊断

    治疗原则：
    1. 生活方式干预
    2. 药物治疗
    3. 定期随访
    """

    try:
        # 写入测试文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content.strip())

        # 调用extract
        stdout = call_extract_command(file_path=str(test_file), output_file=str(output_file))

        print(f"文件内容: {test_content.strip()}")
        print(f"命令输出: {stdout}")

        # 读取输出文件内容
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            print(f"输出文件内容: {file_content}")

    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
        if output_file.exists():
            output_file.unlink()

    print()


def test_non_medical_content():
    """测试非医疗内容"""
    print("=== 测试非医疗内容 ===")

    non_medical = "这是一段普通的日常对话内容。"

    stdout = call_judge_command(content=non_medical)

    print(f"输入: {non_medical}")
    print(f"judge输出: {stdout}")
    print()


def main():
    """主测试函数"""
    print("开始测试命令行调用功能...\n")

    try:
        # 测试各种输入方式
        # test_judge_with_content()
        test_extract_with_content()
        # test_extract_with_file()
        # test_non_medical_content()

        # print("所有测试完成！")

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()