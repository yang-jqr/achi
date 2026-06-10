"""
前程无忧 (51job) 上海 AI应用开发 岗位爬虫
使用 Selenium 控制 Chrome 浏览器，抓取前2页数据
"""
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager


def fetch_51job_shanghai(keyword: str = "AI应用开发", city_code: str = "030200",max_pages: int = 2) -> list[dict]:
    """
    抓取前程无忧上海地区指定关键词的职位信息
    返回: list[dict]，每个 dict 包含职位名称、公司、地点、薪资、经验、学历等
    """
    chrome_options = Options()
    # 调试时可注释掉 --headless 来观察浏览器行为
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = None
    all_jobs: list[dict] = []

    try:
        print("正在初始化浏览器...")
        service = Service(executable_path=r"E:\chrome\chrome-win64\chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 前程无忧新版搜索URL
        # keyword: 搜索关键词
        # jobArea: 090200 = 上海
        # searchType: 2 表示精确匹配
        search_url = (
            f"https://we.51job.com/pc/search?"
            f"keyword={keyword}&jobArea={city_code}&searchType=2"  
        )
        print(f"正在访问: {search_url}")
        driver.get(search_url)

        # 等待职位列表加载
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".joblist-item"))
            )
            print("职位列表加载成功。")
        except Exception:
            print("等待职位列表超时，可能触发了反爬或需要登录。")
            # 保存页面源码用于调试
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("已保存页面源码到 debug_page.html")
            return all_jobs

        for page in range(1, max_pages + 1):
            print(f"\n{'='*50}")
            print(f"正在抓取第 {page} 页")
            print(f"{'='*50}")

            time.sleep(random.uniform(2, 4))

            # 获取所有职位卡片
            job_cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-item")
            print(f"本页找到 {len(job_cards)} 个职位。")

            for idx, card in enumerate(job_cards):
                try:
                    def safe_text(selector, default=""):
                        try:
                            el = card.find_element(By.CSS_SELECTOR, selector)
                            return el.text.strip()
                        except Exception:
                            return default

                    job = {
                        "序号": (page - 1) * len(job_cards) + idx + 1,
                        "职位名称": safe_text(".jname"),
                        "公司名称": safe_text(".cname"),
                        "工作地点": safe_text(".area .shrink-0"),
                        "薪资范围": safe_text(".sal"),
                        "公司性质": safe_text(".dc.shrink-0"),
                        "所属区域": safe_text(".area.shrink-0"),
                        "经营范围": safe_text(".dc.text-cut"),
                        "公司规模": safe_text(".area.shrink-0"),
                        "公司概况": safe_text(".bc.text-cut"),
                        "关键词": safe_text(".joblist-item-tags"),
                    }
                    all_jobs.append(job)

                except Exception as e:
                    print(f"解析第 {idx+1} 个卡片出错: {e}")
                    continue

            # --- 翻页逻辑 ---
            if page < max_pages:
                print(f"尝试翻到第 {page + 1} 页...")
                try:
                    # 尝试多种翻页按钮选择器
                    pagination_selectors = [
                        ".pagination li",           # 通用分页
                        ".page-index li",           # 另一种分页
                        ".pagination .number",       # 数字按钮
                        "li[class*='number']",       # 包含number的li
                        ".pagination li:not(.next):not(.prev)",  # 排除前后按钮
                    ]

                    page_links = []
                    for sel in pagination_selectors:
                        page_links = driver.find_elements(By.CSS_SELECTOR, sel)
                        if page_links:
                            print(f"使用选择器 '{sel}' 找到 {len(page_links)} 个分页元素")
                            break

                    if not page_links:
                        print("未找到分页元素，尝试查找 '下一页' 按钮...")
                        next_btn = driver.find_elements(By.CSS_SELECTOR, ".pagination .next, .page-index .next, a[class*='next']")
                        if next_btn:
                            driver.execute_script("arguments[0].click();", next_btn[0])
                            print("已点击'下一页'按钮")
                            time.sleep(random.uniform(3, 5))
                            continue
                        else:
                            print("翻页元素均未找到，停止翻页。")
                            break

                    # 提取数字页码
                    numeric_btns = []
                    for btn in page_links:
                        txt = btn.text.strip()
                        if txt.isdigit():
                            numeric_btns.append((int(txt), btn))

                    if not numeric_btns:
                        print("未找到数字页码按钮。")
                        break

                    # 找下一页的按钮（当前页+1）
                    target_page = page + 1
                    target_btn = None
                    for num, btn in numeric_btns:
                        if num == target_page:
                            target_btn = btn
                            break

                    if target_btn is None:
                        print(f"未找到第 {target_page} 页按钮。")
                        break

                    # 滚动到按钮并点击
                    driver.execute_script("arguments[0].scrollIntoView(true);", target_btn)
                    time.sleep(0.5)
                    try:
                        target_btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", target_btn)

                    print(f"已点击第 {target_page} 页，等待加载...")
                    time.sleep(random.uniform(3, 5))

                except Exception as e:
                    print(f"翻页失败: {e}")
                    break

    except Exception as e:
        print(f"爬虫运行出错: {e}")

    finally:
        if driver:
            print("\n正在关闭浏览器...")
            driver.quit()

    return all_jobs


def print_jobs(jobs: list[dict]):
    """格式化打印职位信息"""
    if not jobs:
        print("未抓取到任何职位信息。")
        return

    print(f"\n{'='*70}")
    print(f"共抓取 {len(jobs)} 个职位")
    print(f"{'='*70}")

    for job in jobs:
        print(f"{job['序号']}. 职位: {job['职位名称']}")
        print(f"   公司: {job['公司名称']}")
        print(f"   地点: {job['工作地点']}")
        print(f"   薪资: {job['薪资范围']}")
        print(f"   概况: {job['公司概况']}")
        print(f"   技能: {job['关键词'].replace('\n', ',')}")
        print()


if __name__ == "__main__":
    jobs = fetch_51job_shanghai(keyword="AI应用开发", city_code="020000",max_pages=2)
    print_jobs(jobs)
