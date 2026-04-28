# MarkItDown Windows 文档转 Markdown 工具

[English](README.md) | [简体中文](README.zh-CN.md)

一个用于将 `.doc` 和 `.docx` 文档转换为 Markdown 的 Windows 桌面小工具。

## 功能特点

- 基于 Tkinter 的单窗口桌面应用
- 支持单个或多个文件批量转换
- `.docx` 直接通过 MarkItDown 转换
- `.doc` 先通过 LibreOffice 无界面转换为临时 `.docx`，再交给 MarkItDown
- 默认输出到源文件同目录
- 支持自定义输出目录
- 支持逐文件状态显示和整批任务结果汇总

## 运行要求

- Python 3.11+
- `markitdown`
- 如果需要打包，需要 `pyinstaller`
- 如果需要支持 `.doc`，请安装 LibreOffice，并确保 `soffice` 已加入 `PATH`

## 安装依赖

Windows 下执行：

```powershell
py -m pip install -r requirements.txt
```

## 本地运行

```powershell
py app.py
```

或者在 Windows 下直接双击：

- `run_windows.bat`

## 运行测试

当前自动化测试使用 Python 标准库的 `unittest`：

```powershell
set PYTHONPATH=.
py -m unittest discover -s tests -v
```

macOS 或 Linux 下执行：

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## 打包 Windows EXE

```powershell
pyinstaller markitdown_tool.spec
```

或者在 Windows 下直接双击：

- `build_windows.bat`

预期输出：

- `dist/MarkItDownTool.exe`

## 关于 `.doc`

- `.docx` 可以直接通过 MarkItDown 转换。
- `.doc` 需要先通过 LibreOffice 转成临时 `.docx`，再继续转换。
- 如果系统中没有 LibreOffice，程序会在开始转换前给出明确提示。

## Windows 快速开始

1. 安装 Python 3.11+。
2. 如果你需要支持 `.doc`，请安装 LibreOffice。
3. 打开项目目录。
4. 双击 `run_windows.bat`。

如果你想生成独立的 `.exe`：

1. 双击 `build_windows.bat`。
2. 等待打包完成。
3. 打开 `dist/MarkItDownTool.exe`。
