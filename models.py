"""GitHub 项目评估相关的数据模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectEvaluationData(BaseModel):
    """项目评估原始数据 - 收集所有 API 数据"""

    # 基础信息
    owner: str
    repo: str
    full_name: str
    description: Optional[str] = None
    url: str
    created_at: datetime
    updated_at: datetime

    # 代码质量相关
    has_readme: bool
    readme_length: int = 0
    has_license: bool = False
    license_name: Optional[str] = None
    has_contributing: bool = False
    has_code_of_conduct: bool = False
    primary_language: Optional[str] = None
    language_count: int = 0
    language_distribution: dict[str, float] = Field(default_factory=dict)
    has_standard_dirs: bool = False  # 是否存在标准目录（src/lib/tests）
    protected_branches: int = 0  # 受保护的分支数

    # 活跃度相关 (v2.0)
    release_count: int = 0
    releases_last_year: int = 0

    # Issue/PR 相关（近 12 个月）
    open_issues: int = 0
    closed_issues: int = 0
    issue_comments_total: int = 0  # Issue 评论总数
    issue_comments_avg: float = 0.0  # Issue 平均评论数

    total_prs: int = 0
    merged_prs: int = 0
    pr_comments_total: int = 0  # PR 评论总数
    pr_comment_density: float = 0.0  # PR 评论密度 = (issue_comments + pr_comments) / merged_prs

    # 社区相关
    stars: int = 0
    forks: int = 0
    contributors: int = 0

    # 计算字段
    age_in_days: int = 0
    maintained_for_years: float = 0.0
    commits_confidence: str = "high"  # v2.0总是high（不再依赖commits数据）


class DimensionScore(BaseModel):
    """维度评分"""

    score: float = Field(ge=0, le=100)  # 该维度得分
    max_score: float = 100  # 该维度满分
    percentage: float = Field(ge=0, le=100)  # 得分率百分比
    confidence: str = "high"  # 可信度：high/medium/low
    details: dict = Field(default_factory=dict)  # 子指标详情


class ProjectEvaluation(BaseModel):
    """项目综合评估结果"""

    # 基本信息
    repo_full_name: str
    repo_url: str
    evaluated_at: datetime

    # 总分
    total_score: float = Field(ge=0, le=100)
    confidence: str = "high"  # 总体可信度
    rating: str  # A+, A, B+, B, C, D

    # 三大维度
    code_quality: DimensionScore
    activity: DimensionScore
    community_health: DimensionScore

    # 关键指标
    key_metrics: dict = Field(default_factory=dict)

    # 评估总结
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)  # 优势
    weaknesses: list[str] = Field(default_factory=list)  # 不足
    recommendation: str = ""  # 推荐建议


class EvaluationCard(BaseModel):
    """评分卡片输出格式"""

    markdown: str  # Markdown 格式的完整卡片
    plain_text: str  # 纯文本格式
    json_data: ProjectEvaluation  # JSON 数据
    raw_data: ProjectEvaluationData  # 原始评估数据
    scoring_breakdown: dict = Field(default_factory=dict)  # 评分点详细分解
