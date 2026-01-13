"""GitHub 项目评估结果格式化器"""

from datetime import datetime, timezone

from .models import ProjectEvaluation, ProjectEvaluationData


class EvaluationFormatter:
    """评估结果格式化器 - 生成各种格式的输出"""

    @staticmethod
    def to_debug_report(evaluation: ProjectEvaluation, raw_data: ProjectEvaluationData) -> str:
        """生成详细的调试报告，显示原始数据和评分对比

        Args:
            evaluation: 项目评估结果
            raw_data: 原始评估数据

        Returns:
            详细的调试报告
        """
        lines = []

        # ===== 标题 =====
        lines.append("# 🔍 GitHub 项目评估详细调试报告\n")
        lines.append(f"## 项目: {evaluation.repo_full_name}\n")
        lines.append("---\n")

        # ===== 原始数据 - 代码质量相关 =====
        lines.append("## 📊 【原始数据】代码质量指标\n")
        lines.append(f"- has_readme: {raw_data.has_readme}\n")
        lines.append(f"- readme_length: {raw_data.readme_length} 字符\n")
        lines.append(f"- has_license: {raw_data.has_license}\n")
        lines.append(f"- license_name: {raw_data.license_name}\n")
        lines.append(f"- has_contributing: {raw_data.has_contributing}\n")
        lines.append(f"- has_code_of_conduct: {raw_data.has_code_of_conduct}\n")
        lines.append(f"- has_standard_dirs: {raw_data.has_standard_dirs}\n")
        lines.append(f"- primary_language: {raw_data.primary_language}\n")
        lines.append(f"- language_count: {raw_data.language_count}\n")
        lines.append(f"- language_distribution: {raw_data.language_distribution}\n")

        lines.append("\n### 💡 评分结果\n")
        cq = evaluation.code_quality
        lines.append(f"**代码质量得分: {cq.score:.1f}/{cq.max_score} ({cq.percentage:.1f}%)**\n")
        lines.append("评分详情:\n")
        for key, value in cq.details.items():
            lines.append(f"  - {key}: {value}\n")

        # ===== 原始数据 - 活跃度相关 =====
        lines.append("\n---\n")
        lines.append("## 📊 【原始数据】项目活跃度指标 (v2.0)\n")
        lines.append(f"- updated_at: {raw_data.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        days_since_update = (datetime.now(timezone.utc) - raw_data.updated_at).days
        lines.append(f"- days_since_update: {days_since_update} 天\n")
        lines.append(f"- release_count: {raw_data.release_count}\n")
        lines.append(f"- releases_last_year: {raw_data.releases_last_year}\n")
        lines.append(f"- open_issues: {raw_data.open_issues}\n")
        lines.append(f"- closed_issues: {raw_data.closed_issues}\n")
        lines.append(f"- issue_comments_total: {raw_data.issue_comments_total} 条\n")
        lines.append(f"- issue_comments_avg: {raw_data.issue_comments_avg:.2f} 条/issue\n")
        lines.append(f"- total_prs: {raw_data.total_prs}\n")
        lines.append(f"- merged_prs: {raw_data.merged_prs}\n")
        lines.append(f"- pr_comments_total: {raw_data.pr_comments_total} 条\n")
        lines.append(f"- pr_comment_density: {raw_data.pr_comment_density:.2f} 条/merged_pr\n")
        lines.append(f"- protected_branches: {raw_data.protected_branches}\n")

        # 计算关键比率
        if raw_data.open_issues + raw_data.closed_issues > 0:
            issue_close_rate = (raw_data.closed_issues / (raw_data.open_issues + raw_data.closed_issues)) * 100
            lines.append(f"- 📈 Issue 关闭率: {issue_close_rate:.1f}%\n")

        if raw_data.total_prs > 0:
            pr_merge_rate = (raw_data.merged_prs / raw_data.total_prs) * 100
            lines.append(f"- 📈 PR 合并率: {pr_merge_rate:.1f}%\n")

        lines.append("\n**ℹ️ 数据来源说明:**\n")
        lines.append("- `releases_last_year`: 过去一年内发布的版本数（v2.0核心指标）\n")
        lines.append("- `updated_at`: 项目最后更新时间（v2.0核心指标）\n")

        lines.append("\n### 💡 评分结果\n")
        activity = evaluation.activity
        lines.append(f"**项目活跃度得分: {activity.score:.1f}/{activity.max_score} ({activity.percentage:.1f}%)**\n")
        lines.append("评分详情:\n")
        for key, value in activity.details.items():
            lines.append(f"  - {key}: {value}\n")

        # ===== 原始数据 - 社区健康度相关 =====
        lines.append("\n---\n")
        lines.append("## 📊 【原始数据】社区健康度指标\n")
        lines.append(f"- stars: {raw_data.stars}\n")
        lines.append(f"- forks: {raw_data.forks}\n")
        lines.append(f"- contributors: {raw_data.contributors}\n")
        lines.append(f"- age_in_days: {raw_data.age_in_days} 天\n")
        lines.append(f"- maintained_for_years: {raw_data.maintained_for_years:.2f} 年\n")

        # 计算关键比率
        if raw_data.forks > 0:
            star_fork_ratio = raw_data.stars / raw_data.forks
            lines.append(f"- 📈 Star/Fork 比率: {star_fork_ratio:.2f}\n")

        if raw_data.stars > 0:
            issue_ratio = raw_data.open_issues / raw_data.stars
            lines.append(f"- 📈 Open Issues/Stars 比率: {issue_ratio:.4f}\n")

        lines.append("\n### 💡 评分结果\n")
        ch = evaluation.community_health
        lines.append(f"**社区健康度得分: {ch.score:.1f}/{ch.max_score} ({ch.percentage:.1f}%)**\n")
        lines.append("评分详情:\n")
        for key, value in ch.details.items():
            lines.append(f"  - {key}: {value}\n")

        # ===== 综合评分汇总 =====
        lines.append("\n---\n")
        lines.append("## 📊 综合评分汇总\n")
        lines.append(f"**代码质量**: {evaluation.code_quality.score:.1f}/30 ({evaluation.code_quality.percentage:.1f}%)\n")
        lines.append(f"**项目活跃度**: {evaluation.activity.score:.1f}/40 ({evaluation.activity.percentage:.1f}%)\n")
        lines.append(
            f"**社区健康度**: {evaluation.community_health.score:.1f}/30 ({evaluation.community_health.percentage:.1f}%)\n",
        )
        lines.append(f"\n**总分**: {evaluation.total_score:.1f}/100\n")
        lines.append(f"**评级**: {evaluation.rating}\n")

        # ===== 数据质量诊断 =====
        lines.append("\n---\n")
        lines.append("## 🔧 数据质量诊断 (v2.0)\n")
        lines.append("### ⚠️ 可能的问题\n")

        # v2.0诊断逻辑
        days_since_update = (datetime.now(timezone.utc) - raw_data.updated_at).days
        if days_since_update > 365:
            lines.append(f"- **项目长期停滞**: {days_since_update}天未更新\n")
            lines.append("  → 可能存在维护风险\n")

        if raw_data.releases_last_year < 1:
            lines.append("- **无正式发行版本**: 过去一年内未发布任何版本\n")
            lines.append("  → 可能难以获得稳定使用体验\n")

        if raw_data.open_issues > raw_data.closed_issues * 2:
            lines.append(f"- **Open Issues堆积**: {raw_data.open_issues} 个未关闭问题\n")
            lines.append("  → 可能需要更多维护人力\n")

        lines.append("\n### 📌 建议\n")
        lines.append("如果评分与实际不符，可能需要:\n")
        lines.append("1. 查看项目的Releases页面了解发版频率\n")
        lines.append("2. 检查项目的最近更新: 点击GitHub上的 'Commits' 查看最新活动\n")
        lines.append("3. 查看Open Issues和PR的活跃度\n")

        # ===== 优缺点分析 =====
        lines.append("\n---\n")
        lines.append("## 📋 评估总结\n")

        if evaluation.strengths:
            lines.append("### 💪 主要优势\n")
            for strength in evaluation.strengths:
                lines.append(f"- {strength}\n")

        if evaluation.weaknesses:
            lines.append("\n### ⚠️ 可改进之处\n")
            for weakness in evaluation.weaknesses:
                lines.append(f"- {weakness}\n")

        lines.append("\n### 🎯 推荐建议\n")
        lines.append(f"{evaluation.recommendation}\n")

        return "".join(lines)

    @staticmethod
    def to_brief_report(evaluation: ProjectEvaluation) -> str:
        """生成简洁报告（限制在1000字符内）

        Args:
            evaluation: 项目评估结果

        Returns:
            简洁的评估报告
        """
        lines = []

        # 标题和总分
        lines.append(f"📊 **{evaluation.repo_full_name}**\n")
        lines.append(f"总分: **{evaluation.total_score:.1f}/100** | 评级: **{evaluation.rating}**\n")

        # 评分细分
        lines.append("\n📌 维度评分:\n")
        lines.append(f"- 代码质量: {evaluation.code_quality.score:.1f}/{evaluation.code_quality.max_score}\n")
        lines.append(f"- 项目活跃: {evaluation.activity.score:.1f}/{evaluation.activity.max_score}\n")
        lines.append(f"- 社区健康: {evaluation.community_health.score:.1f}/{evaluation.community_health.max_score}\n")

        # 关键指标
        lines.append("\n🎯 关键指标:\n")
        if evaluation.key_metrics:
            for key, value in list(evaluation.key_metrics.items())[:5]:  # 仅显示前5个
                lines.append(f"- {key}: {value}\n")

        # 优缺点（简短版）
        if evaluation.strengths:
            lines.append("\n✅ 优势:\n")
            for s in evaluation.strengths[:2]:  # 仅显示前2个
                lines.append(f"- {s}\n")

        if evaluation.weaknesses:
            lines.append("\n⚠️ 不足:\n")
            for w in evaluation.weaknesses[:2]:  # 仅显示前2个
                lines.append(f"- {w}\n")

        # 建议
        lines.append(f"\n💡 {evaluation.recommendation}\n")

        report = "".join(lines)

        # 检查长度，如果超过1000字符就进一步截断
        if len(report) > 1000:
            report = report[:1000] + "..."

        return report

    @staticmethod
    def to_markdown_card(evaluation: ProjectEvaluation) -> str:
        """生成 Markdown 格式的评分卡片

        Args:
            evaluation: 项目评估结果

        Returns:
            Markdown 格式的评分卡片
        """
        lines = []

        # ===== 标题和总分 =====
        lines.append("# 🎯 GitHub 项目评估报告\n")
        lines.append(
            f"## 📊 综合评分: **{evaluation.total_score:.1f}/100** | 评级: **{evaluation.rating}**\n",
        )
        lines.append("---\n")

        # ===== 维度得分 =====
        lines.append("## 📈 维度得分\n")

        # 代码质量
        cq = evaluation.code_quality
        lines.append(f"### 🔨 代码质量: {cq.score:.1f}/{cq.max_score}\n")
        for key, value in cq.details.items():
            lines.append(f"- **{key}**: {value}\n")

        # 活跃度
        lines.append("")
        activity = evaluation.activity
        lines.append(f"### 🚀 项目活跃度: {activity.score:.1f}/{activity.max_score}\n")
        for key, value in activity.details.items():
            lines.append(f"- **{key}**: {value}\n")

        # 社区健康度
        lines.append("")
        ch = evaluation.community_health
        lines.append(f"### 🌟 社区健康度: {ch.score:.1f}/{ch.max_score}\n")
        for key, value in ch.details.items():
            lines.append(f"- **{key}**: {value}\n")

        # ===== 关键指标 =====
        lines.append("\n## 💡 关键指标\n")
        lines.append("| 指标 | 数值 |\n")
        lines.append("|------|------|\n")

        # 构建指标表格
        metrics_map = {
            "⭐ Stars": "stars",
            "🔀 Forks": "forks",
            "👥 Contributors": "contributors",
            "📊 周均 Commits": "commits_per_week",
            "📋 Open Issues": "open_issues",
            "📝 最近 3 月 Commits": "recent_commits",
            "📦 Release 数": "release_count",
            "💻 主要语言": "primary_language",
            "📅 项目年龄": "project_age_years",
        }

        for label, key in metrics_map.items():
            if key in evaluation.key_metrics:
                value = evaluation.key_metrics[key]
                lines.append(f"| {label} | {value} |\n")

        # ===== 评估总结 =====
        lines.append("\n## ✨ 评估总结\n")

        if evaluation.summary:
            lines.append(f"{evaluation.summary}\n\n")

        # 优势
        if evaluation.strengths:
            lines.append("### 💪 主要优势\n")
            for strength in evaluation.strengths:
                lines.append(f"- {strength}\n")
            lines.append("")

        # 不足
        if evaluation.weaknesses:
            lines.append("### ⚠️ 可改进之处\n")
            for weakness in evaluation.weaknesses:
                lines.append(f"- {weakness}\n")
            lines.append("")

        # 推荐建议
        lines.append("### 🎯 推荐建议\n")
        lines.append(f"{evaluation.recommendation}\n")

        # ===== 尾部信息 =====
        lines.append("\n---\n")
        lines.append(f"**评估时间**: {evaluation.evaluated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
        lines.append(f"**项目链接**: [{evaluation.repo_full_name}]({evaluation.repo_url})\n")
        lines.append("**数据来源**: GitHub API\n")

        return "".join(lines)

    @staticmethod
    def to_plain_text(evaluation: ProjectEvaluation) -> str:
        """生成纯文本格式的评估报告

        Args:
            evaluation: 项目评估结果

        Returns:
            纯文本格式的评估报告
        """
        lines = []

        # 标题
        lines.append("=" * 70)
        lines.append("GitHub 项目评估报告")
        lines.append("=" * 70)
        lines.append("")

        # 项目信息
        lines.append(f"项目: {evaluation.repo_full_name}")
        lines.append(f"链接: {evaluation.repo_url}")
        lines.append(f"评估时间: {evaluation.evaluated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append("")

        # 总分
        lines.append("-" * 70)
        lines.append(f"综合评分: {evaluation.total_score:.1f}/100 | 评级: {evaluation.rating}")
        lines.append("-" * 70)
        lines.append("")

        # 维度得分
        lines.append("【维度得分】")
        lines.append(f"  代码质量: {evaluation.code_quality.score:.1f}/{evaluation.code_quality.max_score}")
        lines.append(f"  项目活跃度: {evaluation.activity.score:.1f}/{evaluation.activity.max_score}")
        lines.append(f"  社区健康度: {evaluation.community_health.score:.1f}/{evaluation.community_health.max_score}")
        lines.append("")

        # 关键指标
        lines.append("【关键指标】")
        for key, value in evaluation.key_metrics.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

        # 优势
        if evaluation.strengths:
            lines.append("【主要优势】")
            for strength in evaluation.strengths:
                lines.append(f"  ✓ {strength}")
            lines.append("")

        # 不足
        if evaluation.weaknesses:
            lines.append("【可改进之处】")
            for weakness in evaluation.weaknesses:
                lines.append(f"  ✗ {weakness}")
            lines.append("")

        # 推荐
        lines.append("【推荐建议】")
        lines.append(evaluation.recommendation)
        lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)

    @staticmethod
    def to_detailed_scoring_report(
        evaluation: ProjectEvaluation,
        scoring_breakdown: dict,
    ) -> str:
        """生成详细的评分逐项报告（每行一个检查项）

        Args:
            evaluation: 项目评估结果
            scoring_breakdown: 评分点分解

        Returns:
            格式化的详细评分报告
        """
        lines = []

        # ===== 标题和总分 =====
        total_score = evaluation.total_score
        lines.append("=" * 80)
        lines.append(f"🎯 综合评分: {total_score}/100 | 评级: {evaluation.rating}")
        lines.append(f"📊 数据可信度: {evaluation.confidence}")
        lines.append("=" * 80)
        lines.append("")

        # ===== 代码质量维度 =====
        lines.append("📝 【代码质量】30分")
        lines.append("-" * 80)
        cq_breakdown = scoring_breakdown["code_quality"]
        cq_score = cq_breakdown["total_score"]
        lines.append(f"当前得分: {cq_score}/30 ({cq_breakdown['percentage']:.1f}%)")
        lines.append(f"可信度: {cq_breakdown['confidence']}")
        lines.append("")

        # 详细检查项
        raw_cq = cq_breakdown["raw_metrics"]

        # README
        readme_status = "✓" if raw_cq["has_readme"] else "✗"
        readme_detail = f"(长度: {raw_cq['readme_length']} 字符)" if raw_cq["has_readme"] else "(缺失)"
        lines.append(f"  {readme_status} README文档: {readme_detail}")
        if raw_cq["has_readme"] and raw_cq["readme_length"] >= 500:
            lines.append("     → 得分: +5 分 (优秀)")
        elif raw_cq["has_readme"]:
            lines.append("     → 得分: +3 分 (良好)")
        else:
            lines.append("     → 得分: 0 分 (缺失)")

        # LICENSE
        license_status = "✓" if raw_cq["has_license"] else "✗"
        license_name = raw_cq.get("license_name", "无")
        lines.append(f"  {license_status} 许可证: {license_name}")
        lines.append(f"     → 得分: {'2 分' if raw_cq['has_license'] else '0 分'}")

        # CONTRIBUTING
        contrib_status = "✓" if raw_cq["has_contributing"] else "✗"
        lines.append(f"  {contrib_status} 贡献指南")
        lines.append(f"     → 得分: {'1.5 分' if raw_cq['has_contributing'] else '0 分'}")

        # CODE_OF_CONDUCT
        coc_status = "✓" if raw_cq.get("has_code_of_conduct") else "✗"
        lines.append(f"  {coc_status} 行为准则")
        lines.append(f"     → 得分: {'1.5 分' if raw_cq.get('has_code_of_conduct') else '0 分'}")

        # 主语言
        lines.append(f"  🔧 主要语言: {raw_cq['primary_language']}")
        lines.append("     → 得分: 3 分")

        # 语言多样性
        lang_count = raw_cq["language_count"]
        if 1 <= lang_count <= 5:
            lang_level = "合理"
            lang_score = 4
        elif 5 < lang_count <= 10:
            lang_level = "可接受"
            lang_score = 2
        elif lang_count > 10:
            lang_level = "过度分散"
            lang_score = 0
        else:
            lang_level = "未识别"
            lang_score = 0
        lines.append(f"  📚 语言多样性: {lang_count} 种语言 ({lang_level})")
        lines.append(f"     → 得分: {lang_score} 分")

        # 标准目录
        std_dirs_status = "✓" if raw_cq["has_standard_dirs"] else "✗"
        lines.append(f"  {std_dirs_status} 标准目录结构")
        lines.append(f"     → 得分: {'3 分' if raw_cq['has_standard_dirs'] else '0-1.5 分'}")

        # Release管理
        release_count = raw_cq["release_count"]
        if release_count >= 4:
            release_level = "规范"
            release_score = 3
        elif release_count >= 2:
            release_level = "基础"
            release_score = 2
        elif release_count >= 1:
            release_level = "初级"
            release_score = 1
        else:
            release_level = "无"
            release_score = 0
        lines.append(f"  📦 Release管理: {release_count} 个发行版 ({release_level})")
        lines.append(f"     → 得分: {release_score} 分")

        # 分支保护
        protected = raw_cq["protected_branches"]
        lines.append(f"  🔒 分支保护: {protected} 个受保护分支")
        lines.append(f"     → 得分: {min(2, protected * 0.5)} 分")

        lines.append(f"\n   【代码质量详情】{dict(cq_breakdown['details'])}")
        lines.append("")

        # ===== 活跃度维度 =====
        lines.append("🚀 【项目活跃度】40分")
        lines.append("-" * 80)
        activity_breakdown = scoring_breakdown["activity"]
        activity_score = activity_breakdown["total_score"]
        lines.append(f"当前得分: {activity_score}/40 ({activity_breakdown['percentage']:.1f}%)")
        lines.append(f"可信度: {activity_breakdown['confidence']}")
        lines.append("")

        raw_activity = activity_breakdown["raw_metrics"]

        # Release 发布频率 (v2.0新指标)
        releases = raw_activity.get("releases_last_year", 0)
        if releases >= 6:
            release_freq_level = "高频 (≥6次/年)"
            release_freq_score = 12
        elif releases >= 4:
            release_freq_level = "中上 (4-5次/年)"
            release_freq_score = 10
        elif releases >= 2:
            release_freq_level = "中等 (2-3次/年)"
            release_freq_score = 7
        elif releases >= 1:
            release_freq_level = "低频 (1次/年)"
            release_freq_score = 4
        else:
            release_freq_level = "无发行"
            release_freq_score = 0

        lines.append(f"  📦 Release发布频率: {releases}次/年 ({release_freq_level})")
        lines.append(f"     → 得分: {release_freq_score} 分")

        # 项目新鲜度 (v2.0新指标)
        days_since_update = raw_activity.get("days_since_update", 0)
        if days_since_update <= 30:
            freshness_level = "🟢 持续活跃"
            freshness_score = 15
        elif days_since_update <= 90:
            freshness_level = "🟡 定期维护"
            freshness_score = 12
        elif days_since_update <= 180:
            freshness_level = "🟠 不太频繁"
            freshness_score = 8
        elif days_since_update <= 365:
            freshness_level = "🔴 长期停滞"
            freshness_score = 4
        else:
            freshness_level = "⚫ 已放弃"
            freshness_score = 0

        lines.append(f"  🕐 项目新鲜度: {days_since_update}天未更新 ({freshness_level})")
        lines.append(f"     → 得分: {freshness_score} 分")

        # Issue统计
        open_issues = raw_activity["open_issues"]
        closed_issues = raw_activity["closed_issues"]
        issue_close_rate = raw_activity["issue_close_rate"]

        lines.append(f"  📋 Issue管理: {open_issues} 开放 | {closed_issues} 已关闭")
        lines.append(f"     关闭率: {issue_close_rate:.1f}%")
        lines.append(f"     → 得分: {min(5, issue_close_rate / 20):.1f} 分")

        # PR统计
        total_prs = raw_activity["total_prs"]
        merged_prs = raw_activity["merged_prs"]
        pr_merge_rate = raw_activity["pr_merge_rate"]

        lines.append(f"  🔀 PR管理: {total_prs} 个PR | {merged_prs} 已合并")
        lines.append(f"     合并率: {pr_merge_rate:.1f}%")
        lines.append(f"     → 得分: {min(5, pr_merge_rate / 20):.1f} 分")

        lines.append(f"\n   【活跃度详情】{dict(activity_breakdown['details'])}")
        lines.append("")

        # ===== 社区健康度维度 =====
        lines.append("👥 【社区健康度】30分")
        lines.append("-" * 80)
        community_breakdown = scoring_breakdown["community_health"]
        community_score = community_breakdown["total_score"]
        lines.append(f"当前得分: {community_score}/30 ({community_breakdown['percentage']:.1f}%)")
        lines.append(f"可信度: {community_breakdown['confidence']}")
        lines.append("")

        raw_community = community_breakdown["raw_metrics"]

        # Stars
        stars = raw_community["stars"]
        if stars > 0:
            star_score = min(6, __import__("math").log10(stars + 1) * 1.5)
        else:
            star_score = 0
        lines.append(f"  ⭐ Stars: {stars:,}")
        lines.append(f"     → 得分: {star_score:.1f} 分 (对数评分)")

        # Forks
        forks = raw_community["forks"]
        if forks > 0:
            fork_score = min(4, __import__("math").log10(forks + 1) * 1.2)
        else:
            fork_score = 0
        lines.append(f"  🔀 Forks: {forks:,}")
        lines.append(f"     → 得分: {fork_score:.1f} 分 (对数评分)")

        # Contributors
        contributors = raw_community["contributors"]
        if contributors > 0:
            contrib_score = min(5, __import__("math").log10(contributors + 1) * 1.8)
            contrib_level = "活跃" if contributors >= 10 else "少量"
        else:
            contrib_score = 0
            contrib_level = "无"
        lines.append(f"  👥 贡献者: {contributors} 人 ({contrib_level})")
        lines.append(f"     → 得分: {contrib_score:.1f} 分 (对数评分)")

        # Issue讨论
        issue_comments_avg = raw_community["issue_comments_avg"]
        if issue_comments_avg >= 3:
            discussion_level = "活跃"
            discussion_score = 5
        elif issue_comments_avg >= 1:
            discussion_level = "中等"
            discussion_score = 3
        elif issue_comments_avg > 0:
            discussion_level = "低活动"
            discussion_score = 1
        else:
            discussion_level = "无评论"
            discussion_score = 0

        lines.append(f"  💬 Issue讨论: 平均 {issue_comments_avg:.2f} 条评论/issue ({discussion_level})")
        lines.append(f"     → 得分: {discussion_score} 分")

        # PR评审
        pr_density = raw_community["pr_comment_density"]
        if pr_density >= 1:
            review_level = "优秀"
            review_score = 5
        elif pr_density >= 0.5:
            review_level = "良好"
            review_score = 3
        elif pr_density > 0:
            review_level = "基础"
            review_score = 1
        else:
            review_level = "待改进"
            review_score = 0

        lines.append(f"  🔍 PR评审: {pr_density:.2f} 条评论/merged_pr ({review_level})")
        lines.append(f"     → 得分: {review_score} 分")

        # 项目成熟度
        age_years = raw_community["age_in_years"]
        age_days = raw_community["age_in_days"]
        if age_years >= 3:
            age_level = "成熟"
            age_score = 2
        elif age_years >= 1:
            age_level = "发展中"
            age_score = 1
        else:
            age_level = "新项目"
            age_score = 0

        lines.append(f"  📅 项目年龄: {age_years:.1f} 年 ({age_level}) [创建至今: {age_days} 天]")
        lines.append(f"     → 得分: {age_score} 分")

        # Star/Fork比率
        star_fork_ratio = raw_community["star_fork_ratio"]
        if isinstance(star_fork_ratio, (int, float)):
            if 3 <= star_fork_ratio <= 15:
                ratio_level = "健康"
                ratio_score = 2
            elif 2 <= star_fork_ratio <= 20:
                ratio_level = "可接受"
                ratio_score = 1
            else:
                ratio_level = "不均"
                ratio_score = 0
        else:
            ratio_level = "无Fork"
            ratio_score = 0

        lines.append(f"  ⚖️ Star/Fork比: {star_fork_ratio} ({ratio_level})")
        lines.append(f"     → 得分: {ratio_score} 分")

        # 持续维护
        maintained_years = raw_community["maintained_for_years"]
        if maintained_years >= 2:
            maintain_level = "长期"
            maintain_score = 1
        else:
            maintain_level = "短期"
            maintain_score = 0

        lines.append(f"  🔧 持续维护: {maintain_level}维护 ({maintained_years:.1f} 年)")
        lines.append(f"     → 得分: {maintain_score} 分")

        lines.append(f"\n   【社区健康度详情】{dict(community_breakdown['details'])}")
        lines.append("")

        # ===== 总结 =====
        lines.append("=" * 80)
        lines.append(f"📊 最终评分: {total_score}/100")
        lines.append(f"📈 评级: {evaluation.rating}")
        lines.append(f"🎯 推荐: {evaluation.recommendation}")
        lines.append("=" * 80)

        if evaluation.strengths:
            lines.append("\n✅ 主要优势:")
            for strength in evaluation.strengths:
                lines.append(f"   • {strength}")

        if evaluation.weaknesses:
            lines.append("\n⚠️ 可改进之处:")
            for weakness in evaluation.weaknesses:
                lines.append(f"   • {weakness}")

        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_compact_summary(evaluation: ProjectEvaluation) -> str:
        """生成简洁的评估摘要（适合快速查看）

        Args:
            evaluation: 项目评估结果

        Returns:
            简洁摘要
        """
        return f"""
🎯 **{evaluation.repo_full_name}** 项目评估

📊 综合评分: **{evaluation.total_score:.1f}/100** ({evaluation.rating})

📈 维度得分:
  • 代码质量: {evaluation.code_quality.score:.1f}/30
  • 活跃度: {evaluation.activity.score:.1f}/40
  • 社区健康度: {evaluation.community_health.score:.1f}/30

🎯 建议: {evaluation.recommendation}
""".strip()

    @staticmethod
    def generate_detailed_analysis(evaluation: ProjectEvaluation) -> dict:
        """生成详细的分析数据供进一步处理

        Args:
            evaluation: 项目评估结果

        Returns:
            包含详细分析数据的字典
        """
        return {
            "basic_info": {
                "repo_full_name": evaluation.repo_full_name,
                "repo_url": evaluation.repo_url,
                "evaluated_at": evaluation.evaluated_at.isoformat(),
            },
            "scores": {
                "total": {
                    "score": evaluation.total_score,
                    "rating": evaluation.rating,
                },
                "code_quality": {
                    "score": evaluation.code_quality.score,
                    "max_score": evaluation.code_quality.max_score,
                    "percentage": evaluation.code_quality.percentage,
                    "details": evaluation.code_quality.details,
                },
                "activity": {
                    "score": evaluation.activity.score,
                    "max_score": evaluation.activity.max_score,
                    "percentage": evaluation.activity.percentage,
                    "details": evaluation.activity.details,
                },
                "community_health": {
                    "score": evaluation.community_health.score,
                    "max_score": evaluation.community_health.max_score,
                    "percentage": evaluation.community_health.percentage,
                    "details": evaluation.community_health.details,
                },
            },
            "metrics": evaluation.key_metrics,
            "analysis": {
                "summary": evaluation.summary,
                "strengths": evaluation.strengths,
                "weaknesses": evaluation.weaknesses,
                "recommendation": evaluation.recommendation,
            },
        }
