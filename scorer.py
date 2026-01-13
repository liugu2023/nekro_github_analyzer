"""GitHub 项目评分算法"""

import math
from datetime import datetime, timezone

from nekro_agent.core import logger

from .models import DimensionScore, ProjectEvaluationData


class ProjectScorer:
    """项目评分计算器 - 实现三大维度的评分算法"""

    def calculate_scores(self, data: ProjectEvaluationData) -> dict:
        """计算所有维度的得分

        Args:
            data: 项目评估原始数据

        Returns:
            包含三个维度评分的字典
        """
        return {
            "code_quality": self.calculate_code_quality(data),
            "activity": self.calculate_activity(data),
            "community_health": self.calculate_community_health(data),
        }

    def calculate_code_quality(self, data: ProjectEvaluationData) -> DimensionScore:
        """计算代码质量得分 (0-30)

        维度细分:
        - 文档完整性 (10分): README、LICENSE、CONTRIBUTING、CODE_OF_CONDUCT
        - 项目维护性 (10分): 活跃 commit、Release 管理、分支保护
        - 代码组织 (10分): 语言明确、分布合理、结构清晰
        """
        score = 0.0
        details = {}
        confidence = "high"

        # ===== 文档完整性 (10分) =====
        # README (5分)
        if data.has_readme and data.readme_length >= 500:
            score += 5
            details["readme"] = "优秀"
        elif data.has_readme:
            score += 3
            details["readme"] = "良好"
        else:
            details["readme"] = "缺失"

        # LICENSE (2分)
        if data.has_license:
            score += 2
            details["license"] = f"✓ {data.license_name}"
        else:
            details["license"] = "✗ 缺失"

        # CONTRIBUTING (1.5分)
        if data.has_contributing:
            score += 1.5
            details["contributing"] = "✓"
        else:
            details["contributing"] = "✗"

        # CODE_OF_CONDUCT (1.5分)
        if data.has_code_of_conduct:
            score += 1.5
            details["code_of_conduct"] = "✓"
        else:
            details["code_of_conduct"] = "✗"

        # ===== 项目维护性 (10分) =====
        # Release 管理 (5分)
        if data.releases_last_year >= 6:
            score += 5
            details["release_management"] = f"规范 ({data.releases_last_year}/年)"
        elif data.releases_last_year >= 2:
            score += 3
            details["release_management"] = f"基础 ({data.releases_last_year}/年)"
        elif data.releases_last_year >= 1:
            score += 1
            details["release_management"] = f"初级 ({data.releases_last_year}/年)"
        else:
            details["release_management"] = "无正式发行"

        # 最后更新时间 (2.5分) ⭐ v2.0新指标
        from datetime import datetime, timezone

        try:
            days_since_update = (datetime.now(timezone.utc) - data.updated_at).days
            if days_since_update <= 30:
                score += 2.5
                update_status = "活跃维护"
            elif days_since_update <= 90:
                score += 1.5
                update_status = "定期维护"
            elif days_since_update <= 180:
                score += 0.5
                update_status = "偶尔维护"
            else:
                update_status = "长期停滞"
            details["last_update"] = f"{days_since_update}天前 ({update_status})"
        except Exception as e:
            logger.warning(f"⚠️ 计算最后更新时间失败: {e}")
            details["last_update"] = "无法计算"

        # 分支保护 (2.5分)
        if data.protected_branches > 0:
            branch_protection_score = min(2.5, data.protected_branches * 0.5)
            score += branch_protection_score
            details["branch_protection"] = f"✓ {data.protected_branches} 受保护分支"
        else:
            details["branch_protection"] = "✗ 无受保护分支"

        # ===== 代码组织 (10分) =====
        # 主要语言 (3分)
        if data.primary_language:
            score += 3
            details["primary_language"] = data.primary_language
        else:
            details["primary_language"] = "未识别"

        # 语言数量合理性 (4分)
        if 1 <= data.language_count <= 5:
            score += 4
            details["language_diversity"] = "合理"
        elif 5 < data.language_count <= 10:
            score += 2
            details["language_diversity"] = "可接受"
        elif data.language_count > 10:
            score += 0
            details["language_diversity"] = "过度分散"
        else:
            details["language_diversity"] = "未识别"

        # 结构清晰度 (3分)
        if data.has_standard_dirs:
            score += 3
            details["code_structure"] = "清晰 (含标准目录)"
        elif data.primary_language and data.language_count > 0:
            score += 1.5
            details["code_structure"] = "中等"
        else:
            details["code_structure"] = "待改进"

        final_score = min(30, score)

        return DimensionScore(
            score=round(final_score, 1),
            max_score=30,
            percentage=round((final_score / 30) * 100, 1),
            confidence=confidence,
            details=details,
        )

    def calculate_activity(self, data: ProjectEvaluationData) -> DimensionScore:
        """计算项目活跃度得分 (0-40) - v2.0标准

        维度细分:
        - Release 发布频率 (12分): 过去一年的发行版本数量
        - 项目新鲜度 (15分): 基于 updated_at 的最后更新时间
        - Issue/PR 响应 (13分): 关闭率、合并率、开放Issue健康度
        """
        score = 0.0
        details = {}
        confidence = "high"  # v2.0不再依赖commit数据

        # ===== Release 发布频率 (12分) =====
        if data.releases_last_year >= 6:
            score += 12
            release_level = "高频 (≥6次/年)"
        elif data.releases_last_year >= 4:
            score += 10
            release_level = "中上 (4-5次/年)"
        elif data.releases_last_year >= 2:
            score += 7
            release_level = "中等 (2-3次/年)"
        elif data.releases_last_year >= 1:
            score += 4
            release_level = "低频 (1次/年)"
        else:
            score += 0
            release_level = "无发行"

        details["release_frequency"] = f"{data.releases_last_year}次/年 ({release_level})"

        # ===== 项目新鲜度 (15分) ⭐ 新核心指标 =====
        # 基于 repo 的 updated_at 时间戳
        from datetime import datetime, timedelta, timezone

        try:
            days_since_update = (datetime.now(timezone.utc) - data.updated_at).days

            if days_since_update <= 30:
                score += 15
                freshness_level = "🟢 持续活跃"
            elif days_since_update <= 90:
                score += 12
                freshness_level = "🟡 定期维护"
            elif days_since_update <= 180:
                score += 8
                freshness_level = "🟠 不太频繁"
            elif days_since_update <= 365:
                score += 4
                freshness_level = "🔴 长期停滞"
            else:
                score += 0
                freshness_level = "⚫ 已放弃"

            details["project_freshness"] = f"{days_since_update}天未更新 ({freshness_level})"
        except Exception as e:
            logger.warning(f"⚠️ 计算项目新鲜度失败: {e}")
            details["project_freshness"] = "无法计算"

        # ===== Issue/PR 响应能力 (13分) =====
        # Issue 关闭率 (4.3分)
        if data.open_issues + data.closed_issues > 0:
            close_rate = data.closed_issues / (data.open_issues + data.closed_issues)
            issue_score = close_rate * 4.3
            score += issue_score
            details["issue_close_rate"] = f"{close_rate * 100:.1f}%"
        else:
            details["issue_close_rate"] = "无 Issue"

        # PR 合并率 (4.3分)
        if data.total_prs > 0:
            merge_rate = data.merged_prs / data.total_prs
            pr_score = merge_rate * 4.3
            score += pr_score
            details["pr_merge_rate"] = f"{merge_rate * 100:.1f}%"
        else:
            details["pr_merge_rate"] = "无 PR"

        # 开放 Issue 健康度 (4.4分)
        # 基于 Issue/Stars 比例
        if data.stars > 0:
            issue_ratio = data.open_issues / max(1, data.stars)
            if issue_ratio < 0.01:
                score += 4.4
                details["open_issues_health"] = "很好 (问题很少)"
            elif issue_ratio < 0.05:
                score += 3.0
                details["open_issues_health"] = "良好 (适度)"
            elif issue_ratio < 0.15:
                score += 1.5
                details["open_issues_health"] = "一般 (较多)"
            else:
                details["open_issues_health"] = "需要改进 (堆积)"
        else:
            # Stars 为 0
            if data.open_issues == 0:
                score += 4.4
                details["open_issues_health"] = "很好 (问题很少)"
            else:
                details["open_issues_health"] = "需改进"

        final_score = min(40, score)

        return DimensionScore(
            score=round(final_score, 1),
            max_score=40,
            percentage=round((final_score / 40) * 100, 1),
            confidence=confidence,
            details=details,
        )

    def calculate_community_health(self, data: ProjectEvaluationData) -> DimensionScore:
        """计算社区健康度得分 (0-30)

        使用对数评分避免大项目碾压小项目

        维度细分:
        - 社区参与度 (15分): Stars、Forks、Contributors（已移除 Watchers）
        - 社区互动 (10分): Issue 讨论活跃、PR 评审质量（改用 PR 评论密度）
        - 项目成熟度 (5分): 项目年龄、持续维护
        """
        score = 0.0
        details = {}
        confidence = "high"

        # ===== 社区参与度 (15分) =====
        # Stars (对数评分，6分)
        if data.stars > 0:
            star_score = min(6, math.log10(data.stars + 1) * 1.5)
            score += star_score
            details["stars"] = f"{data.stars:,} ⭐"
        else:
            details["stars"] = "0 ⭐"

        # Forks (对数评分，4分)
        if data.forks > 0:
            fork_score = min(4, math.log10(data.forks + 1) * 1.2)
            score += fork_score
            details["forks"] = f"{data.forks:,} 🔀"
        else:
            details["forks"] = "0 🔀"

        # Contributors (对数评分，5分)
        if data.contributors > 0:
            contrib_score = min(5, math.log10(data.contributors + 1) * 1.8)
            score += contrib_score
            contributor_level = "活跃" if data.contributors >= 10 else "少量"
            details["contributors"] = f"{data.contributors} 👥 ({contributor_level})"
        else:
            details["contributors"] = "0 👥"

        # ===== 社区互动 (10分) =====
        # Issue 讨论活跃度 (5分)
        total_issues = data.open_issues + data.closed_issues
        if total_issues > 0:
            avg_issue_comments = data.issue_comments_avg
            if avg_issue_comments >= 3:
                score += 5
                details["issue_discussion"] = f"活跃 (平均{avg_issue_comments:.1f}条评论/issue)"
            elif avg_issue_comments >= 1:
                score += 3
                details["issue_discussion"] = f"中等 (平均{avg_issue_comments:.1f}条评论/issue)"
            elif avg_issue_comments > 0:
                score += 1
                details["issue_discussion"] = f"低活动 (平均{avg_issue_comments:.1f}条评论/issue)"
            else:
                details["issue_discussion"] = "无评论"
        else:
            details["issue_discussion"] = "无 Issue"

        # PR 评审质量 (5分) - 使用 PR 评论密度替代
        if data.total_prs > 0:
            merge_rate = data.merged_prs / data.total_prs
            pr_comment_density = data.pr_comment_density

            if merge_rate > 0.8 and pr_comment_density >= 1:
                score += 5
                details["pr_review"] = f"优秀 (合并率{merge_rate*100:.0f}%, 评论密度{pr_comment_density:.1f})"
            elif merge_rate > 0.6 and pr_comment_density >= 0.5:
                score += 3
                details["pr_review"] = f"良好 (合并率{merge_rate*100:.0f}%, 评论密度{pr_comment_density:.1f})"
            elif merge_rate > 0.4 or pr_comment_density > 0:
                score += 1
                details["pr_review"] = f"基础 (合并率{merge_rate*100:.0f}%)"
            else:
                details["pr_review"] = "待改进"
        else:
            details["pr_review"] = "无 PR"

        # ===== 项目成熟度 (5分) =====
        # 项目年龄 (2分)
        if data.age_in_days >= 365 * 3:
            score += 2
            age_level = "成熟"
        elif data.age_in_days >= 365:
            score += 1
            age_level = "发展中"
        else:
            age_level = "新项目"

        details["project_age"] = f"{data.age_in_days // 365} 年 ({age_level})"

        # Star/Fork 比率 (2分)
        if data.forks > 0:
            ratio = data.stars / data.forks
            if 3 <= ratio <= 15:
                score += 2
                details["star_fork_ratio"] = f"{ratio:.1f} (健康)"
            elif 2 <= ratio <= 20:
                score += 1
                details["star_fork_ratio"] = f"{ratio:.1f} (可接受)"
            else:
                details["star_fork_ratio"] = f"{ratio:.1f}"
        else:
            if data.stars > 0:
                details["star_fork_ratio"] = "无 Forks"
            else:
                details["star_fork_ratio"] = "-"

        # 持续维护 (1分)
        if data.maintained_for_years >= 2:
            score += 1
            details["maintained"] = "长期维护"
        else:
            details["maintained"] = "短期维护"

        final_score = min(30, score)

        return DimensionScore(
            score=round(final_score, 1),
            max_score=30,
            percentage=round((final_score / 30) * 100, 1),
            confidence=confidence,
            details=details,
        )

    @staticmethod
    def get_rating(total_score: float) -> str:
        """根据总分获取评级

        Args:
            total_score: 总分 (0-100)

        Returns:
            评级字符串 (A+, A, B+, B, C, D)
        """
        if total_score >= 85:
            return "A+ (优秀)"
        if total_score >= 75:
            return "A (良好)"
        if total_score >= 65:
            return "B+ (中上)"
        if total_score >= 55:
            return "B (中等)"
        if total_score >= 45:
            return "C (一般)"
        return "D (较差)"

    @staticmethod
    def generate_strengths_and_weaknesses(
        data: ProjectEvaluationData,
        scores: dict,
    ) -> tuple[list[str], list[str]]:
        """生成项目的优势和不足列表

        Args:
            data: 项目评估原始数据
            scores: 维度评分结果

        Returns:
            (优势列表, 不足列表)
        """
        strengths = []
        weaknesses = []

        # 代码质量维度
        cq_score = scores["code_quality"].score
        if cq_score >= 25:
            strengths.append("📚 文档齐全，易于上手和贡献")
        if cq_score < 15:
            weaknesses.append("⚠️ 文档或许可证不完整")

        # 活跃度维度
        activity_score = scores["activity"].score
        if activity_score >= 35:
            strengths.append("🔄 持续维护，更新频繁")
        if activity_score < 20:
            weaknesses.append("⚠️ 项目更新不频繁，可能面临维护困难")

        # 社区健康度维度
        ch_score = scores["community_health"].score
        if ch_score >= 25:
            strengths.append("👥 社区活跃，贡献者众多")
        if data.open_issues > data.closed_issues * 2:
            weaknesses.append("⚠️ Open Issues 数量较多，可能需要加强问题管理")

        # 其他指标
        if data.stars > 1000:
            strengths.append("⭐ Star 数量充足，用户认可度高")

        # 基于 Release 频率判断开发活跃度
        if data.releases_last_year >= 6:
            strengths.append("🚀 开发活跃，版本发布频繁")
        elif data.releases_last_year < 2:
            weaknesses.append("⚠️ 版本发布不频繁，可能维护缓慢")

        if data.has_license and data.has_contributing:
            strengths.append("✅ 项目管理规范，有明确的贡献指南")

        if not data.has_readme or data.readme_length < 300:
            weaknesses.append("⚠️ README 可能不够详细")

        if data.closed_issues / max(1, data.open_issues + data.closed_issues) > 0.85:
            strengths.append("✅ Issue 处理及时，响应良好")

        return strengths, weaknesses

    @staticmethod
    def generate_recommendation(total_score: float) -> str:
        """生成推荐建议

        Args:
            total_score: 总分

        Returns:
            推荐建议文本
        """
        if total_score >= 85:
            return "✅ **强烈推荐** - 这是一个高质量、活跃维护的项目，代码质量有保障，社区健康，开发团队响应及时。非常适合在生产环境中使用，也是学习开源项目的优秀案例。"
        if total_score >= 75:
            return "✅ **推荐使用** - 这是一个良好维护的项目，具有较好的代码质量和社区支持。可以放心在生产环境中使用，但建议关注其更新动态。"
        if total_score >= 65:
            return "👍 **可以使用** - 这个项目总体不错，但在某些方面（如文档、活跃度或社区规模）还有改进空间。可以使用，但建议对关键功能进行充分测试。"
        if total_score >= 55:
            return "⚠️ **谨慎使用** - 这个项目有一定的实用价值，但在维护、文档或社区支持方面存在不足。如果使用，建议做好风险评估和备选方案准备。"
        if total_score >= 45:
            return "❌ **需要评估** - 这个项目可能存在明显的维护问题或其他风险因素。不建议在关键业务中使用，除非有充分的技术支持能力。"
        return "❌ **不推荐** - 这个项目在多个方面存在问题，可能面临维护困难。不建议在生产环境中使用。"

    def generate_scoring_breakdown(self, data: ProjectEvaluationData, scores: dict) -> dict:
        """生成评分点的详细分解，显示每个评分项如何得出

        Args:
            data: 项目评估原始数据
            scores: 维度评分结果

        Returns:
            包含详细评分点分解的字典
        """
        return {
            "code_quality": {
                "total_score": scores["code_quality"].score,
                "max_score": 30,
                "percentage": scores["code_quality"].percentage,
                "confidence": scores["code_quality"].confidence,
                "details": scores["code_quality"].details,
                "raw_metrics": {
                    "has_readme": data.has_readme,
                    "readme_length": data.readme_length,
                    "has_license": data.has_license,
                    "has_contributing": data.has_contributing,
                    "has_code_of_conduct": data.has_code_of_conduct,
                    "has_standard_dirs": data.has_standard_dirs,
                    "primary_language": data.primary_language,
                    "language_count": data.language_count,
                    "release_count": data.release_count,
                    "protected_branches": data.protected_branches,
                },
            },
            "activity": {
                "total_score": scores["activity"].score,
                "max_score": 40,
                "percentage": scores["activity"].percentage,
                "confidence": scores["activity"].confidence,
                "details": scores["activity"].details,
                "raw_metrics": {
                    "releases_last_year": data.releases_last_year,
                    "updated_at": data.updated_at.isoformat(),
                    "days_since_update": (datetime.now(timezone.utc) - data.updated_at).days,
                    "open_issues": data.open_issues,
                    "closed_issues": data.closed_issues,
                    "issue_close_rate": (
                        round(
                            data.closed_issues / max(1, data.open_issues + data.closed_issues) * 100,
                            1,
                        )
                        if (data.open_issues + data.closed_issues) > 0
                        else 0
                    ),
                    "total_prs": data.total_prs,
                    "merged_prs": data.merged_prs,
                    "pr_merge_rate": (
                        round(
                            data.merged_prs / max(1, data.total_prs) * 100,
                            1,
                        )
                        if data.total_prs > 0
                        else 0
                    ),
                },
            },
            "community_health": {
                "total_score": scores["community_health"].score,
                "max_score": 30,
                "percentage": scores["community_health"].percentage,
                "confidence": scores["community_health"].confidence,
                "details": scores["community_health"].details,
                "raw_metrics": {
                    "stars": data.stars,
                    "forks": data.forks,
                    "contributors": data.contributors,
                    "age_in_days": data.age_in_days,
                    "age_in_years": round(data.age_in_days / 365, 1),
                    "maintained_for_years": round(data.maintained_for_years, 1),
                    "issue_comments_avg": round(data.issue_comments_avg, 2),
                    "pr_comment_density": round(data.pr_comment_density, 2),
                    "star_fork_ratio": (
                        round(
                            data.stars / max(1, data.forks),
                            2,
                        )
                        if data.forks > 0
                        else "N/A"
                    ),
                },
            },
            "summary": {
                "total_score": scores["code_quality"].score + scores["activity"].score + scores["community_health"].score,
                "max_score": 100,
                "rating": self.get_rating(
                    scores["code_quality"].score + scores["activity"].score + scores["community_health"].score,
                ),
                "data_confidence": data.commits_confidence,  # 整体数据可信度
            },
        }
