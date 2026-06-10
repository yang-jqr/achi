"""
BOSS直聘 岗位爬虫
使用 Playwright + 代理 + 手动扫码登录
需要先安装: pip install playwright && playwright install chromium
"""
import asyncio
import json
import random
import time
import re
from pathlib import Path
from playwright.async_api import async_playwright, Page

# ============== 配置区 ==============
# 代理配置（三选一，根据你购买的代理类型修改）
# 方式1: HTTP代理隧道（快代理/豌豆代理等）
PROXY_CONFIG = {
    "server": "http://your-proxy-server:port",    # 替换为你的代理地址
    "username": "your-username",                    # 替换为你的代理账号
    "password": "your-password",                    # 替换为你的代理密码
}

# 方式2: 如果是手机热点，不需要配置代理，直接用本机网络即可
# PROXY_CONFIG = None

# 方式3: 如果代理不需要认证（如本地代理软件）
# PROXY_CONFIG = {"server": "http://127.0.0.1:7890"}  # clash/v2ray 本地端口

# 搜索关键词
KEYWORD = "AI应用开发"
# 城市编码 (100010000=全国, 101010100=北京, 101020100=上海, 101280100=广州, 101280600=深圳)
CITY_CODE = "101020100"  # 上海
# 最大抓取页数
MAX_PAGES = 5
# 每页之间的等待秒数范围
PAGE_INTERVAL = (15, 30)
# Cookie 持久化文件路径
COOKIE_FILE = Path(__file__).parent / "boss_cookies.json"
# =================================


def get_proxy_settings():
    """组装 Playwright 代理参数"""
    if PROXY_CONFIG is None:
        return None
    proxy = {"server": PROXY_CONFIG["server"]}
    if "username" in PROXY_CONFIG:
        proxy["username"] = PROXY_CONFIG["username"]
        proxy["password"] = PROXY_CONFIG["password"]
    return proxy


async def save_cookies(context, path: Path):
    """保存 Cookie 到文件，下次复用，避免反复扫码"""
    cookies = await context.cookies()
    path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    print(f"[Cookie] 已保存到 {path}")


async def load_cookies(context, path: Path) -> bool:
    """从文件加载 Cookie，返回是否加载成功"""
    if not path.exists():
        return False
    try:
        cookies = json.loads(path.read_text(encoding="utf-8"))
        await context.add_cookies(cookies)
        print(f"[Cookie] 已从 {path} 加载 {len(cookies)} 条")
        return True
    except Exception as e:
        print(f"[Cookie] 加载失败: {e}")
        return False


async def random_delay(min_s: float = 1.0, max_s: float = 3.0):
    """随机等待，模拟人类阅读节奏"""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def human_scroll(page: Page):
    """模拟人类滚动浏览行为"""
    for _ in range(random.randint(2, 4)):
        scroll_amount = random.randint(300, 800)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await random_delay(1.5, 4.0)


async def parse_job_card(card, page: Page):
    """解析单个职位卡片"""
    try:
        # BOSS的职位卡片选择器（需要根据实际页面调整）
        title_el = await card.query_selector(".job-name, .job-title")
        title = await title_el.inner_text() if title_el else ""

        salary_el = await card.query_selector(".salary, .red")
        salary = await salary_el.inner_text() if salary_el else ""

        company_el = await card.query_selector(".company-name a, .company-text")
        company = await company_el.inner_text() if company_el else ""

        # 标签信息（经验/学历/城市）
        tags_el = await card.query_selector_all(".tag-list li, .job-tags span")
        tags = []
        for t in tags_el:
            text = (await t.inner_text()).strip()
            if text:
                tags.append(text)

        # 技能/福利标签
        skill_els = await card.query_selector_all(".info-desc, .job-card-footer .tag-item")
        skills = []
        for s in skill_els:
            text = (await s.inner_text()).strip()
            if text:
                skills.append(text)

        # HR活跃度
        boss_el = await card.query_selector(".boss-name, .info-public")
        boss_info = await boss_el.inner_text() if boss_el else ""

        return {
            "职位名称": title,
            "薪资": salary,
            "公司": company,
            "标签": ", ".join(tags),
            "技能": ", ".join(skills),
            "HR信息": boss_info,
        }
    except Exception as e:
        print(f"  [解析失败] {e}")
        return None


async def crawl_boss():
    """主爬虫逻辑"""
    proxy = get_proxy_settings()

    async with async_playwright() as p:
        # 启动浏览器（非headless，方便手动扫码）
        browser = await p.chromium.launch(
            headless=False,  # 首次运行需要扫码，设为 False
            proxy=proxy,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # 创建上下文（伪装成普通浏览器）
        context = await browser.new_context(
            viewport={"width": random.choice([1920, 1366, 1440]),
                      "height": random.choice([1080, 768, 900])},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{random.choice(['120','121','122'])}.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )

        # 反检测脚本：隐藏自动化特征
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh']});
            // 覆盖 chrome.runtime（BOSS会检测）
            window.chrome = { runtime: {} };
        """)

        page = await context.new_page()

        # 尝试加载已有 Cookie
        cookie_loaded = await load_cookies(context, COOKIE_FILE)

        # 访问 BOSS 直聘首页
        print("[访问] 打开 BOSS 直聘...")
        await page.goto("https://www.zhipin.com/", wait_until="domcontentloaded")
        await random_delay(3, 5)

        # 检查是否需要登录
        if not cookie_loaded or "登录" in await page.inner_text("body"):
            print("\n" + "=" * 50)
            print("⚠️  请手动扫码登录（扫码后等待页面跳转）")
            print("=" * 50)
            # 等待用户手动登录（等待URL变化或特定元素出现）
            try:
                await page.wait_for_url("**/zhipin.com/**", timeout=120_000)
                # 再等一点确保登录状态稳定
                await random_delay(3, 5)
                # 保存 Cookie 供下次复用
                await save_cookies(context, COOKIE_FILE)
                print("[登录] 登录成功，Cookie 已保存")
            except Exception:
                print("[登录] 等待超时，请确认是否已登录")
        else:
            print("[Cookie] 复用已有登录状态")

        # 构建搜索 URL
        search_url = (
            f"https://www.zhipin.com/web/geek/job"
            f"?query={KEYWORD}&city={CITY_CODE}"
        )
        print(f"\n[搜索] 访问: {search_url}")
        await page.goto(search_url, wait_until="domcontentloaded")
        await random_delay(5, 8)

        all_jobs = []

        for pg in range(1, MAX_PAGES + 1):
            print(f"\n{'='*50}")
            print(f"[第 {pg} 页] 开始抓取...")
            print(f"{'='*50}")

            # 模拟人类滚动
            await human_scroll(page)

            # 等待职位列表加载
            try:
                await page.wait_for_selector(
                    ".job-list-box .job-card-wrapper, "
                    ".search-job-result .job-card-wrap",
                    timeout=15_000
                )
            except Exception:
                print("[警告] 职位列表未加载，可能触发了验证码")

                # 检测是否有验证码
                if "验证" in await page.inner_text("body") or "滑块" in await page.inner_text("body"):
                    print("\n⚠️  检测到验证码，请手动完成验证...")
                    input("完成验证后按回车继续...")

            # 获取当前页所有职位卡片
            cards = await page.query_selector_all(
                ".job-card-wrapper, .job-card-wrap"
            )
            print(f"[找到] {len(cards)} 个职位卡片")

            for idx, card in enumerate(cards):
                job = await parse_job_card(card, page)
                if job:
                    job["页码"] = pg
                    job["序号"] = len(all_jobs) + 1
                    all_jobs.append(job)
                    print(f"  [{job['序号']}] {job['职位名称'][:30]} | {job['薪资']} | {job['公司'][:15]}")
                # 每个卡片之间小间隔
                await random_delay(0.5, 2.0)

            # 翻页
            if pg < MAX_PAGES:
                print(f"\n[翻页] 尝试翻到第 {pg + 1} 页...")
                try:
                    # BOSS的翻页选择器
                    next_btn = await page.query_selector(
                        ".pagination .next, "
                        ".options-pages .next, "
                        ".page .next"
                    )
                    if next_btn:
                        await next_btn.click()
                        wait_time = random.uniform(*PAGE_INTERVAL)
                        print(f"[等待] 翻页后等待 {wait_time:.1f} 秒...")
                        await asyncio.sleep(wait_time)
                    else:
                        print("[翻页] 未找到下一页按钮，停止翻页")
                        break
                except Exception as e:
                    print(f"[翻页] 失败: {e}")
                    break

        # 保存结果
        output_file = Path(__file__).parent / "boss_jobs.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for job in all_jobs:
                f.write(f"{job['序号']}. {job['职位名称']}\n")
                f.write(f"   公司: {job['公司']}\n")
                f.write(f"   薪资: {job['薪资']}\n")
                f.write(f"   标签: {job['标签']}\n")
                f.write(f"   技能: {job['技能']}\n")
                f.write(f"   HR信息: {job['HR信息']}\n")
                f.write("\n")

        print(f"\n{'='*50}")
        print(f"[完成] 共抓取 {len(all_jobs)} 条职位")
        print(f"[保存] 已写入 {output_file}")
        print(f"{'='*50}")

        await browser.close()


if __name__ == "__main__":
    print("=" * 50)
    print("BOSS直聘岗位爬虫")
    print(f"关键词: {KEYWORD}")
    print(f"城市编码: {CITY_CODE}")
    print(f"最大页数: {MAX_PAGES}")
    print(f"代理: {'已配置' if PROXY_CONFIG else '未配置（使用本机网络）'}")
    print("=" * 50)
    asyncio.run(crawl_boss())