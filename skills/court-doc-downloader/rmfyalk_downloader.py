#!/usr/bin/env python3
"""
人民法院案例库下载器 v1
从 rmfyalk.court.gov.cn 搜索并下载案例。

用法:
    python rmfyalk_downloader.py search "<关键词>" [--pages <页数>]
    python rmfyalk_downloader.py download "<案例ID>" [--output <目录>]
    python rmfyalk_downloader.py case "<案例URL>"
"""

import argparse
import asyncio
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright, Page

# ============================================================
# 配置
# ============================================================

DEFAULT_OUTPUT_DIR = Path(os.environ.get(
    "COURT_OUTPUT_DIR",
    "D:/多平台同步文件/05诉讼项目/11我的法院送达文件"
))

BASE_URL = "https://rmfyalk.court.gov.cn"
SEARCH_URL = f"{BASE_URL}/view/list.html"
CONTENT_URL = f"{BASE_URL}/view/content.html"
DOWNLOAD_API = f"{BASE_URL}/cpws_al_api/api/cpwsAl/contentDownload"

# ============================================================
# 工具函数
# ============================================================

def extract_case_id_from_url(url: str) -> str:
    """从 content.html URL 中提取 ID 参数。"""
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    return query.get('id', [''])[0]

def parse_case_id(raw_id: str) -> str:
    """
    将 content.html URL 中的 ID（已编码）转换为 download API 需要的格式。
    content URL: id=lmACF1R47BWcr2N%252BobqpHljijBEPOe5OisU%252Br0walmc%253D
    download URL: id=lmACF1R47BWcr2N%2BobqpHljijBEPOe5OisU%2Br0walmc%3D
    即 content URL 中 %252B → download 中 +，%253D → =
    """
    return raw_id.replace('%2B', '+').replace('%253D', '=')

def save_case_json(case_data: dict, output_path: Path):
    """保存案例 JSON 元数据。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, ensure_ascii=False, indent=2)

def make_output_dir(output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

async def _launch_browser(p) -> 'BrowserContext':
    """
    启动 Chromium 浏览器，返回 BrowserContext。
    - CHROME_DATA_DIR: Chrome 用户数据目录（可复制已登录的配置文件）
    - CHROME_PROFILE: Chrome profile 子目录名，默认 "Default"
    如果设置了 CHROME_DATA_DIR，则使用已有配置（可避免重复登录）。
    """
    data_dir = os.environ.get("CHROME_DATA_DIR", "")
    profile = os.environ.get("CHROME_PROFILE", "Default")

    if data_dir:
        # 使用已有 Chrome 配置：launch_persistent_context 直接返回 BrowserContext
        profile_dir = f"{data_dir}/{profile}"
        print(f"[浏览器] 使用已有 Chrome 配置: {profile_dir}")
        return await p.chromium.launch_persistent_context(
            profile_dir,
            headless=True,
            args=[
                "--disable-first-run-ui",
                "--no-default-browser-check",
            ],
        )
    else:
        # 启动新 Chromium，从 Browser 创建 BrowserContext
        print("[浏览器] 启动新 Chromium（无头模式，无登录状态）")
        browser = await p.chromium.launch(headless=True)
        return await browser.new_context()

# ============================================================
# 搜索流程
# ============================================================

async def search_cases(keyword: str, max_pages: int = 3, progress_callback=None):
    """
    搜索案例，返回案例列表。
    每条记录包含: title, case_no, court, date, category, reason, id, url, lib
    """
    results = []
    encoded_kw = urllib.parse.quote(keyword)

    async with async_playwright() as p:
        context = await _launch_browser(p)
        page = await context.new_page()
        page.set_default_timeout(60000)

        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                search_url = (f"{SEARCH_URL}?key=qw&keyName=%E5%85%A8%E6%96%87"
                              f"&value={encoded_kw}&isAdvSearch=0&searchType=1&lib=cpwsAl_qb")
            else:
                search_url = (f"{SEARCH_URL}?key=qw&keyName=%E5%85%A8%E6%96%87"
                              f"&value={encoded_kw}&isAdvSearch=0&searchType=1&lib=cpwsAl_qb&page={page_num}")

            print(f"[搜索] 第 {page_num} 页...")
            await page.goto(search_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # 解析搜索结果列表
            cases = await parse_search_results(page)
            if not cases:
                print(f"[搜索] 第 {page_num} 页无结果，停止")
                break

            for case in cases:
                case['keyword'] = keyword
                case['search_page'] = page_num
            results.extend(cases)
            print(f"[搜索] 第 {page_num} 页找到 {len(cases)} 条记录")

            # 简单翻页检测
            try:
                total_text = await page.locator('text=共').first.inner_text()
                if '共' in total_text:
                    page_links = await page.locator('text=/^\\d+$/').all_inner_texts()
                    if len(page_links) == 0 or int(page_links[-1]) if page_links else 1 <= page_num:
                        break
            except Exception:
                pass

        await context.close()

    return results


async def parse_search_results(page: Page) -> list:
    """从搜索结果页解析案例列表。"""
    cases = []

    try:
        items = await page.locator('a[href*="/view/content.html"]').all()

        for item in items:
            try:
                href = await item.get_attribute('href')
                title = await item.inner_text()

                if not href or 'content.html' not in href:
                    continue

                parsed = urllib.parse.urlparse(href)
                query = urllib.parse.parse_qs(parsed.query)
                case_id = query.get('id', [''])[0]
                lib = query.get('lib', ['ck'])[0]

                if not case_id:
                    continue

                # 获取相邻元信息
                siblings_text = ''
                try:
                    next_el = item.locator('xpath=following-sibling::*').first
                    siblings_text = await next_el.inner_text()
                except Exception:
                    pass

                meta = parse_case_meta(siblings_text)

                case = {
                    'id': case_id,
                    'url': f"{CONTENT_URL}?id={urllib.parse.quote(case_id)}&lib={lib}",
                    'title': title.strip(),
                    'case_no': meta.get('case_no', ''),
                    'court': meta.get('court', ''),
                    'date': meta.get('date', ''),
                    'category': meta.get('category', ''),
                    'reason': meta.get('reason', ''),
                    'procedure': meta.get('procedure', ''),
                    'storage_date': meta.get('storage_date', ''),
                    'lib': lib,
                }
                cases.append(case)

            except Exception as e:
                print(f"[解析] 单条案例失败: {e}")
                continue

    except Exception as e:
        print(f"[解析] 搜索结果解析失败: {e}")

    return cases


def parse_case_meta(text: str) -> dict:
    """
    解析案例元信息文本。
    格式: "2026-13-2-167-001 / 民事 / 发明专利权权属、侵权纠纷 / 最高人民法院 / 2024.10.23 / （2022）最高法知民终2527号 / 二审 / 入库日期：2026.04.13"
    """
    meta = {}
    if not text:
        return meta

    parts = [p.strip() for p in text.split('/')]
    if len(parts) >= 7:
        meta['storage_no'] = parts[0].strip()
        meta['category'] = parts[1].strip()
        meta['reason'] = parts[2].strip()
        meta['court'] = parts[3].strip()
        meta['date'] = parts[4].strip()
        meta['case_no'] = parts[5].strip()
        meta['procedure'] = parts[6].strip()
        if len(parts) >= 8 and '入库日期' in parts[7]:
            meta['storage_date'] = parts[7].replace('入库日期：', '').strip()

    return meta

# ============================================================
# 案例详情获取
# ============================================================

async def get_case_detail(case_url_or_id: str, lib: str = 'ck') -> dict:
    """获取案例详情页信息。"""
    async with async_playwright() as p:
        context = await _launch_browser(p)
        page = await context.new_page()
        page.set_default_timeout(60000)

        if case_url_or_id.startswith('http'):
            url = case_url_or_id
        else:
            url = f"{CONTENT_URL}?id={urllib.parse.quote(case_url_or_id)}&lib={lib}"

        print(f"[详情] 访问: {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        detail = await parse_case_detail(page)
        detail['url'] = url
        detail['id'] = extract_case_id_from_url(url)

        await context.close()

    return detail


async def parse_case_detail(page: Page) -> dict:
    """解析案例详情页。"""
    detail = {}

    try:
        try:
            title_el = page.locator('text=/.*诉.*/').first
            detail['title'] = await title_el.inner_text()
        except Exception:
            detail['title'] = ''

        try:
            idx = await page.locator('text=入库编号').inner_text()
            detail['storage_no'] = idx
        except Exception:
            pass

        try:
            all_text = await page.inner_text('body')
        except Exception:
            all_text = ''

        try:
            kw_section = page.locator('text=关键词').first
            kw_text = await kw_section.inner_text()
            detail['keywords'] = [k.strip() for k in kw_text.split('\n') if k.strip()]
        except Exception:
            pass

        sections = ['基本案情', '裁判理由', '裁判要旨', '关联索引']
        for section in sections:
            try:
                el = page.locator(f'text={section}').first
                parent = el.locator('..')
                section_text = await parent.inner_text()
                detail[section] = section_text
            except Exception:
                detail[section] = ''

        try:
            download_link = page.locator('a:has-text("下载")')
            href = await download_link.get_attribute('href')
            if href:
                raw_id = extract_case_id_from_url(href)
                download_id = parse_case_id(raw_id)
                detail['download_url'] = f"{DOWNLOAD_API}?id={download_id}"
                detail['download_id'] = download_id
        except Exception:
            pass

    except Exception as e:
        print(f"[详情] 解析失败: {e}")

    return detail

# ============================================================
# 下载文件
# ============================================================

async def download_case(case_url_or_id: str, output_dir: Path = None,
                        case_title: str = '', lib: str = 'ck') -> Path:
    """下载案例 PDF 文件。"""
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    output_dir = make_output_dir(output_dir)

    async with async_playwright() as p:
        context = await _launch_browser(p)
        page = await context.new_page()
        page.set_default_timeout(60000)

        if case_url_or_id.startswith('http'):
            url = case_url_or_id
        else:
            url = f"{CONTENT_URL}?id={urllib.parse.quote(case_url_or_id)}&lib={lib}"

        print(f"[下载] 访问详情页...")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        try:
            download_link = page.locator('a:has-text("下载")')
            href = await download_link.get_attribute('href')
            raw_id = extract_case_id_from_url(href)
            download_id = parse_case_id(raw_id)
            download_url = f"{DOWNLOAD_API}?id={download_id}"
        except Exception as e:
            print(f"[下载] 无法获取下载链接: {e}")
            await context.close()
            return None

        print(f"[下载] 下载 URL: {download_url}")

        # 获取案号
        case_no = ''
        try:
            body_text = await page.inner_text('body')
            match = re.search(r'（\d+）[^/（]+\d+号', body_text)
            if match:
                case_no = match.group(0)
        except Exception:
            pass

        title_text = case_title
        if not title_text:
            try:
                title_el = page.locator('text=/.*诉.*/').first
                title_text = await title_el.inner_text()
            except Exception:
                title_text = ''

        if case_no:
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', case_no)
        else:
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title_text[:30]) if title_text else '未知案例'

        filename = f"{safe_title}.pdf"
        filepath = output_dir / filename

        counter = 1
        while filepath.exists():
            filename = f"{safe_title}_{counter}.pdf"
            filepath = output_dir / filename
            counter += 1

        print(f"[下载] 保存到: {filepath}")

        async with page.expect_download(timeout=60000) as download_info:
            await page.goto(download_url)

        download = await download_info.value
        await download.save_as(str(filepath))

        print(f"[下载] 完成: {filepath}")
        await context.close()

        return filepath

# ============================================================
# 搜索 + 下载完整流程
# ============================================================

async def search_and_download(keyword: str, max_pages: int = 3,
                               output_dir: Path = None,
                               download_all: bool = False,
                               case_indices: list = None):
    """搜索并可选下载案例。"""
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    output_dir = make_output_dir(output_dir)

    print(f"=" * 60)
    print(f"开始搜索: {keyword}")
    print(f"=" * 60)

    cases = await search_cases(keyword, max_pages=max_pages)
    print(f"\n共找到 {len(cases)} 条案例记录\n")

    if not cases:
        print("未找到任何案例。")
        return cases

    print(f"{'序号':<4} {'标题':<40} {'案号':<25} {'法院':<12} {'日期'}")
    print("-" * 110)
    for i, case in enumerate(cases, 1):
        title = (case['title'][:38] + '..') if len(case['title']) > 38 else case['title']
        case_no = (case['case_no'][:23] + '..') if len(case['case_no']) > 23 else case['case_no']
        court = (case['court'][:10] + '..') if len(case['court']) > 10 else case['court']
        print(f"{i:<4} {title:<40} {case_no:<25} {court:<12} {case['date']}")

    to_download = []
    if download_all:
        to_download = list(range(1, len(cases) + 1))
    elif case_indices:
        to_download = case_indices

    if to_download:
        print(f"\n开始下载第 {to_download} 条案例...\n")
        for idx in to_download:
            if 1 <= idx <= len(cases):
                case = cases[idx - 1]
                print(f"\n[{idx}/{len(cases)}] 下载: {case['title']}")
                try:
                    filepath = await download_case(
                        case['id'],
                        output_dir=output_dir,
                        case_title=case['title'],
                        lib=case['lib']
                    )
                    if filepath:
                        json_path = filepath.with_suffix('.json')
                        save_case_json(case, json_path)
                        print(f"[完成] {filepath}")
                except Exception as e:
                    print(f"[错误] 下载失败: {e}")
            else:
                print(f"[跳过] 无效序号: {idx}")

    return cases

# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="人民法院案例库下载器 - 从 rmfyalk.court.gov.cn 搜索并下载案例"
    )
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    search_parser = subparsers.add_parser('search', help='搜索案例')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('--pages', '-p', type=int, default=3, help='最大搜索页数（默认3）')
    search_parser.add_argument('--download', '-d', action='store_true', help='下载找到的案例')
    search_parser.add_argument('--indices', '-i', type=str, help='指定下载的案例序号，如 "1,3,5"')
    search_parser.add_argument('--output', '-o', type=str, help='输出目录')

    dl_parser = subparsers.add_parser('download', help='下载指定案例')
    dl_parser.add_argument('case_url_or_id', help='案例URL或ID')
    dl_parser.add_argument('--output', '-o', type=str, help='输出目录')

    case_parser = subparsers.add_parser('case', help='获取案例详情')
    case_parser.add_argument('case_url_or_id', help='案例URL或ID')

    args = parser.parse_args()

    if args.command == 'search':
        output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
        output_dir = make_output_dir(output_dir)
        indices = [int(x) for x in args.indices.split(',')] if args.indices else None
        cases = asyncio.run(search_and_download(
            args.keyword,
            max_pages=args.pages,
            output_dir=output_dir,
            download_all=args.download and indices is None,
            case_indices=indices
        ))
        result_file = output_dir / f"搜索结果_{args.keyword}_{len(cases)}条.json"
        save_case_json({'keyword': args.keyword, 'count': len(cases), 'cases': cases}, result_file)
        print(f"\n搜索结果已保存: {result_file}")

    elif args.command == 'download':
        output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
        output_dir = make_output_dir(output_dir)
        filepath = asyncio.run(download_case(args.case_url_or_id, output_dir=output_dir))
        if filepath:
            print(f"\n下载完成: {filepath}")
        else:
            print("\n下载失败")
            sys.exit(1)

    elif args.command == 'case':
        detail = asyncio.run(get_case_detail(args.case_url_or_id))
        print(json.dumps(detail, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
