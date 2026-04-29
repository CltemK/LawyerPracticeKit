#!/usr/bin/env python3
"""
法院送达文书下载器 v7
从 zxfw.court.gov.cn 下载法院送达 PDF，支持多文件、OCR 识别与自动命名，
上传至飞书云空间，按案号归类（相同案号的文件放入同一文件夹）。

文件夹命名规则：{案号}_{最新送达日期}
飞书上传路径：用户云空间根目录下

用法:
    python court_doc_downloader.py "<法院送达链接>"
    python court_doc_downloader.py "<链接>" --parent-folder "<folder_token>"   # 指定飞书父文件夹
    python court_doc_downloader.py "<链接>" --skip-calendar
    python court_doc_downloader.py "<链接>" --files "1,3,5"
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import async_playwright

# ============================================================
# 配置
# ============================================================

DEFAULT_OUTPUT_DIR = Path(os.environ.get(
    "COURT_OUTPUT_DIR",
    "D:/多平台同步文件/05诉讼项目/11我的法院送达文件"
))

# lark-cli 路径（subprocess 调用时优先用完整路径）
def _get_lark_cli_path() -> str:
    if sys.platform == "win32":
        # 依次尝试常见安装位置
        for candidate in [
            Path(os.environ.get("LARK_CLI_PATH", "")),
            Path.home() / "AppData" / "Roaming" / "npm" / "lark-cli.cmd",
            Path(os.environ.get("APPDATA", "")) / "npm" / "lark-cli.cmd",
        ]:
            if candidate and candidate.is_file():
                return str(candidate)
        # 兜底：交给 PATH
        return "lark-cli"
    return "lark-cli"

LARK_CLI_FULLPATH = _get_lark_cli_path()

# 团队日历 ID（通过环境变量配置，不含默认值）
TEAM_CALENDAR_ID = os.environ.get("COURT_TEAM_CALENDAR_ID", "")

# 飞书上传父文件夹 token（通过环境变量或 CLI --parent-folder 传入）
FEISHU_PARENT_FOLDER_TOKEN = os.environ.get("COURT_FEISHU_FOLDER_TOKEN", "")

# 可选依赖
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


# ============================================================
# 飞书 Drive 操作：查找/创建文件夹、上传文件
# ============================================================

def find_feishu_folder(folder_name: str, parent_token: str = "") -> str | None:
    """
    在指定飞书文件夹中查找同名子文件夹，返回 folder_token；若找不到返回 None。
    parent_token 为空表示在云空间根目录搜索。
    """
    try:
        params = {"page_size": 200}
        if parent_token:
            params["folder_token"] = parent_token

        proc = subprocess.run(
            [LARK_CLI_FULLPATH, "drive", "files", "list",
             "--params", json.dumps(params),
             "--format", "json"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            print(f"    [WARN] 列出飞书文件夹失败: {proc.stderr[:200]}")
            return None

        # 解析 JSON（lark-cli --format json 输出纯 JSON）
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            print(f"    [WARN] 解析文件夹列表失败（非JSON）: {proc.stdout[:200]}")
            return None

        files = data if isinstance(data, list) else data.get("files", [])
        for f in files:
            if f.get("type") == "folder" and f.get("name") == folder_name:
                token = f.get("token", "")
                print(f"    找到已有文件夹: {folder_name} -> {token}")
                return token
        return None
    except Exception as e:
        print(f"    [WARN] 查找飞书文件夹异常: {e}")
        return None


def create_feishu_folder(folder_name: str, parent_token: str = "") -> str | None:
    """
    在飞书云空间创建文件夹，返回新文件夹的 token。
    parent_token 为空表示在根目录创建。
    """
    try:
        body = {"name": folder_name, "folder_token": parent_token or ""}
        proc = subprocess.run(
            [LARK_CLI_FULLPATH, "drive", "files", "create_folder",
             "--data", json.dumps(body, ensure_ascii=False)],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            print(f"    [WARN] 创建文件夹失败: {proc.stderr[:200]}")
            return None

        # 解析 JSON 输出
        try:
            data = json.loads(proc.stdout)
            # token 嵌套在 data.token 里，不是顶层
            token = (data.get("data") or {}).get("token", "")
            if not token:
                # 兜底用正则从原始文本中提取
                m = re.search(r'"token"\s*:\s*"([^"]+)"', proc.stdout)
                token = m.group(1) if m else ""
        except json.JSONDecodeError:
            # 兜底用正则从原始文本中提取
            m = re.search(r'"token"\s*:\s*"([^"]+)"', proc.stdout)
            token = m.group(1) if m else ""

        if token:
            print(f"    创建飞书文件夹成功: {folder_name} -> {token}")
            return token
        print(f"    [WARN] 创建文件夹未返回 token: {proc.stdout[:200]}")
        return None
    except Exception as e:
        print(f"    [WARN] 创建飞书文件夹异常: {e}")
        return None


def get_or_create_feishu_folder(folder_name: str, parent_token: str = "") -> str | None:
    """查找同名文件夹，若不存在则创建。返回 folder_token。"""
    existing = find_feishu_folder(folder_name, parent_token)
    if existing:
        return existing
    return create_feishu_folder(folder_name, parent_token)


def upload_file_to_feishu(local_path: str, file_name: str, folder_token: str = "") -> dict:
    """
    将本地文件上传到飞书云空间（使用 +upload shortcut）。
    返回 {"ok": True, "url": "...", "token": "..."} 或 {"ok": False, "error": "..."}
    """
    local_path = Path(local_path)
    if not local_path.exists():
        return {"ok": False, "error": f"本地文件不存在: {local_path}"}

    # lark-cli 的 +upload 要求 --file 为相对路径，且当前目录不能有中文/特殊字符
    # 因此复制到临时目录再上传
    import tempfile, uuid, os, shutil
    tmp_dir = Path(tempfile.gettempdir())
    tmp_name = f"court_upload_{uuid.uuid4().hex[:8]}.pdf"
    tmp_path = tmp_dir / tmp_name

    try:
        shutil.copy2(local_path, tmp_path)

        # 从临时目录执行 lark-cli，这样 --file 可以用相对路径
        cmd = [
            LARK_CLI_FULLPATH, "drive", "+upload",
            "--file", tmp_name,   # 相对路径
            "--name", file_name,
        ]
        if folder_token:
            cmd.extend(["--folder-token", folder_token])

        proc = subprocess.run(
            cmd, cwd=str(tmp_dir),   # 在临时目录执行
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace",
        )

        # 从 stdout 提取 JSON（PowerShell 输出可能带 CLIXML 头）
        raw = proc.stdout or ""
        # 去掉 PowerShell 的 CLIXML 标签
        json_str = re.sub(r'#< CLIXML[^>]*>[\s\S]*?</Objs>', '', raw)
        json_str = json_str.strip()

        if proc.returncode != 0:
            err = (proc.stderr or json_str or "")[:300]
            print(f"    [WARN] 上传失败: {err}")
            return {"ok": False, "error": err}

        # 解析 JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return {"ok": False, "error": f"JSON解析失败: {json_str[:200]}"}

        # 提取 file_token 和 url
        if not data.get("ok", False):
            err = data.get("error", {}).get("message", str(data))[:200]
            print(f"    [WARN] 上传失败: {err}")
            return {"ok": False, "error": err}

        file_token = data.get("data", {}).get("file_token", "")
        file_url = f"https://feishu.cn/drive/file/{file_token}" if file_token else ""
        print(f"    上传成功: {file_name} -> {file_url}")
        return {"ok": True, "token": file_token, "url": file_url}

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "上传超时（文件可能过大）"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        # 清理临时文件
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

# ============================================================
# Step 1: 调用法院 API 获取文件列表
# ============================================================

def extract_params_from_url(url: str) -> dict:
    """
    从送达链接中提取 qdbh, sdbh, sdsin 参数。

    URL 格式: https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=...&sdbh=...&sdsin=...
    参数在 fragment（#）后面，需要特殊处理。
    """
    # 方法：从 URL 中直接用正则提取
    params = {}
    for key in ['qdbh', 'sdbh', 'sdsin']:
        # 匹配 key=value，支持在 fragment 或 query 中
        pattern = rf'(?:[\?&#])(?:{key})=([a-zA-Z0-9]+)'
        match = re.search(pattern, url)
        if match:
            params[key] = match.group(1)

    # 如果正则没找到，尝试传统解析（作为兜底）
    if len(params) < 3:
        parsed = urllib.parse.urlparse(url)
        # fragment 中的查询参数（格式：#/path?key=value&key2=value2）
        if '#' in url:
            fragment_part = url.split('#', 1)[1]  # 取 # 后面的全部内容
            # 去掉前面的路径部分（/pagesAjkj/...），找 ? 后的参数
            if '?' in fragment_part:
                fragment_query = fragment_part.split('?', 1)[1]
                for key in ['qdbh', 'sdbh', 'sdsin']:
                    if key not in params:
                        m = re.search(rf'{key}=([a-zA-Z0-9]+)', fragment_query)
                        if m:
                            params[key] = m.group(1)

    return params


def get_document_list_from_api(url: str) -> dict:
    """
    调用法院 API 获取送达文件列表。

    Returns:
        {
            "ok": bool,
            "files": [{"wjlj": URL, "c_wsmc": 名称, "c_fymc": 法院, "c_wsbh": ID}, ...],
            "error": str
        }
    """
    params = extract_params_from_url(url)
    if not all(k in params for k in ['qdbh', 'sdbh', 'sdsin']):
        return {"ok": False, "files": [], "error": f"URL 参数不完整: {params}"}

    api_url = "https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew"
    payload = {
        "sdbh": params["sdbh"],
        "qdbh": params["qdbh"],
        "sdsin": params["sdsin"],
    }

    print(f"正在获取送达文件列表...")
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://zxfw.court.gov.cn/zxfw/",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "files": [], "error": f"API 请求失败: {e}"}

    if result.get("code") != 200 or not result.get("success"):
        return {"ok": False, "files": [], "error": f"API 返回错误: {result.get('msg', result)}"}

    raw_files = result.get("data", [])
    if not raw_files:
        return {"ok": False, "files": [], "error": "文件列表为空"}

    files = []
    for item in raw_files:
        files.append({
            "wjlj": item.get("wjlj", ""),           # PDF 直链
            "c_wsmc": item.get("c_wsmc", ""),       # 文书名称
            "c_fymc": item.get("c_fymc", ""),       # 法院名称
            "c_wsbh": item.get("c_wsbh", ""),       # 文书编号
            "c_stbh": item.get("c_stbh", ""),       # 存储路径
            "dt_cjsj": item.get("dt_cjsj", ""),     # 创建时间
        })

    print(f"找到 {len(files)} 个送达文书:")
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f['c_wsmc']} ({f['c_fymc']})")

    return {"ok": True, "files": files}


# ============================================================
# Step 2: 下载单个 PDF 文件（直接下载，不走 Playwright）
# ============================================================

def download_pdf_direct(wjlj: str, filename: str, output_dir: Path) -> dict:
    """直接通过 HTTP 下载 PDF（URL 已有签名）"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 避免同名覆盖：如果文件已存在，自动加序号
    filepath = output_dir / filename
    if filepath.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1
        while filepath.exists():
            filepath = output_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        filename = filepath.name
        print(f"  文件已存在，重命名为: {filename}")

    filepath.write_bytes(b"")  # 占位

    try:
        req = urllib.request.Request(
            wjlj,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://zxfw.court.gov.cn/",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            filepath.write_bytes(data)
            print(f"  下载成功: {filename} ({len(data):,} bytes)")
            return {"ok": True, "filepath": str(filepath), "size": len(data)}
    except Exception as e:
        filepath.unlink(missing_ok=True)
        return {"ok": False, "error": str(e)}


# ============================================================
# Step 3: PDF 文字提取（pdfplumber + MinerU）
# ============================================================

# MinerU script path（优先使用环境变量指定路径）
MINERU_SCRIPT = os.environ.get(
    "MINERU_EXTRACT_SCRIPT",
    str(Path(__file__).parent / "mineru_parse_documents.py")
)


def quick_ocr_for_case_no(pdf_path: str) -> str | None:
    """
    快速从 PDF 提取案号（只读前2页 pdfplumber，不调用 MinerU OCR）。
    用于在上传前预先识别"未分类"文件夹的正确案号。
    Returns: 案号字符串（如"（2026）鄂0191民初2332号"）或 None。
    """
    if not PDFPLUMBER_AVAILABLE:
        return None
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages[:2]:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            if not text.strip():
                return None
            # 用同一的 extract_case_no_from_wsmc 从 OCR 文本中提取案号
            return extract_case_no_from_wsmc(text)
    except Exception as e:
        print(f"  [WARN] quick_ocr 失败: {e}")
        return None


def rename_feishu_folder_api(folder_token: str, new_name: str) -> bool:
    """
    调用飞书 PATCH /open-apis/drive/v1/files/{folder_token} API 重命名文件夹。
    返回 True 成功，False 失败。
    """
    import os, requests

    # 从 lark-cli 的缓存/配置中读取 access_token
    # lark-cli 默认把 token 存到 ~/.lark-cli/tokens.json
    token_file = Path.home() / ".lark-cli" / "tokens.json"
    access_token = None
    if token_file.exists():
        try:
            tok_data = json.loads(token_file.read_text(encoding="utf-8"))
            # 优先取 user token（可写），其次取 bot token
            access_token = tok_data.get("user_access_token") or tok_data.get("access_token")
        except Exception:
            pass

    if not access_token:
        print(f"  [WARN] 未找到 lark access_token，无法 rename 文件夹")
        return False

    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{folder_token}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"name": new_name, "type": "folder"}
    try:
        resp = requests.patch(url, headers=headers, json=payload, timeout=15)
        data = resp.json()
        if data.get("code") == 0:
            print(f"  文件夹重命名成功: {new_name}")
            return True
        else:
            print(f"  [WARN] 重命名失败: {data.get('msg', data)}")
            return False
    except Exception as e:
        print(f"  [WARN] 重命名请求异常: {e}")
        return False


def extract_text_from_pdf(pdf_path, pdf_url=None) -> dict:
    """
    从 PDF 提取文字。策略：
    1. pdfplumber 直接提取（文本型 PDF）
    2. 若提取不足，调用 MinerU parse API 对 PDF 直链 URL 做 OCR（扫描型 PDF）
    """
    if not PDFPLUMBER_AVAILABLE:
        return {"ok": False, "error": "pdfplumber 未安装"}

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return {"ok": False, "error": f"文件不存在: {pdf_path}"}

    print(f"  正在提取文字: {pdf_path.name}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"  PDF 共 {len(pdf.pages)} 页")
            all_text = []
            low_text_pages = []

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if len(text.strip()) > 30:
                    all_text.append(f"[第{i+1}页]\n{text}")
                else:
                    low_text_pages.append(i + 1)
                    all_text.append(f"[第{i+1}页 - 无文字]")

            full_text = "\n".join(all_text)
            total_chars = sum(len(t) for t in all_text)

            # pdfplumber 提取总量超过 200 字，认为是文本型 PDF
            if total_chars > 200:
                print(f"  pdfplumber 提取约 {total_chars} 字（文本型）")
                return {"ok": True, "content": full_text, "method": "pdfplumber"}

            # 文字不足，调用 MinerU OCR（通过 PDF 直链 URL）
            if not pdf_url:
                print(f"  pdfplumber 提取过少（{total_chars} 字），无可用 PDF URL，跳过 MinerU OCR")
                return {"ok": True, "content": full_text, "method": "pdfplumber_fallback"}

            print(f"  pdfplumber 提取过少（{total_chars} 字），调用 MinerU OCR...")
            ocr_text = ocr_pdf_with_mineru(pdf_url)
            if ocr_text and len(ocr_text.strip()) > 100:
                print(f"  MinerU 提取约 {len(ocr_text)} 字")
                return {"ok": True, "content": ocr_text, "method": "MinerU"}

            # 兜底：返回已有的少量文字
            print(f"  MinerU OCR 未能提取更多内容")
            return {"ok": True, "content": full_text, "method": "pdfplumber_fallback"}

    except Exception as e:
        return {"ok": False, "error": f"PDF 解析失败: {e}"}


def ocr_pdf_with_mineru(pdf_url: str) -> str:
    """
    通过 MinerU parse API 对 PDF 直链 URL 进行 OCR 文字提取。

    MinerU 会自动完成：下载 PDF → 页面截图 → OCR 识别 → 返回 Markdown 文本。
    所需依赖已通过 skill 本地 .env 配置（MINERU_TOKEN 等环境变量）。
    """
    import subprocess, json

    mineru_script = MINERU_SCRIPT

    cmd = [
        sys.executable,
        mineru_script,
        "--file-sources", pdf_url,
        "--language", "ch",
        "--enable-ocr",
        "--model-version", "pipeline",
        "--emit-markdown",
        "--max-chars", "50000",
        "--timeout", "600",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=660,
            encoding="utf-8",
            errors="replace",
        )

        if proc.returncode != 0:
            err = (proc.stderr or "")[:500]
            print(f"    MinerU 调用失败（exit {proc.returncode}）: {err}")
            return ""

        # 解析 JSON 输出
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError:
            print(f"    MinerU 输出解析失败: {proc.stdout[:200]}")
            return ""

        if not result.get("ok", False):
            errors = result.get("errors", [])
            if errors:
                print(f"    MinerU 错误: {errors[0].get('error', errors[0])}")
            return ""

        items = result.get("items", [])
        if not items:
            return ""

        # 取第一个 item 的 markdown 文本
        markdown_text = items[0].get("markdown", "")
        if not markdown_text:
            # 尝试从本地 markdown_path 读取
            md_path = items[0].get("markdown_path", "")
            if md_path and Path(md_path).exists():
                markdown_text = Path(md_path).read_text(encoding="utf-8", errors="replace")

        return markdown_text

    except subprocess.TimeoutExpired:
        print(f"    MinerU 调用超时（660s）")
        return ""
    except Exception as e:
        print(f"    MinerU 调用异常: {e}")
        return ""


# ============================================================
# Step 4: 文书类型识别与字段提取
# ============================================================

def _has_case_number(text: str) -> bool:
    """检查文本中是否包含案号"""
    case_patterns = [
        r'[（(]\s*\d{2,4}\s*[)）]\s*\S?\s*\d{2,6}\s*\S{0,5}\s*\d{1,5}\s*号',
        r'[（(]\s*\d{2,4}\s*[)）]\s*\S{0,10}\s*\d{1,10}\s*号',
    ]
    for p in case_patterns:
        if re.search(p, text):
            return True
    return False


def _has_party_info(text: str) -> bool:
    """检查文本中是否包含当事人信息（原告/被告 或 上诉人/被上诉人）"""
    return ("原告" in text and "被告" in text) or \
           ("上诉人" in text and "被上诉人" in text)


def _build_case_metadata_txt(results: list, case_no: str, case_folder_name: str) -> str:
    """
    为整个案件生成元数据 TXT 内容，供后续读取和用户编辑。
    上传到飞书时同时创建此文件。
    """
    lines = []
    today = datetime.now().strftime("%Y-%m-%d")

    lines.append(f"# 案件信息  （自动生成于 {today}）")
    lines.append(f"# 本文件由 court-doc-downloader 自动创建")
    lines.append("# " + "=" * 50)
    lines.append("")

    # ── 基础信息 ──
    lines.append("[基本信息]")
    lines.append(f"案号: {case_no or '未知'}")
    lines.append("")

    # ── 当事人（供用户编辑）──
    lines.append("[当事人]")
    lines.append(f"我方当事人: ")
    lines.append(f"对方当事人: ")
    lines.append("")

    # ── 案件信息：从传票/判决书中提取 ──
    lines.append("[案件信息]")

    # 案由
    cause = None
    hearing_date = None
    court_name = None
    plaintiff = None
    defendant = None

    for r in results:
        fields = r.get("fields", {})
        if not fields:
            continue
        if not cause:
            cause = fields.get("cause_of_action") or fields.get("case_reason") or fields.get("案由")
        if not hearing_date:
            hearing_date = fields.get("hearing_date")
        if not court_name:
            court_name = fields.get("court_name")
        if not plaintiff:
            plaintiff = fields.get("plaintiff") or fields.get("上诉人") or fields.get("原告")
        if not defendant:
            defendant = fields.get("defendant") or fields.get("被上诉人") or fields.get("被告")

    lines.append(f"案由: {cause or ''}")
    lines.append(f"开庭时间: {hearing_date or ''}")
    lines.append(f"受理法院: {court_name or ''}")
    lines.append("")

    # ── 我方/对方当事人（从判决书提取供参考）──
    lines.append("[当事人（供参考）]")
    lines.append(f"# 以下由文书自动识别，建议确认后在上方[当事人]区块填写")
    lines.append(f"原告/上诉人: {plaintiff or ''}")
    lines.append(f"被告/被上诉人: {defendant or ''}")
    lines.append("")

    # ── 历次送达文书记录 ──
    lines.append("[送达记录]")
    lines.append(f"# 格式：送达日期 | 文书类型 | 文件名")
    lines.append(f"# 生成时间: {today}")
    lines.append("")
    lines.append(f"{'送达日期':<14} {'文书类型':<8} {'文件名'}")
    lines.append("-" * 60)

    # 按送达日期排序
    sorted_results = sorted(results, key=lambda x: x.get("dt_cjsj", ""))

    for r in sorted_results:
        dt = r.get("dt_cjsj", "")
        if dt:
            # 格式化日期
            try:
                dt_obj = parse_dt_cjsj(dt)
                if dt_obj:
                    dt = dt_obj.strftime("%Y-%m-%d")
            except Exception:
                pass
        doc_type = r.get("doc_type", "其他")
        name = r.get("name", "未知")
        feishu_url = r.get("feishu_url", "")
        lines.append(f"{dt or '未知':<14} {doc_type:<8} {name}")
        if feishu_url:
            lines.append(f"{'':14} {'':8} 飞书: {feishu_url}")

    lines.append("")
    lines.append("[备注]")
    lines.append(f"# 飞书文件夹: {case_folder_name}")
    lines.append(f"# 共 {len(results)} 份送达文书")

    return "\n".join(lines)


def classify_and_extract(content: str) -> dict:
    """
    识别文书类型（传票/判决书/其他）并提取关键字段。

    判决书识别规则（必须同时满足）：
      1. PDF 第一页包含"人民法院判决书"字样
      2. 包含原告/被告 或 上诉人/被上诉人
      3. 包含案号
    以上三条缺少任意一条，则不认定为判决书。
    """
    first_page = content[:1500]  # 第一页内容

    # —— 判决书严格判断（三条必须同时满足）——
    has_title       = "人民法院判决书" in first_page
    has_parties     = _has_party_info(content)
    has_case_no     = _has_case_number(content)
    is_judgment     = has_title and has_parties and has_case_no

    # —— 传票判断（标题含"传票"）——
    title_area = first_page.lower()
    is_summons = "传票" in title_area

    # —— 综合判定 ——
    if is_judgment:
        doc_type = "判决书"
    elif is_summons:
        doc_type = "传票"
    elif any(kw in title_area for kw in ["须知", "通知", "指南", "规定", "告知书", "权利义务"]):
        doc_type = "其他"
    else:
        # 兜底：按关键词打分
        summons_kw  = ["传票", "开庭通知", "应诉", "举证通知"]
        judgment_kw = ["判决书", "本院认为", "判决如下", "上诉人", "被上诉人"]
        s_score = sum(1 for kw in summons_kw  if kw in content)
        j_score = sum(1 for kw in judgment_kw if kw in content)
        doc_type = "传票" if s_score > j_score else ("判决书" if j_score > s_score else "其他")

    fields = {}
    if doc_type == "传票":
        fields = extract_summons_fields(content)
    elif doc_type == "判决书":
        fields = extract_judgment_fields(content)

    return {"type": doc_type, "fields": fields}


def extract_summons_fields(content: str) -> dict:
    """从传票提取法院名称、开庭日期、案号"""
    court_name = None
    hearing_date = None

    court_patterns = [
        r'([^\s]{2,6}省[^\s]{2,10}市[^\s]{2,10}(?:区|县|市)人民法院)',
        r'([^\s]{2,6}市[^\s]{2,10}(?:区|县|市)人民法院)',
        r'([^\s]{2,6}中级人民法院)',
        r'([^\s]{2,6}铁路运输法院)',
        r'(湖北省[^\s]{2,10}人民法院)',
        r'(武汉市[^\s]{2,10}人民法院)',
        r'([^\s]{2,10}法院)',
    ]
    for pattern in court_patterns:
        match = re.search(pattern, content)
        if match:
            court_name = match.group(1).strip()
            break

    # 日期正则：兼容"2026年4月16日"和"2026 年 04 月 16 日"和"2026-04-16"
    # 也兼容"14:50"或"14时30分"时间格式
    date_patterns = [
        # 2026年4月16日14时30分 / 2026 年 04 月 16 日 14 时 30 分
        r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{0,2}\s*分?)',
        # 2026年4月16日14:50 / 2026 年 04 月 16 日 14:50
        r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}[:：]\d{2})',
        # 2026年4月16日14时
        r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时)',
        # 2026年4月16日（无时间）
        r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)',
        # 2026-04-16
        r'(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            hearing_date = match.group(1).strip()
            # 清除多余空格
            hearing_date = re.sub(r'\s+', '', hearing_date)
            break

    # 如果日期中没有时间，尝试在"应到时间"附近找
    if hearing_date and ':' not in hearing_date and '时' not in hearing_date:
        time_m = re.search(r'(\d{1,2}[:：]\d{2})', content)
        if time_m:
            hearing_date += time_m.group(1).replace('：', ':')
        else:
            time_m = re.search(r'(\d{1,2}时\d{0,2}分?)', content)
            if time_m:
                hearing_date += time_m.group(1)

    case_no = None
    for pattern in [
        # 案号含空格：（2026）鄂 0103 行初 23 号
        r'((?:20\d{2}|19\d{2})\s*[（(]\s*\d{2,4}\s*[)）]\s*\S{0,5}\s*\d{2,6}\s*\S{0,5}\s*\d{1,5}\s*号)',
        # 标准案号：（2026）鄂0103行初23号
        r'((?:20\d{2}|19\d{2})\s*[（(]\s*\d{2,4}\s*[)）]\s*\S{0,10}\s*\d{1,10}\s*号)',
        r'(案\s*号[：:]\s*\S+)',
    ]:
        match = re.search(pattern, content)
        if match:
            case_no = match.group(1).strip()
            # 清除多余空格
            case_no = re.sub(r'\s+', '', case_no)
            break

    return {
        "court_name": court_name or "未知法院",
        "hearing_date": hearing_date or "未知日期",
        "case_no": case_no,
    }


def extract_judgment_fields(content: str) -> dict:
    """从判决书提取原告、被告、案由"""
    cause_of_action = None
    for pattern in [r'案由[：:]\s*([^\n]{2,20})', r'案由为\s*([^\n]{2,20})',
                     r'本案案由[是为]?\s*([^\n]{2,20})']:
        match = re.search(pattern, content)
        if match:
            cause_of_action = match.group(1).strip()
            break
    if not cause_of_action:
        cause_of_action = "纠纷"

    plaintiff = None
    defendant = None

    firm_pattern = r'湖北瀛楚律师事务所|瀛楚律师事务所'
    firm_match = re.search(firm_pattern, content)
    if firm_match:
        nearby = content[max(0, firm_match.start()-400): firm_match.end()+400]
        for pat in [r'原告[：:]\s*([^\n，,；;]{2,30})', r'上诉人[（(][^）)]*[)）][：:]\s*([^\n，,；;]{2,30})']:
            m = re.search(pat, nearby)
            if m:
                plaintiff = re.sub(r'[（(][^）)]*[)）]', '', m.group(1).strip())
                break

    if not plaintiff:
        m = re.search(r'原告[：:]\s*([^\n，,；;]{2,30})', content)
        if m:
            plaintiff = m.group(1).strip()

    for pat in [r'被告[：:]\s*([^\n，,；;]{2,30})', r'被上诉人[：:]\s*([^\n，,；;]{2,30})']:
        m = re.search(pat, content)
        if m:
            defendant = re.sub(r'[（(][^）)]*[)）]', '', m.group(1).strip())
            break

    return {
        "plaintiff": plaintiff or "未知原告",
        "defendant": defendant or "未知被告",
        "cause_of_action": cause_of_action,
        "read_date": datetime.now().strftime("%Y年%m月%d日"),
    }


# ============================================================
# Step 5: 文件重命名
# ============================================================

def rename_file(original_path: str, doc_type: str, fields: dict, doc_name: str) -> str:
    """根据文书类型重命名文件"""
    original = Path(original_path)
    parent = original.parent

    def clean(s):
        return re.sub(r'[<>:"/\\|?*]', '-', str(s))

    if doc_type == "传票":
        hd = clean(fields.get("hearing_date", "未知日期"))
        cn = clean(fields.get("court_name", "未知法院"))
        new_name = f"{hd}_{cn}_传票.pdf"
    elif doc_type == "判决书":
        pl = clean(fields.get("plaintiff", "未知原告"))
        df = clean(fields.get("defendant", "未知被告"))
        ca = clean(fields.get("cause_of_action", "纠纷"))
        suffix = "" if ca.endswith("纠纷") else (ca + "纠纷" if ca else "纠纷")
        rd = fields.get("read_date", datetime.now().strftime("%Y年%m月%d日"))
        new_name = f"{pl}与{df}{suffix}_{rd}.pdf"
    else:
        # 其他文书：使用原 API 名称或原始文件名
        new_name = clean(doc_name) + ".pdf" if doc_name else original.name

    # 避免重名
    new_path = parent / new_name
    if new_path.exists() and new_path.resolve() != original.resolve():
        stem = Path(new_name).stem
        counter = 1
        while new_path.exists():
            new_name = f"{stem}_{counter}{Path(new_name).suffix}"
            new_path = parent / new_name
            counter += 1

    if new_path.resolve() != original.resolve():
        shutil.move(str(original), str(new_path))
        print(f"  重命名为: {new_name}")

    return str(new_path)


# ============================================================
# Step 6: 飞书日历创建
# ============================================================

def create_feishu_calendar_event(fields: dict, case_no_api: str = "") -> dict:
    """为传票创建飞书开庭日程（写入团队日历）"""
    hearing_date_str = fields.get("hearing_date", "")
    court_name = fields.get("court_name", "")
    case_no = fields.get("case_no", "") or case_no_api

    if not hearing_date_str or hearing_date_str == "未知日期":
        print("  [WARN] 未能提取开庭日期，跳过日历创建")
        return {"ok": False, "error": "开庭日期缺失"}

    # 解析日期（已去除空格，格式如: 2026年04月16日14:50 或 2026年4月16日14时30分）
    date_patterns = [
        # 2026年04月16日14时30分
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})时(\d{0,2})分?', None),
        # 2026年04月16日14:50
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})[:：](\d{2})', None),
        # 2026年04月16日14时
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})时', None),
        # 2026年04月16日
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', None),
        # 2026-04-16
        (r'(\d{4})-(\d{2})-(\d{2})', None),
    ]

    dt_start = None
    for pattern, _ in date_patterns:
        m = re.match(pattern, hearing_date_str)
        if m:
            groups = m.groups()
            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            hour = int(groups[3]) if len(groups) > 3 and groups[3] else 9
            minute = int(groups[4]) if len(groups) > 4 and groups[4] else 0
            try:
                dt_start = datetime(year, month, day, hour, minute)
                dt_end = dt_start + timedelta(hours=2)
            except Exception:
                continue
            break

    if not dt_start:
        print(f"  [WARN] 无法解析开庭日期: {hearing_date_str}")
        return {"ok": False, "error": "日期解析失败"}

    # 用案号构建清晰标题（案号来自 API 或 OCR，优先使用 API 案号）
    if case_no:
        # 去掉案号中的空格，使格式清晰
        case_no_clean = re.sub(r'\s+', '', case_no)
        title = f"开庭：{case_no_clean}"
    else:
        title = f"开庭：{court_name}"

    description_parts = [f"法院：{court_name}"]
    if case_no:
        description_parts.append(f"案号：{case_no_clean}")
    description_parts.append(f"开庭日期：{hearing_date_str}")
    description = "\n".join(description_parts)

    # 构建请求体
    body = {
        "summary": title,
        "description": description,
        "start_time": {
            "timestamp": str(int(dt_start.timestamp())),
            "timezone": "Asia/Shanghai",
        },
        "end_time": {
            "timestamp": str(int(dt_end.timestamp())),
            "timezone": "Asia/Shanghai",
        },
    }
    params = json.dumps({"calendar_id": TEAM_CALENDAR_ID})
    body_json = json.dumps(body)

    print(f"  创建飞书日程（团队日历）: {title} {dt_start.strftime('%Y-%m-%d %H:%M')}")

    try:
        proc = subprocess.run(
            [LARK_CLI_FULLPATH, "calendar", "events", "create",
             "--params", params, "--data", body_json],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        # 检查成功（兼容 JSON 中冒号后有无空格）
        if proc.returncode == 0 and re.search(r'"code"\s*:\s*0', proc.stdout):
            print(f"  [OK] 日程创建成功")
            return {"ok": True, "title": title, "start": dt_start.isoformat()}
        else:
            err = (proc.stderr or proc.stdout or "")[:300]
            print(f"  [WARN] 日程创建失败: {err}")
            return {"ok": False, "error": err}
    except FileNotFoundError:
        print("  [WARN] lark-cli 未找到，跳过日历创建")
        return {"ok": False, "error": "lark-cli 未安装"}
    except Exception as e:
        print(f"  [WARN] 日历异常: {e}")
        return {"ok": False, "error": str(e)}


# ============================================================
# 主流程：处理单个文件
# ============================================================

def process_single_file(
    file_info: dict,
    temp_dir: Path,
    feishu_folder_token: str,
    skip_calendar: bool,
    case_tag: str = "",
    case_no_api: str = "",
) -> dict:
    """
    处理单个送达文书：下载（到临时目录）→ OCR → 识别 → 命名 → 上传飞书 → 清理临时文件。
    feishu_folder_token: 飞书目标文件夹 token。
    返回结果中 filepath 为空（文件已清理），feishu_url 为上传后的链接。
    """
    result = {
        "name": file_info["c_wsmc"],
        "court": file_info["c_fymc"],
        "success": False,
        "filepath": None,       # 本地路径（处理完毕后清空）
        "feishu_url": None,     # 飞书链接
        "feishu_token": None,   # 飞书 file_token
        "feishu_folder_token": feishu_folder_token,  # 所属飞书文件夹
        "doc_type": None,
        "fields": {},
        "calendar_event": None,
        "error": None,
        "case_no": None,        # 案号
        "dt_cjsj": file_info.get("dt_cjsj", ""),  # 送达时间
    }

    wjlj = file_info["wjlj"]
    c_wsmc = file_info["c_wsmc"]

    # 生成初始文件名
    filename = re.sub(r'[<>:"/\\|?*]', '_', c_wsmc) + ".pdf"

    print(f"\n--- 处理: {c_wsmc} ---")

    # 下载到临时目录
    dl = download_pdf_direct(wjlj, filename, temp_dir)
    if not dl["ok"]:
        result["error"] = f"下载失败: {dl.get('error')}"
        return result

    pdf_path = dl["filepath"]

    # 文字提取（OCR）
    text_result = extract_text_from_pdf(pdf_path, pdf_url=wjlj)
    if not text_result.get("ok"):
        # 下载成功但 OCR 失败，仍继续上传飞书
        content = ""
        print(f"  [WARN] 文字提取失败: {text_result.get('error')}，仍继续上传")
    else:
        content = text_result["content"]
        print(f"  提取约 {len(content)} 字（{text_result.get('method', '?')}）")

    # 文书识别
    if content:
        classification = classify_and_extract(content)
        doc_type = classification["type"]
        fields = classification["fields"]
    else:
        doc_type = "其他"
        fields = {}

    result["doc_type"] = doc_type
    result["fields"] = fields
    print(f"  类型: {doc_type}")
    if fields:
        print(f"  字段: {fields}")

    # 提取案号（用于区分不同案件的同名文书）
    case_no_in_content = None
    for pattern in [
        r'[（(]\s*\d{2,4}\s*[)）]\s*\S?\s*\d{0,4}\s*\S{0,5}\s*\d{0,4}\s*\S{0,5}\s*\d{1,5}\s*号',
        r'[（(]\s*\d{2,4}\s*[)）]\s*\S{0,5}\s*\d{2,6}\s*\S{0,5}\s*\d{1,5}\s*号',
        r'[（(]\s*\d{2,4}\s*[)）]\s*\S{0,10}\s*\d{1,10}\s*号',
    ]:
        m = re.search(pattern, content)
        if m:
            case_no_in_content = re.sub(r'\s+', '', m.group(0))
            break

    # 记录案号到 result（供元数据 TXT 使用）
    # 优先级：调用参数 unified_case_no（用户通过 --case-no 提供）> OCR 提取 > API 提取
    result["case_no"] = case_no_in_content

    # 重命名文件
    if doc_type != "传票" and doc_type != "判决书" and case_no_in_content:
        final_path = rename_file(pdf_path, doc_type, fields, f"{c_wsmc}_{case_no_in_content}")
    else:
        final_path = rename_file(pdf_path, doc_type, fields, c_wsmc)

    final_name = Path(final_path).name

    # 上传到飞书
    print(f"  上传到飞书文件夹: {feishu_folder_token or '(根目录)'}")
    feishu_result = upload_file_to_feishu(final_path, final_name, feishu_folder_token)
    if feishu_result.get("ok"):
        result["feishu_url"] = feishu_result.get("url", "")
        result["feishu_token"] = feishu_result.get("token", "")
        print(f"  飞书链接: {result['feishu_url']}")
    else:
        result["error"] = f"飞书上件失败: {feishu_result.get('error', '未知错误')}"
        # 上传失败仍然保留本地文件，不清理
        result["filepath"] = final_path
        return result

    # 清理本地临时文件（上传成功后删除，避免占用空间）
    try:
        Path(final_path).unlink(missing_ok=True)
        print(f"  已清理本地临时文件: {final_name}")
    except Exception as e:
        print(f"  [WARN] 清理本地文件失败: {e}")

    result["filepath"] = None  # 确认已无本地路径
    result["success"] = True

    # 传票建日历
    if doc_type == "传票" and not skip_calendar:
        cal = create_feishu_calendar_event(fields, case_no_api=case_no_api)
        result["calendar_event"] = cal
    elif doc_type == "传票":
        print("  跳过日历（--skip-calendar）")

    return result


# ============================================================
# CLI 入口
# ============================================================

def extract_case_no_from_wsmc(wsmc: str) -> str | None:
    """从文书名称（c_wsmc）中提取案号"""
    for pattern in [
        # 标准案号含空格：（2026）鄂 0103 行初 23 号
        r'[（(]\s*\d{2,4}\s*[)）]\s*[^\s]{0,5}\s*\d{2,6}\s*[^\s]{0,5}\s*\d{1,5}\s*号',
        # 标准案号：（2026）鄂0103行初23号
        r'[（(]\s*\d{2,4}\s*[)）]\s*\S{0,10}\s*\d{1,10}\s*号',
    ]:
        m = re.search(pattern, wsmc)
        if m:
            return re.sub(r'\s+', '', m.group(0))
    return None


def parse_dt_cjsj(dt_cjsj: str) -> datetime | None:
    """
    解析 dt_cjsj（送达文件创建时间）返回 datetime。
    格式如: '2026-04-11 10:30:00' 或 '2026-04-11T10:30:00' 等。
    """
    if not dt_cjsj:
        return None
    # 尝试多种格式
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"]:
        try:
            return datetime.strptime(dt_cjsj[:19], fmt)
        except ValueError:
            pass
    # 兜底：取前10位当日期
    if len(dt_cjsj) >= 10:
        try:
            return datetime.strptime(dt_cjsj[:10], "%Y-%m-%d")
        except ValueError:
            pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="法院送达文书下载器 v8（飞书云空间 + 按案号归类 + 支持本地图片）"
    )
    parser.add_argument("url", nargs="?", default=None, help="法院送达页面完整 URL")
    parser.add_argument("--local-file", default=None,
                        help="处理本地上传的传票图片/PDF（微信传来的附件等）")
    parser.add_argument("--parent-folder", default=None,
                        help='飞书云空间父文件夹 token（默认使用环境变量 COURT_FEISHU_FOLDER_TOKEN）')
    parser.add_argument("--skip-calendar", action="store_true", help="跳过飞书日历创建")
    parser.add_argument("--local-only", action="store_true",
                        help="仅保存本地，不上传飞书云空间")
    parser.add_argument("--local-dir", default=None,
                        help="本地保存目录（默认: 环境变量 COURT_OUTPUT_DIR 或 ./court_documents）")
    parser.add_argument("--files", "-f", default=None, help="要下载的文件编号，如 1,3,5（默认全部）")
    parser.add_argument("--case-no", default=None,
                        help="案号（从用户短信中提取，如（2026）鄂0191民初2844号）。"
                             "优先使用此参数；未提供时尝试从文书名OCR提取。")

    args = parser.parse_args()

    # ── 本地文件模式（微信图片等）──────────────────────────────
    if args.local_file:
        from PIL import Image  # 确认依赖
        import hashlib

        local_path = Path(args.local_file).resolve()
        if not local_path.exists():
            print(f"[FAIL] 文件不存在: {local_path}")
            sys.exit(1)

        print("=" * 60)
        print("本地文件模式")
        print("=" * 60)
        print(f"文件: {local_path}")
        print(f"大小: {local_path.stat().st_size / 1024:.1f} KB")

        suffix = local_path.suffix.lower()
        is_image = suffix in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]

        # 复制到临时目录（统一按 PDF 路径格式存放，方便后续处理）
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            work_path = tmp_path / f"src{suffix}"

            # 图片需转 PDF 再处理（保持 pipeline 统一）
            if is_image:
                try:
                    img = Image.open(local_path)
                    pdf_path = tmp_path / "src.pdf"
                    img.convert("RGB").save(str(pdf_path), "PDF", resolution=150)
                    print(f"  图片已转为 PDF: {pdf_path.stat().st_size / 1024:.1f} KB")
                    work_path = pdf_path
                except Exception as e:
                    print(f"[FAIL] 图片转 PDF 失败: {e}")
                    sys.exit(1)
            else:
                shutil.copy2(local_path, work_path)

            # 文字提取（图片已转 PDF，统一走 extract_text_from_pdf）
            text_result = extract_text_from_pdf(str(work_path))
            content = text_result["content"] if text_result.get("ok") else ""
            method = text_result.get("method", "?")
            print(f"  提取约 {len(content)} 字（{method}）")

            # pdfplumber_fallback 且字数极少（< 50）时，尝试本地 OCR 补全
            if method == "pdfplumber_fallback" and len(content) < 50:
                print("  pdfplumber 文字过少，尝试本地 OCR...")
                ocr_success = False
                for ocr_name, ocr_module in [
                    ("rapidocr", "rapidocr_onnxruntime"),
                    ("paddleocr", "paddleocr"),
                    ("easyocr", "easyocr"),
                ]:
                    try:
                        import importlib
                        importlib.import_module(ocr_module)
                    except Exception:
                        continue
                    try:
                        if ocr_name == "rapidocr":
                            import rapidocr_onnxruntime as rapidocr
                            res, _ = rapidocr.RapidOCR()(str(local_path))
                            if res:
                                ocr_text = "\n".join([item[1] for item in res])
                                if len(ocr_text.strip()) > 30:
                                    content = ocr_text; method = "rapidocr"
                                    print(f"  RapidOCR 提取约 {len(content)} 字"); ocr_success = True
                        elif ocr_name == "paddleocr":
                            from paddleocr import PaddleOCR
                            raw = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False).ocr(str(local_path))
                            lines = [str(l[1][0]) for page in raw for l in (page or [])]
                            ocr_text = "\n".join(lines)
                            if len(ocr_text.strip()) > 30:
                                content = ocr_text; method = "paddleocr"
                                print(f"  PaddleOCR 提取约 {len(content)} 字"); ocr_success = True
                        elif ocr_name == "easyocr":
                            import easyocr
                            reader = easyocr.Reader(["ch_sim", "en"])
                            res = reader.readtext(str(local_path))
                            ocr_text = "\n".join([item[1] for item in res])
                            if len(ocr_text.strip()) > 30:
                                content = ocr_text; method = "easyocr"
                                print(f"  EasyOCR 提取约 {len(content)} 字"); ocr_success = True
                        if ocr_success:
                            break
                    except Exception as e:
                        print(f"  {ocr_name} 失败: {e}")
                        continue
                if not ocr_success:
                    print("  未检测到可用本地 OCR 库，图片将按传票默认处理")

            # 文书识别
            if len(content.strip()) > 50:
                classification = classify_and_extract(content)
                doc_type = classification["type"]
                fields = classification["fields"]
            else:
                doc_type = "传票"  # 本地上传的图片默认当传票处理（用户主动提交）
                fields = {}

            print(f"  类型: {doc_type}")
            if fields:
                print(f"  字段: {fields}")

            # 传票必须提供案号（用户传入 --case-no 或从内容提取）
            if doc_type == "传票" and not args.case_no:
                # 从内容中尝试提取案号
                for pattern in [
                    r'[（(]\s*\d{2,4}\s*[)）]\s*\S{0,10}\s*\d{1,6}\s*号',
                ]:
                    m = re.search(pattern, content)
                    if m:
                        args.case_no = m.group().strip()
                        print(f"  从内容提取案号: {args.case_no}")
                        break

            if doc_type == "传票" and not args.case_no:
                print("[FAIL] 传票必须通过 --case-no 指定案号")
                sys.exit(1)

            # 生成正确命名的文件
            if doc_type == "传票":
                hd = re.sub(r'[<>:"/\\|?*]', '-', fields.get("hearing_date", "未知日期"))
                cn = re.sub(r'[<>:"/\\|?*]', '-', fields.get("court_name", "未知法院"))
                correct_name = f"{hd}_{cn}_传票.pdf"
            elif doc_type == "判决书":
                pl = re.sub(r'[<>:"/\\|?*]', '-', fields.get("plaintiff", "未知原告"))
                df = re.sub(r'[<>:"/\\|?*]', '-', fields.get("defendant", "未知被告"))
                ca = fields.get("cause_of_action", "纠纷")
                suffix_2 = "" if ca.endswith("纠纷") else (ca + "纠纷" if ca else "纠纷")
                rd = fields.get("read_date", datetime.now().strftime("%Y年%m月%d日"))
                correct_name = f"{pl}与{df}{suffix_2}_{rd}.pdf"
            else:
                correct_name = local_path.name

            correct_path = tmp_path / correct_name
            shutil.copy2(work_path, correct_path)
            print(f"  正确命名: {correct_name}")

            # 上传飞书（指定案号文件夹）
            feishu_parent = args.parent_folder or FEISHU_PARENT_FOLDER_TOKEN or ""
            feishu_folder_token = get_or_create_feishu_folder(
                args.case_no or "未知案号",
                feishu_parent
            )
            feishu_result = upload_file_to_feishu(
                str(correct_path), correct_name, feishu_folder_token
            )

            # 传票 → 创建日历
            if doc_type == "传票" and not args.skip_calendar and fields:
                calendar_result = create_feishu_calendar_event(fields, args.case_no or "")
                if calendar_result.get("ok"):
                    print(f"  [OK] 开庭日历已创建")
                else:
                    print(f"  [WARN] 日历创建失败: {calendar_result.get('error', '?')}")

        print("\n[OK] 处理完成")
        sys.exit(0)
    # ── 法院 API 模式（原有流程）──────────────────────────────

    # 飞书父文件夹 token（CLI参数 > 环境变量 > 默认根目录）
    feishu_parent = args.parent_folder or FEISHU_PARENT_FOLDER_TOKEN or ""
    print(f"[INFO] 飞书上传目标: {'根目录' if not feishu_parent else feishu_parent}")

    # Step 1: 获取文件列表
    print("=" * 60)
    print("Step 1: 获取送达文件列表")
    print("=" * 60)
    api_result = get_document_list_from_api(args.url)
    if not api_result["ok"]:
        print(f"[FAIL] 获取文件列表失败: {api_result['error']}")
        sys.exit(1)

    all_files = api_result["files"]
    selected = all_files

    # 筛选指定文件
    if args.files:
        try:
            indices = [int(i) - 1 for i in args.files.split(",")]
            selected = [all_files[i] for i in indices if 0 <= i < len(all_files)]
            print(f"已筛选 {len(selected)} 个文件: {args.files}")
        except Exception as e:
            print(f"[WARN] 文件编号解析失败，将下载全部: {e}")

    # Step 2: 提取所有文件的案号，并按案号分组
    # 每个案号 → { "case_no": str, "latest_date": datetime, "files": [...] }
    # 关键原则：同一链接(sdbh)的所有文件必须进入同一个文件夹
    print("\n" + "=" * 60)
    print("Step 2: 按案号分组并确定飞书文件夹名称")
    print("=" * 60)

    # 优先使用用户通过 --case-no 参数直接提供的案号（从短信文本复制）
    # 其次尝试从文书名（c_wsmc）提取；均无法提取时再用 OCR
    unified_case_no = args.case_no
    if not unified_case_no:
        for f in all_files:
            wsmc = f.get("c_wsmc", "")
            cn = extract_case_no_from_wsmc(wsmc)
            if cn:
                unified_case_no = cn
                break

    # 若文书名均无案号，用 sdbh 充当案号标识（同链接同一 sdbh）
    url_params = extract_params_from_url(args.url)
    sdbh_fallback = url_params.get("sdbh", "") or url_params.get("qdbh", "")

    if not unified_case_no:
        # sdbh 格式类似 "ee69d8f216e9473487e410951415e492"，太乱，
        # 改用"同链接所有文书同一文件夹"策略：用第一个文书名作为文件夹基础名
        # 但所有文书共一个 case_no（即 None），保证同一文件夹
        pass  # unified_case_no 保持 None

    case_groups: dict[str, dict] = {}  # case_no -> group info

    for f in all_files:
        wsmc = f.get("c_wsmc", "")
        dt_cjsj = f.get("dt_cjsj", "")

        # 统一案号：同链接所有文件共用；若全链接均无法提取则用 None（表示未分类）
        case_no = unified_case_no

        dt = parse_dt_cjsj(dt_cjsj)
        if not dt:
            dt = datetime.now()

        if case_no:
            if case_no not in case_groups:
                case_groups[case_no] = {"case_no": case_no, "latest_date": dt, "files": []}
            else:
                if dt > case_groups[case_no]["latest_date"]:
                    case_groups[case_no]["latest_date"] = dt
            case_groups[case_no]["files"].append(f)
        else:
            # 所有 case_no=None 的文件都归入同一个"未分类"组（用 sdbh 做 key 保证唯一性）
            key = f"未分类_{sdbh_fallback}" if sdbh_fallback else "未分类"
            if key not in case_groups:
                case_groups[key] = {"case_no": None, "latest_date": dt, "files": []}
            else:
                if dt > case_groups[key]["latest_date"]:
                    case_groups[key]["latest_date"] = dt
            case_groups[key]["files"].append(f)

    # 输出分组情况
    for cn, g in case_groups.items():
        date_str = g["latest_date"].strftime("%Y%m%d")
        folder_name = f"{cn}_{date_str}" if cn else f"未分类文书_{date_str}"
        print(f"  案号: {cn or '(未分类)'} | 最新送达: {g['latest_date'].strftime('%Y-%m-%d')} | "
              f"文件数: {len(g['files'])} | 飞书文件夹: {folder_name}")

    # Step 3: 为每个案号组创建或获取飞书文件夹
    print("\n" + "=" * 60)
    print("Step 3: 创建/查找飞书文件夹")
    print("=" * 60)

    case_folder_tokens: dict[str, str] = {}  # case_no -> folder_token

    for cn, g in case_groups.items():
        date_str = g["latest_date"].strftime("%Y%m%d")
        folder_name = f"{cn}_{date_str}" if cn else f"未知案号_{date_str}"

        folder_token = get_or_create_feishu_folder(folder_name, feishu_parent)
        if not folder_token:
            print(f"  [WARN] 无法创建/获取文件夹 {folder_name}，将上传到根目录")
            folder_token = ""
        else:
            print(f"  文件夹就绪: {folder_name} -> {folder_token}")

        case_folder_tokens[cn] = folder_token

    # Step 4: 从 c_wsmc 中提取主案号（用于日历标题）
    case_no_api = ""
    for f in all_files:
        wsmc = f.get("c_wsmc", "")
        cn = extract_case_no_from_wsmc(wsmc)
        if cn:
            case_no_api = cn
            break

    # Step 5: 创建临时目录，所有文件下载到这里
    temp_base = Path(tempfile.gettempdir()) / "court_doc_downloader"
    temp_base.mkdir(parents=True, exist_ok=True)
    temp_dir = temp_base / datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[INFO] 临时工作目录: {temp_dir}")

    # Step 6: 依次处理每个文件
    print("\n" + "=" * 60)
    print(f"Step 6: 处理 {len(selected)} 个文件（下载→OCR→上传飞书）")
    print("=" * 60)

    results = []

    # ── 预检：当 unified_case_no 为空（"未分类"文件夹）时，
    #        对第一个文件快速 OCR 提取案号，若命中则rename文件夹 ──
    prechecked_case_no = unified_case_no  # None 表示仍"未分类"
    prechecked_folder_token = case_folder_tokens.get(None, "")
    if not unified_case_no and selected and prechecked_folder_token:
        first_file = selected[0]
        wsmc = first_file.get("c_wsmc", "")
        filename_tmp = re.sub(r'[<>:"/\\|?*]', '_', wsmc) + ".pdf"
        print(f"\n[预检] 文书名无案号，快速 OCR 识别...")
        dl = download_pdf_direct(first_file.get("wjlj", ""), filename_tmp, temp_dir)
        if dl.get("ok"):
            pdf_path = dl["filepath"]
            cn_from_ocr = quick_ocr_for_case_no(str(pdf_path))
            # 清理临时 PDF（后续 process_single_file 会重新下载）
            try:
                Path(pdf_path).unlink(missing_ok=True)
            except Exception:
                pass
            if cn_from_ocr:
                # 拼接正确的文件夹名：案号_最新送达日期
                date_str = ""
                for f2 in all_files:
                    dt2 = parse_dt_cjsj(f2.get("dt_cjsj", ""))
                    if dt2:
                        if not date_str or dt2.strftime("%Y%m%d") > date_str:
                            date_str = dt2.strftime("%Y%m%d")
                correct_folder_name = f"{cn_from_ocr}_{date_str or datetime.now().strftime('%Y%m%d')}"
                ok = rename_feishu_folder_api(prechecked_folder_token, correct_folder_name)
                if ok:
                    prechecked_case_no = cn_from_ocr  # 非 None，后续使用正确案号
                    print(f"  文件夹已更正: {correct_folder_name}")
                else:
                    print(f"  [WARN] rename 失败，继续使用未分类文件夹")
            else:
                print(f"  [预检] 未找到案号，继续使用未分类文件夹")
        else:
            print(f"  [预检] 下载失败，跳过预检: {dl.get('error')}")

    for i, file_info in enumerate(selected, 1):
        # 找到该文件所属的 case_no（在 case_groups 中匹配对象）
        file_case_no = None
        for cn, g in case_groups.items():
            # 用 c_wsbh（文书编号）匹配，比对对象 identity
            if any(x.get("c_wsbh") == file_info.get("c_wsbh") for x in g["files"]):
                file_case_no = cn
                break

        # 若 unified_case_no 为空但 precheck 找到了案号，用 precheck 的结果
        if file_case_no is None and prechecked_case_no:
            file_case_no = prechecked_case_no

        folder_token = case_folder_tokens.get(file_case_no, "")

        print(f"\n[{i}/{len(selected)}]")
        r = process_single_file(
            file_info,
            temp_dir,
            folder_token,
            args.skip_calendar,
            case_no_api=case_no_api,
        )
        results.append(r)

    # Step 7: 为每个案号文件夹生成并上传元数据 TXT
    print(f"\n{'=' * 60}")
    print("Step 7: 生成元数据 TXT")
    print("=" * 60)

    # 按 folder_token 分组 results（同一案件同一文件夹）
    folder_results: dict[str, list] = {}
    for r in results:
        if not r.get("success"):
            continue
        token = r.get("feishu_folder_token", "")
        if token not in folder_results:
            folder_results[token] = []
        folder_results[token].append(r)

    for folder_token, group_results in folder_results.items():
        # 取该组共同的案号和文件夹名
        cn = list(set(r.get("case_no") or "" for r in group_results))
        case_no_val = cn[0] if len(cn) == 1 else (unified_case_no or "未知案号")

        # 构建文件夹名（与飞书文件夹命名规则一致）
        dt_vals = []
        for r in group_results:
            dt_str = r.get("dt_cjsj", "")
            if dt_str:
                dt_obj = parse_dt_cjsj(dt_str)
                if dt_obj:
                    dt_vals.append(dt_obj)
        latest_dt = max(dt_vals) if dt_vals else datetime.now()
        folder_name = f"{case_no_val}_{latest_dt.strftime('%Y%m%d')}" if case_no_val != "未知案号" else f"未分类_{latest_dt.strftime('%Y%m%d')}"

        txt_content = _build_case_metadata_txt(group_results, case_no_val, folder_name)
        txt_name = "案件信息.txt"

        # 先写到临时文件，再上传到飞书
        import tempfile as _tmp
        txt_tmp = Path(_tmp.gettempdir()) / f"court_meta_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        txt_tmp.write_text(txt_content, encoding="utf-8")

        print(f"  生成: {txt_name}（{len(txt_content)} 字符）-> {folder_name}")
        up = upload_file_to_feishu(str(txt_tmp), txt_name, folder_token)
        if up.get("ok"):
            print(f"    [OK] {up.get('url', '')}")
        else:
            print(f"    [FAIL] {up.get('error', '未知错误')}")
        # 清理临时 TXT
        try:
            txt_tmp.unlink(missing_ok=True)
        except Exception:
            pass

    # Step 8: 汇总
    print(f"\n{'=' * 60}")
    print("处理结果汇总")
    print("=" * 60)

    success_count = sum(1 for r in results if r["success"])
    for r in results:
        status = "[OK]" if r["success"] else "[FAIL]"
        feishu_url = r.get("feishu_url", "")
        print(f"  {status} {r['name']}")
        if feishu_url:
            print(f"       飞书: {feishu_url}")
        print(f"       类型: {r['doc_type'] or '-'}, 法院: {r['court']}")
        cal = r.get("calendar_event")
        if cal and isinstance(cal, dict) and cal.get("ok"):
            print(f"       日历: [OK] {cal['title']}")
        if r.get("error"):
            print(f"       错误: {r['error']}")

    print(f"\n成功: {success_count}/{len(results)}")

    # 收集上传失败但本地存在的文件，移到本地法院送达目录
    failed_local = [r for r in results if r.get("filepath") and Path(r["filepath"]).exists()]
    if failed_local:
        local_dir = Path(args.local_dir) if args.local_dir else DEFAULT_OUTPUT_DIR
        local_dir.mkdir(parents=True, exist_ok=True)

        # 创建按日期+法院命名的文件夹
        today_str = datetime.now().strftime("%Y%m%d")
        court_name = (results[0].get("court") or "未知法院").strip()
        safe_court = re.sub(r'[<>:"/\\|?*]', '_', court_name)
        base_pattern = f"{today_str}_{safe_court}"
        seq = 1
        if local_dir.exists():
            for d in local_dir.iterdir():
                if d.is_dir() and d.name.startswith(base_pattern):
                    m2 = re.search(r'_(\d+)$', d.name)
                    if m2:
                        seq = max(seq, int(m2.group(1)) + 1)
                    else:
                        seq = max(seq, 2)

        save_dir = local_dir / f"{base_pattern}_{seq}"
        save_dir.mkdir(parents=True, exist_ok=True)

        moved = 0
        for r in failed_local:
            src = Path(r["filepath"])
            if src.exists():
                dst = save_dir / src.name
                shutil.move(str(src), str(dst))
                print(f"  [LOCAL] {src.name} -> {save_dir}")
                moved += 1
        if moved:
            print(f"[INFO] {moved} 个文件已保存到本地: {save_dir}")

    # 清理临时目录（只清理本次创建的子目录中已处理的文件）
    try:
        # 只删除临时目录中剩余的文件（已移走或已上传的）
        if temp_dir.exists():
            remaining = list(temp_dir.iterdir())
            if not remaining:
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"[INFO] 已清理临时目录: {temp_dir}")
            else:
                print(f"[WARN] 临时目录中还有 {len(remaining)} 个未处理文件: {temp_dir}")
    except Exception:
        pass

    sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
