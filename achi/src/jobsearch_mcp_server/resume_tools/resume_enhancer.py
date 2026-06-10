"""
功能二：AI 根据岗位要求完善简历
1. 借助岗位详情完善简历 - 根据目标岗位的 JD 优化简历内容
2. 使用模板辅助 AI 完善简历 - 使用预设模板指导 AI 生成结构化简历

设计目标：生成可直接投递的专业简历，而非教学演示。
"""

import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# ============================================================
#  专业简历模板（可直接投递的格式）
# ============================================================
RESUME_TEMPLATES = {
    "standard": """{name}
{phone} | {email} | {location}

{target_position}

---

【工作经历】

{company_1} | {position_1} | {duration_1}
{achievement_1_1}
{achievement_1_2}
{achievement_1_3}

{company_2} | {position_2} | {duration_2}
{achievement_2_1}
{achievement_2_2}
{achievement_2_3}

---

【项目经验】

{project_1_name}
{project_1_desc}
{project_1_tech}
{project_1_contribution}

{project_2_name}
{project_2_desc}
{project_2_tech}
{project_2_contribution}

---

【教育背景】
{education}

---

【专业技能】
{skills}

---

【证书与语言】
{certificates}
""",

    "technical": """{name}
{phone} | {email} | {github_or_blog} | {location}

{target_position}

---

【技术栈】

{tech_summary}

---

【工作经历】

{company_1} | {position_1} | {duration_1}
{achievement_1_1}
{achievement_1_2}
{achievement_1_3}

{company_2} | {position_2} | {duration_2}
{achievement_2_1}
{achievement_2_2}
{achievement_2_3}

---

【重点项目】

{project_1_name}
技术栈：{project_1_tech}
{project_1_desc}
核心贡献：{project_1_contribution}
关键成果：{project_1_result}

{project_2_name}
技术栈：{project_2_tech}
{project_2_desc}
核心贡献：{project_2_contribution}
关键成果：{project_2_result}

---

【教育背景】
{education}

---

【开源贡献 / 技术影响力】
{open_source}
""",

    "concise": """{name}
{phone} | {email} | {location}

{target_position}

---

【核心优势】
{core_strengths}

---

【工作经历】
{company_1} | {position_1} | {duration_1}
{achievement_1_1}
{achievement_1_2}

{company_2} | {position_2} | {duration_2}
{achievement_2_1}
{achievement_2_2}

---

【教育背景】
{education}

---

【关键技能】
{skills}
"""
}


# ============================================================
#  ResumeEnhancer 类
# ============================================================
class ResumeEnhancer:
    """
    AI 简历完善器

    用法:
        enhancer = ResumeEnhancer()
        # 1. 根据岗位详情完善简历
        enhanced = enhancer.enhance_by_jd(resume="...", job_description="...")
        # 2. 使用模板完善简历
        result = enhancer.enhance_with_template(resume="...", template_name="technical", job_description="...")
    """

    # ----------------------------------------------------------
    #  1. 借助岗位详情完善简历
    # ----------------------------------------------------------
    def enhance_by_jd(
        self,
        resume: str,
        job_description: str,
        extra_instructions: str = ""
    ) -> str:
        """
        根据岗位描述（JD）优化简历，使简历更贴合目标岗位

        参数:
            resume:           原始简历文本
            job_description:  目标岗位描述（JD）
            extra_instructions: 额外优化要求（如 "突出项目管理经验"）

        返回:
            优化后的简历文本
        """
        system_prompt = """你是一位顶级的简历优化专家，拥有 15 年跨国企业 HR 总监和猎头顾问经验。你的客户正在求职，需要你帮他们把简历优化到可以直接投递的水平。

【核心原则】
1. **关键词精准匹配**：仔细分析 JD 中的每一个关键词（技能、工具、领域术语），确保简历中自然融入这些关键词，提高 ATS（ Applicant Tracking System ）通过率
2. **成果量化优先**：每段工作经历至少包含 1-2 个可量化的成果（如"提升效率 30%"、"支撑日均 100 万请求"、"降低故障率 50%"），数字要合理可信
3. **STAR 法则**：用"情境-任务-行动-结果"的结构描述关键成就
4. **相关性排序**：将与目标岗位最相关的内容前置，弱化或删除不相关的内容
5. **专业表达**：使用行业通用的专业术语，语言简洁有力，避免口语化
6. **绝对真实**：不得编造经历、技能或数据，只能在原始信息基础上优化表达、突出亮点、合理重组
7. **格式规范**：输出结构清晰、排版专业的简历，方便直接复制使用
8. **竞争力导向**：思考"HR 看到这份简历会想约面试吗？"——让每一行都有价值

【输出要求】
- 输出优化后的完整简历
- 在简历末尾用 "---【优化说明】---" 分隔，附上 3-5 条具体的优化要点说明"""

        user_prompt = f"""请根据以下目标岗位描述，优化求职者的简历，生成一份可以直接投递的专业简历。

【目标岗位描述】
{job_description}

【原始简历】
{resume}

【额外要求】
{extra_instructions if extra_instructions else "无"}

请输出优化后的完整简历，并在最后附上优化说明。"""

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"简历优化失败：{str(e)}"

    # ----------------------------------------------------------
    #  2. 使用模板辅助 AI 完善简历
    # ----------------------------------------------------------
    def enhance_with_template(
        self,
        resume: str,
        template_name: str = "standard",
        job_description: str = "",
        custom_template: str = None
    ) -> str:
        """
        使用预设模板或自定义模板，指导 AI 将简历内容填入模板并完善

        参数:
            resume:          原始简历文本
            template_name:   模板名称，可选 "standard" / "technical" / "concise"
            job_description: 目标岗位描述（可选，提供后模板会针对性优化）
            custom_template: 自定义模板文本（提供后将忽略 template_name）

        返回:
            按模板生成的完善版简历
        """
        # 确定模板
        if custom_template:
            template = custom_template
        else:
            template = RESUME_TEMPLATES.get(template_name)
            if template is None:
                available = list(RESUME_TEMPLATES.keys())
                return f"不支持的模板名称：'{template_name}'，可选：{available}"

        system_prompt = """你是一位顶级的简历撰写专家，拥有 15 年 HR 和职业咨询经验。你的客户正在求职，需要你根据他们提供的原始信息，生成一份可以直接投递的专业简历。

【核心要求】
1. **忠实于原始信息**：不得编造经历、技能或数据，但可以在原始信息基础上合理优化表达
2. **专业表达升级**：将口语化、平淡的描述升级为专业、有力的行业用语
3. **成果量化**：每段经历至少包含 1 个可量化的成果，数字要合理可信
4. **模板适配**：严格按照模板结构填写，确保格式完整、排版专业
5. **针对性优化**：如果提供了岗位描述，要针对 JD 做关键词匹配和内容侧重
6. **完整填充**：模板中所有字段都要填写，原始信息不足时基于已有信息做合理推断和补充（用括号标注推断内容）
7. **竞争力导向**：让简历在 10 秒内抓住 HR 的眼球

【输出要求】
- 严格按照模板格式输出完整的简历内容
- 确保简历可以直接复制投递使用"""

        jd_section = f"\n【目标岗位描述】\n{job_description}" if job_description else ""

        user_prompt = f"""请根据以下原始简历信息，按照提供的模板格式生成一份可以直接投递的专业简历。

【原始简历】
{resume}{jd_section}

【简历模板】
{template}

请严格按照模板格式输出完整的简历内容，确保每一部分都经过专业优化。"""

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"模板生成失败：{str(e)}"

    # ----------------------------------------------------------
    #  辅助：列出可用模板
    # ----------------------------------------------------------
    @staticmethod
    def list_templates() -> dict:
        """返回所有可用模板的名称和简介"""
        return {
            "standard": "标准简历模板 - 结构完整、适用面广，适合大多数岗位投递",
            "technical": "技术岗位模板 - 突出技术栈深度和项目实战成果，适合开发/架构/DevOps 等岗位",
            "concise": "简洁模板 - 精简高效、重点突出，适合经验丰富的资深求职者"
        }

    # ----------------------------------------------------------
    #  辅助：批量优化（针对多个岗位）
    # ----------------------------------------------------------
    def batch_enhance(
        self,
        resume: str,
        job_list: list,
        template_name: str = "standard"
    ) -> list:
        """
        针对多个岗位批量优化简历

        参数:
            resume:       原始简历
            job_list:     岗位列表，每个元素为 {"title": "岗位名", "jd": "岗位描述"}
            template_name: 模板名称

        返回:
            list[dict]，每个元素为 {"title": ..., "enhanced_resume": ...}
        """
        results = []
        for job in job_list:
            title = job.get("title", "未知岗位")
            jd = job.get("jd", "")
            print(f"正在优化：{title}...")
            enhanced = self.enhance_by_jd(resume, jd)
            results.append({
                "title": title,
                "enhanced_resume": enhanced
            })
        return results


# ============================================================
#  独立运行测试
# ============================================================
if __name__ == "__main__":
    sample_resume = """
    张三，男，28岁，本科，北京大学计算机科学与技术专业。
    2020-2023 在阿里巴巴做后端开发，负责订单系统。
    2023-至今 在字节跳动做高级后端工程师，负责支付系统。
    技能：Java、Go、Python、Spring Boot、MySQL、Redis、Kafka、Docker、K8s。
    """

    sample_jd = """
    岗位名称：高级后端工程师（支付方向）
    岗位职责：
    1. 负责支付核心链路的设计与开发，保障系统高可用
    2. 优化系统性能，支撑千万级日活用户
    3. 参与技术方案评审，推动架构演进
    任职要求：
    - 5年以上后端开发经验，3年以上支付/金融相关经验
    - 精通 Java 或 Go，熟悉 Spring Cloud 或微服务架构
    - 熟悉分布式系统设计，掌握 Kafka、Redis 等中间件
    - 有高并发、高可用系统实战经验
    - 良好的系统设计能力和团队协作精神
    """

    enhancer = ResumeEnhancer()

    print("=" * 60)
    print("1. 根据岗位详情完善简历")
    print("=" * 60)
    result1 = enhancer.enhance_by_jd(sample_resume, sample_jd)
    print(result1)

    print("\n" + "=" * 60)
    print("2. 使用模板完善简历")
    print("=" * 60)
    result2 = enhancer.enhance_with_template(
        sample_resume,
        template_name="technical",
        job_description=sample_jd
    )
    print(result2)

    print("\n" + "=" * 60)
    print("可用模板：")
    print("=" * 60)
    templates = enhancer.list_templates()
    for name, desc in templates.items():
        print(f"  - {name}: {desc}")
