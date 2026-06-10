# job_crawler_51job.py
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager


def fetch_jobs_from_51job(keyword: str, city_code: str = "090200", max_pages: int = 3) -> str:
    """
    使用Selenium控制Chrome浏览器，从前程无忧抓取职位数据。
    参数示例：keyword="AI应用开发", city_code="090200" (上海)
    """

    chrome_options = Options()
    # chrome_options.add_argument("--headless") # 调试时可以把它注释掉，方便观察浏览器
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.56 Safari/537.36")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    all_jobs_output = ""
    driver = None

    try:
        print("正在初始化浏览器...")
        # service = Service(ChromeDriverManager().install())
        # service = Service(
        #            ChromeDriverManager(
        #                                 root_url="https://npmmirror.com/mirrors/chrome-for-testing"
        #                             ).install()

        driver = webdriver.Chrome(service=service, options=chrome_options)
        

        # --- 直接构造URL，访问搜索页（核心变化在这里） ---
        # 这个URL会直接返回包含职位列表的页面，跳过了在首页的复杂点击操作
        search_url = f"https://we.51job.com/pc/search?keyword={keyword}&jobArea={city_code}&searchType=2"
        print(f"正在直接访问搜索页面：{search_url}")
        driver.get(search_url)

        # 等待职位列表容器加载出来，如果30秒还没出现，就可能触发了反爬
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".joblist-item"))
            )
            print("职位列表已成功加载。")
        except Exception:
            print("等待职位列表超时，可能需要登录或已触发反爬虫机制。")
            return "加载职位列表失败，请检查是否需要手动登录或更换网络环境。"

        # --- 分页抓取数据 ---
        for page in range(1, max_pages + 1):
            print(f"--- 正在抓取第 {page} 页 ---")
            time.sleep(random.uniform(2, 3))

            # 提取职位卡片
            job_cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-item")
            print(f"本页找到 {len(job_cards)} 个职位。")

            for idx, card in enumerate(job_cards):
                try:
                    # 安全的提取文本信息
                    def safe_extract(selector, default="N/A"):
                        try:
                            elem = card.find_element(By.CSS_SELECTOR, selector)
                            return elem.text if elem.text else default
                        except Exception:
                            return default

                    global_idx = (page - 1) * len(job_cards) + idx + 1
                    job_name = safe_extract(".jname.text-cut", "职位名称未找到")
                    salary = safe_extract(".sal.text-cut", "薪资未找到")
                    location = safe_extract(".area .shrink-0", "地点未找到")
                    company = safe_extract(".cname", "公司名称未找到")  # 请确认
                    scale = safe_extract(".dc.shrink-0", "公司性质未找到")  # 请确认

                    all_jobs_output += f"{global_idx}. 职位名称: {job_name}\n"
                    all_jobs_output += f"   公司名称: {company}\n"
                    all_jobs_output += f"   工作地点: {location}\n"
                    all_jobs_output += f"   薪资范围: {salary}\n"
                    all_jobs_output += f"   公司性质: {scale}\n\n"  # 新增公司规模

                except Exception as e:
                    print(f"解析单个卡片时出错: {e}")
                    continue

            # 处理翻页
            if page < max_pages:
                try:
                    # 查找可点击的“下一页”按钮
                    next_page_btn = driver.find_element(By.CSS_SELECTOR, ".next, .page-next:not(.disabled)")
                    if next_page_btn.is_enabled():
                        next_page_btn.click()
                        print("已点击“下一页”，等待页面加载...")
                        time.sleep(random.uniform(3, 5))
                    else:
                        print("已到达最后一页。")
                        break
                except Exception:
                    print("未找到“下一页”按钮，抓取结束。")
                    break

        if not all_jobs_output:
            all_jobs_output = "未抓取到任何职位信息，请检查网络或关键词。"

    except Exception as e:
        all_jobs_output = f"爬虫运行出错：{str(e)}"
        print(all_jobs_output)

    finally:
        if driver:
            print("正在关闭浏览器...")
            driver.quit()

    return all_jobs_output


if __name__ == "__main__":
    # 测试：爬取上海“AI应用开发”职位前2页
    result = fetch_jobs_from_51job("AI应用开发", "090200", max_pages=2)
    print(result)