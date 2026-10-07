"""科研端 Agent - 文献检索/标书/论文润色"""
from typing import List, Optional
from app.services.agents._base import llm_call


LIT_PROMPT = """你是 MedMind 医学文献检索助手。根据用户主题, 返回相关高质量文献(优先 SCI 一区/CNS/顶刊)。

输出 JSON: {results: [{title, authors:[], journal, year, impact_factor, pmid?, abstract, ai_summary, tags:[]}], total}"""

GRANT_PROMPT = """你是 MedMind 国自然标书撰写助手。根据课题题目和方向, 生成完整 5 大章节:
1.立项依据 2.研究内容与目标 3.研究方案 4.可行性分析 5.研究基础与工作条件
每章给出 ai_score (0-100) 与 suggestions。
输出 JSON: {title, sections:[{section, title, content, ai_score, suggestions:[]}], overall_score, citations:[]}"""

POLISH_PROMPT = """你是 MedMind 论文润色助手。把中式英语润色为地道学术英语,逐句对照, 并给出 SCI 期刊推荐(IF + 录用率 + 主题匹配度)。
输出 JSON: {polished_sentences:[{original, polished, improvements:[]}], journal_recommendations:[{name, if, acceptance_rate, match_score}]}"""


class ResearchAgent:
    async def search_literature(self, query: str, sources: List[str] = None,
                                year_from: Optional[int] = None, year_to: Optional[int] = None) -> dict:
        sources = sources or ["pubmed"]
        prompt = f"主题: {query}\n来源: {sources}\n年份: {year_from}-{year_to}\n请输出 JSON。"
        _, data = await llm_call(LIT_PROMPT, prompt, response_format="json", temperature=0.3)
        data.setdefault("results", [])
        data.setdefault("total", len(data.get("results", [])))
        return data

    async def generate_grant(self, title: str, grant_type: str = "面上项目",
                              subject_code: Optional[str] = None,
                              keywords: List[str] = None,
                              research_basis: Optional[str] = None) -> dict:
        prompt = (f"题目: {title}\n基金类型: {grant_type}\n学科代码: {subject_code}\n"
                  f"关键词: {keywords or []}\n研究基础: {research_basis or '无'}\n请输出完整标书 JSON。")
        _, data = await llm_call(GRANT_PROMPT, prompt, response_format="json", temperature=0.3)
        data.setdefault("title", title)
        data.setdefault("sections", [])
        data.setdefault("overall_score", 0)
        data.setdefault("citations", [])
        return data

    async def polish_paper(self, original_text: str) -> dict:
        prompt = f"原文:\n{original_text}\n\n请润色并推荐期刊。输出 JSON。"
        _, data = await llm_call(POLISH_PROMPT, prompt, response_format="json", temperature=0.3)
        data.setdefault("polished_sentences", [])
        data.setdefault("journal_recommendations", [])
        return data
