"""GitHub 项目评估协调器 - 负责数据收集和评估流程"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from nekro_agent.core import logger

from .client import GitHubClient
from .models import EvaluationCard, ProjectEvaluation, ProjectEvaluationData
from .scorer import ProjectScorer
from .utils import LRUCache


class GitHubProjectEvaluator:
    """GitHub 项目评估器 - 协调数据收集和评分"""

    # 全局缓存实例：带 100 个条目容量和 TTL 限制的 LRU 缓存
    _cache = LRUCache(max_size=100, ttl_seconds=1800)

    def __init__(self, client: GitHubClient):
        """初始化评估器

        Args:
            client: GitHubClient 实例
        """
        self.client = client
        self.scorer = ProjectScorer()

    async def evaluate_project(self, url: str) -> ProjectEvaluation:
        """执行完整的项目评估

        Args:
            url: GitHub 项目 URL 或 owner/repo 格式

        Returns:
            ProjectEvaluation 评估结果

        Raises:
            ValueError: 如果 URL 无效或项目不存在或项目超大型
            RuntimeError: 如果数据收集失败
        """
        # 0. 检查缓存
        from .plugin import config

        cached_result = self._cache.get(url)
        if cached_result is not None:
            cache_age = cached_result.get("age_seconds", 0)
            logger.info(f"✅ 使用缓存结果 ({cache_age}秒前): {url}")
            return cached_result["result"]

        # 1. 收集所有必要数据
        data = await self._collect_data(url)

        # 2. 计算各维度得分
        scores = self.scorer.calculate_scores(data)

        # 3. 生成优势和不足
        strengths, weaknesses = self.scorer.generate_strengths_and_weaknesses(data, scores)

        # 4. 生成推荐建议
        total_score = scores["code_quality"].score + scores["activity"].score + scores["community_health"].score
        rating = self.scorer.get_rating(total_score)
        recommendation = self.scorer.generate_recommendation(total_score)

        # 计算总体 confidence
        # v2.0 不再依赖 commits 数据，所以总是 high
        overall_confidence = "high"

        # 5. 生成关键指标
        key_metrics = self._generate_key_metrics(data)

        # 6. 生成总结
        summary = self._generate_summary(data)

        # 7. 构建评估对象
        evaluation = ProjectEvaluation(
            repo_full_name=data.full_name,
            repo_url=data.url,
            evaluated_at=datetime.now(timezone.utc),
            total_score=round(total_score, 1),
            confidence=overall_confidence,
            rating=rating,
            code_quality=scores["code_quality"],
            activity=scores["activity"],
            community_health=scores["community_health"],
            key_metrics=key_metrics,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation,
        )

        # 存储原始数据用于调试
        self._last_evaluation_data = data

        # 8. 缓存评估结果
        self._cache.set(url, {
            "result": evaluation,
            "age_seconds": 0,
        })
        logger.debug(f"💾 评估结果已缓存: {url}")

        return evaluation

    def get_last_evaluation_raw_data(self) -> Optional["ProjectEvaluationData"]:
        """获取最后一次评估的原始数据（用于调试）

        Returns:
            ProjectEvaluationData 或 None
        """
        return getattr(self, "_last_evaluation_data", None)

    def generate_evaluation_card(
        self,
        evaluation: ProjectEvaluation,
        raw_data: ProjectEvaluationData,
    ) -> EvaluationCard:
        """生成完整的评分卡片，包含原始数据和评分点分解

        Args:
            evaluation: 项目评估结果
            raw_data: 原始评估数据

        Returns:
            包含完整信息的 EvaluationCard
        """
        from .formatter import EvaluationFormatter

        # 生成评分点分解
        scores = self.scorer.calculate_scores(raw_data)
        scoring_breakdown = self.scorer.generate_scoring_breakdown(raw_data, scores)

        # 生成各种格式的输出
        formatter = EvaluationFormatter()
        markdown = formatter.to_markdown_card(evaluation)
        plain_text = formatter.to_detailed_scoring_report(evaluation, scoring_breakdown)

        # 构建评分卡片
        return EvaluationCard(
            markdown=markdown,
            plain_text=plain_text,
            json_data=evaluation,
            raw_data=raw_data,
            scoring_breakdown=scoring_breakdown,
        )

    @classmethod
    def get_cache_stats(cls) -> dict:
        """获取缓存统计信息

        Returns:
            dict: 缓存统计信息
        """
        return cls._cache.get_stats()

    @classmethod
    def clear_cache(cls) -> None:
        """清空所有缓存"""
        cls._cache.clear()

    @classmethod
    def cleanup_expired_cache(cls) -> int:
        """清理过期缓存

        Returns:
            int: 清理的条目数
        """
        return cls._cache.cleanup_expired()

    async def _collect_data(self, url: str) -> ProjectEvaluationData:
        """顺序收集评估所需的所有数据（确保完整性）

        Args:
            url: GitHub 项目 URL

        Returns:
            ProjectEvaluationData 包含所有评估数据

        Raises:
            ValueError: 如果 URL 无效或项目不存在
            RuntimeError: 如果数据收集失败
        """
        # 顺序调用 API，与测试脚本保持一致
        logger.info(f"开始收集项目数据: {url}")

        # 1️⃣ 获取基础信息（必需，如果失败则抛出异常）
        logger.debug("📋 获取仓库基础信息...")
        repo_info = await self.client.get_repo_info(url)
        owner = repo_info.owner
        repo = repo_info.repo

        # 2️⃣ 获取 README
        logger.debug("📚 获取 README 信息...")
        try:
            readme_info = await self.client.get_readme(url)
        except Exception as e:
            logger.warning(f"⚠️ README API 调用失败: {e}")
            readme_info = None

        # 3️⃣ 获取 LICENSE
        logger.debug("📄 获取 LICENSE 信息...")
        license_info = await self._safe_call(
            self.client.get_license(url),
            "license",
        )

        # 4️⃣ 获取社区健康文件
        logger.debug("🗣️ 获取社区健康文件...")
        community_profile = await self._safe_call(
            self.client.get_community_profile(url),
            "community_profile",
        )

        # 5️⃣ 获取语言统计
        logger.debug("🔤 获取语言统计...")
        language_stats = await self._safe_call(
            self.client.get_languages(url),
            "language_stats",
        )

        # 5.5️⃣ 获取仓库结构（检测标准目录）
        logger.debug("📁 获取仓库结构...")
        repo_structure = await self._safe_call(
            self.client.get_repo_structure(url),
            "repo_structure",
        )

        # 6️⃣ 获取 Issues 列表
        logger.debug("🐛 获取 Issues 列表...")
        issues = await self._safe_call(
            self.client.get_issues(url, state="all", per_page=100),
            "issues",
        )

        # 9️⃣ 获取 Pull Requests 列表
        logger.debug("🔀 获取 Pull Requests 列表...")
        pull_requests = await self._safe_call(
            self.client.get_pull_requests(url, state="all", per_page=100),
            "pull_requests",
        )

        # 🔟 获取 Releases 列表
        logger.debug("📦 获取 Releases 列表...")
        releases = await self._safe_call(
            self.client.get_releases(url),
            "releases",
        )

        # 🔳 获取分支列表
        logger.debug("🌳 获取分支信息...")
        branches = await self._safe_call(
            self.client.get_branches(url),
            "branches",
        )

        logger.info("✅ 数据收集完成，开始数据处理...")

        # ===== 处理收集到的数据 =====
        # 代码质量数据
        has_readme = readme_info is not None
        readme_length = len(readme_info.content) if readme_info else 0

        has_license = license_info is not None and not isinstance(license_info, Exception)
        license_name = license_info.name if not isinstance(license_info, Exception) else None

        # 社区文件
        if not isinstance(community_profile, Exception):
            has_contributing = community_profile.has_contributing
            has_code_of_conduct = community_profile.has_code_of_conduct
        else:
            has_contributing = False
            has_code_of_conduct = False

        # 语言统计
        if not isinstance(language_stats, Exception):
            primary_language = language_stats.primary_language
            language_count = language_stats.language_count
            language_distribution = language_stats.language_percentages
        else:
            primary_language = repo_info.language
            language_count = 1 if repo_info.language else 0
            language_distribution = {repo_info.language: 100.0} if repo_info.language else {}

        # ===== 检测标准目录结构 =====
        has_standard_dirs = False
        if not isinstance(repo_structure, Exception):
            standard_dirs = {"src", "lib", "tests", "test", "docs", "doc"}
            found_dirs = set()
            for item in repo_structure:
                if hasattr(item, "type") and item.type == "tree":
                    dir_name = item.path.split("/")[-1].lower() if hasattr(item, "path") else ""
                    if dir_name in standard_dirs:
                        found_dirs.add(dir_name)
            # 有2个或以上的标准目录就认为结构清晰
            if len(found_dirs) >= 2:
                has_standard_dirs = True
                logger.debug(f"✅ 检测到标准目录: {found_dirs}")
            elif len(found_dirs) == 1:
                logger.debug(f"⚠️ 检测到部分标准目录: {found_dirs}")
        else:
            logger.debug("⚠️ 获取仓库结构失败，无法检测标准目录")

        # ===== Release 统计 =====
        release_count = 0
        releases_last_year = 0
        if isinstance(releases, list):
            release_count = len(releases)

            one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
            for release in releases:
                try:
                    release_date = datetime.fromisoformat(
                        release.published_at.replace("Z", "+00:00"),
                    )
                    if release_date > one_year_ago:
                        releases_last_year += 1
                except:
                    pass

        # ===== Issue/PR 统计 =====
        open_issues_count = repo_info.issues
        closed_issues_count = 0
        issue_comments_total = 0
        total_prs = 0
        merged_prs = 0
        pr_comments_total = 0
        pr_comment_density = 0.0

        if isinstance(issues, list):
            for issue in issues:
                if not isinstance(issue, Exception):
                    if issue.state == "closed":
                        closed_issues_count += 1
                    # 统计 Issue 评论总数
                    issue_comments_total += issue.comments

        if isinstance(pull_requests, list):
            total_prs = len(pull_requests)
            for pr in pull_requests:
                if not isinstance(pr, Exception):
                    if pr.merged:
                        merged_prs += 1
                    # 统计 PR 评论总数
                    pr_comments_total += pr.comments

        # 计算平均值和密度
        issue_comments_avg = (
            issue_comments_total / max(1, open_issues_count + closed_issues_count)
            if (open_issues_count + closed_issues_count) > 0
            else 0.0
        )

        # PR 评论密度 = (issue_comments + pr_comments) / merged_prs
        pr_comment_density = (issue_comments_total + pr_comments_total) / max(1, merged_prs) if merged_prs > 0 else 0.0

        # ===== 分支保护统计 =====
        protected_branches = 0
        if isinstance(branches, list):
            for branch in branches:
                if not isinstance(branch, Exception) and hasattr(branch, "is_protected") and branch.is_protected:
                    protected_branches += 1
                    logger.debug(f"🔒 受保护分支: {branch.name}")

        # ===== 社区数据 =====
        stars = repo_info.stars
        forks = repo_info.forks
        contributors = repo_info.contributors

        # ===== 计算字段 =====
        age_in_days = 0
        maintained_for_years = 0.0

        try:
            if repo_info.created_at:
                created_str = repo_info.created_at
                if created_str.endswith("Z"):
                    created_str = created_str.replace("Z", "+00:00")
                elif "+" not in created_str and "-" not in created_str[-6:]:
                    created_str = created_str + "+00:00"

                created_date = datetime.fromisoformat(created_str)
                age_in_days = (datetime.now(timezone.utc) - created_date).days
                logger.debug(f"✅ 项目创建时间: {created_date.strftime('%Y-%m-%d')}, 年龄: {age_in_days} 天")
        except Exception as e:
            logger.warning(f"⚠️ 解析 created_at 失败 ({repo_info.created_at}): {e}")

        try:
            if repo_info.updated_at:
                updated_str = repo_info.updated_at
                if updated_str.endswith("Z"):
                    updated_str = updated_str.replace("Z", "+00:00")
                elif "+" not in updated_str and "-" not in updated_str[-6:]:
                    updated_str = updated_str + "+00:00"

                updated_date = datetime.fromisoformat(updated_str)
                days_since_update = (datetime.now(timezone.utc) - updated_date).days
                # 持续维护年数 = (最后一次更新距现在的天数) / 365
                # 这反映了项目有多少时间没更新
                maintained_for_years = max(0, (age_in_days - days_since_update) / 365)
                logger.debug(
                    f"✅ 最后更新: {updated_date.strftime('%Y-%m-%d')}, 距今: {days_since_update} 天, 持续维护: {maintained_for_years:.2f} 年",
                )
        except Exception as e:
            logger.warning(f"⚠️ 解析 updated_at 失败 ({repo_info.updated_at}): {e}")

        # 构建数据对象
        return ProjectEvaluationData(
            owner=owner,
            repo=repo,
            full_name=repo_info.full_name,
            description=repo_info.description,
            url=repo_info.url,
            created_at=(
                datetime.fromisoformat(repo_info.created_at.replace("Z", "+00:00"))
                if repo_info.created_at
                else datetime.now(timezone.utc)
            ),
            updated_at=(
                datetime.fromisoformat(repo_info.updated_at.replace("Z", "+00:00"))
                if repo_info.updated_at
                else datetime.now(timezone.utc)
            ),
            has_readme=has_readme,
            readme_length=readme_length,
            has_license=has_license,
            license_name=license_name,
            has_contributing=has_contributing,
            has_code_of_conduct=has_code_of_conduct,
            has_standard_dirs=has_standard_dirs,  # 基于实际检测结果
            primary_language=primary_language,
            language_count=language_count,
            language_distribution=language_distribution,
            release_count=release_count,
            releases_last_year=releases_last_year,
            open_issues=open_issues_count,
            closed_issues=closed_issues_count,
            issue_comments_total=issue_comments_total,
            issue_comments_avg=issue_comments_avg,
            total_prs=total_prs,
            merged_prs=merged_prs,
            pr_comments_total=pr_comments_total,
            pr_comment_density=pr_comment_density,
            protected_branches=protected_branches,
            stars=stars,
            forks=forks,
            contributors=contributors,
            age_in_days=age_in_days,
            maintained_for_years=maintained_for_years,
        )

    async def _safe_call(self, coro, name: str):
        """安全调用 API，返回异常而不是抛出

        Args:
            coro: 协程
            name: API 名称（用于日志）

        Returns:
            API 结果或 Exception 对象
        """
        try:
            return await coro
        except Exception as e:
            logger.warning(f"⚠️ {name} API 调用失败: {type(e).__name__}: {str(e)[:100]}")
            return e

    @staticmethod
    def _generate_key_metrics(data: ProjectEvaluationData) -> dict:
        """生成关键指标

        Args:
            data: 项目评估原始数据

        Returns:
            关键指标字典
        """
        return {
            "stars": f"{data.stars:,}",
            "forks": f"{data.forks:,}",
            "contributors": f"{data.contributors}",
            "open_issues": f"{data.open_issues}",
            "release_count": f"{data.release_count}",
            "primary_language": data.primary_language or "未知",
            "project_age_years": f"{data.age_in_days // 365}",
            "last_update": data.updated_at.strftime("%Y-%m-%d"),
        }

    @staticmethod
    def _generate_summary(data: ProjectEvaluationData) -> str:
        """生成评估总结

        Args:
            data: 项目评估原始数据

        Returns:
            评估总结文本
        """
        parts = []

        # 项目基本特征
        if data.primary_language:
            parts.append(f"这是一个 {data.primary_language} 项目")
        else:
            parts.append("这是一个开源项目")

        # 规模
        if data.stars > 10000:
            parts.append("，备受关注（10k+ Stars）")
        elif data.stars > 1000:
            parts.append("，具有一定影响力（1k+ Stars）")
        elif data.stars > 100:
            parts.append("，已获得社区认可（100+ Stars）")

        # 活跃度 - 基于 Release 频率和项目新鲜度
        from datetime import datetime, timezone

        days_since_update = (datetime.now(timezone.utc) - data.updated_at).days
        if days_since_update <= 30:
            parts.append("，维护活跃（最近更新）")
        elif data.releases_last_year >= 4:
            parts.append("，持续维护（定期发行）")
        else:
            parts.append("，更新较慢")

        # 社区
        if data.contributors >= 10:
            parts.append("，社区规模较大")
        elif data.contributors > 0:
            parts.append("，有贡献者参与")

        return "。".join(parts) + "。"
