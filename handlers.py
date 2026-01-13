"""GitHub 信息获取的沙盒方法"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.core import logger

from .client import GitHubClient
from .plugin import config, plugin
from .utils import (
    ExceptionHandler,
    ParameterValidator,
    ResponseFormatter,
    ValidationError,
    validate_and_handle,
)


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub项目基本信息与README",
    description="获取GitHub项目的原始信息（作者、Stars、Issues、Fork、主要语言、完整README等），供AI进行深度分析、对话和讨论，不提供评分",
)
async def get_github_info(_ctx: AgentCtx, github_url: str) -> str:
    """获取GitHub项目的原始信息与README

    这是一个代理方法，获取项目的原始详细信息（包括完整README内容）后由AI进行自由分析、总结和对话。
    AI可以基于这些信息来：
    - 了解项目的基本概况和设计目标
    - 阅读和分析完整的项目 README 文档
    - 自由讨论项目的功能和特性
    - 分析技术栈和依赖
    - 深度对话和代码分析

    Args:
        github_url: GitHub项目URL或 owner/repo 格式，例如：
                   - https://github.com/owner/repo
                   - owner/repo
                   - git@github.com:owner/repo.git

    Returns:
        str: 项目信息（包括README内容），将由AI进行处理和对话

    Example:
        get_github_info("https://github.com/python/cpython")
    """
    try:
        # 参数验证
        github_url = ParameterValidator.validate_github_url(github_url)

        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            # 获取项目信息和README
            repo_info = await client.get_repo_info(github_url)
            readme_info = await client.get_readme(github_url)

            # 构建返回信息
            parts = [
                ResponseFormatter.section("📦 GitHub 项目信息"),
                f"项目名称: {repo_info.repo}\n",
                f"完整标识: {repo_info.full_name}\n",
                f"项目作者: {repo_info.owner}\n",
                f"项目地址: {repo_info.url}\n",
                f"项目描述: {repo_info.description}\n",
                ResponseFormatter.subsection("📊 项目统计"),
                f"⭐ Star 数: {repo_info.stars}\n",
                f"📋 Issues 数: {repo_info.issues}\n",
                f"🔀 Fork 数: {repo_info.forks}\n",
                f"👥 贡献者: {repo_info.contributors}\n",
                f"📝 主要语言: {repo_info.language or '未知'}\n",
                f"📅 创建时间: {repo_info.created_at}\n",
                f"🔄 最后更新: {repo_info.updated_at}\n",
            ]

            # 添加 README 内容
            if readme_info:
                parts.extend(
                    [
                        ResponseFormatter.subsection("📖 项目 README"),
                        readme_info.content,
                    ],
                )
            else:
                parts.append("\n⚠️ 项目没有 README 文件\n")

            result = ResponseFormatter.build(parts)
            logger.info(f"✅ 成功获取项目信息: {repo_info.full_name}")
            return result

    except ValidationError as e:
        return ExceptionHandler.handle_validation_error("get_github_info", e)
    except Exception as e:
        return ExceptionHandler.handle_runtime_error("get_github_info", e)


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="搜索GitHub仓库",
    description="在GitHub上搜索符合关键词的仓库，支持按Stars、Forks等多种方式排序",
)
async def search_github_repositories(
    _ctx: AgentCtx,
    keyword: str,
    sort: str = "stars",
    per_page: int = 10,
    page: int = 1,
) -> str:
    """搜索 GitHub 仓库

    这是一个代理方法，搜索结果会交由 AI 进行分析和对话。

    Args:
        keyword: 搜索关键词，例如：
                - python web framework
                - machine learning
                - cli tool
        sort: 排序方式，可选值：
              - stars (按Stars排序，默认)
              - forks (按Fork数排序)
              - updated (按更新时间排序)
              - rating (按评分排序)
        per_page: 每页返回的结果数 (1-100，默认10)
        page: 页码 (默认第1页)

    Returns:
        str: 搜索结果，将由AI进行分析

    Example:
        search_github_repositories("python web framework", sort="stars", per_page=10)
    """
    try:
        # 参数验证
        keyword = ParameterValidator.validate_string(keyword, "keyword")
        per_page = ParameterValidator.validate_per_page(per_page)
        page = ParameterValidator.validate_page(page)

        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            results = await client.search_repositories(
                keyword=keyword,
                sort=sort,
                per_page=per_page,
                page=page,
            )

            if not results.repositories:
                return ResponseFormatter.warning(f"未找到符合关键词 '{keyword}' 的仓库")

            # 构建返回信息
            parts = [
                ResponseFormatter.section("🔍 GitHub 仓库搜索结果", 70),
                f"搜索关键词: {keyword}\n",
                f"排序方式: {sort}\n",
                f"总搜索结果: {results.total_count} 个\n",
                f"当前页: 第 {page} 页\n",
                f"本页显示: {len(results.repositories)} 个\n",
                f"{'─'*70}\n",
            ]

            for idx, repo in enumerate(results.repositories, 1):
                parts.append(f"\n{idx}. ⭐ {repo.full_name}\n")
                parts.append(f"   🔗 {repo.url}\n")
                parts.append(
                    f"   📊 Stars: {repo.stars} | Forks: {repo.forks} | Issues: {repo.issues}\n",
                )

                if repo.language:
                    parts.append(f"   🔤 主要语言: {repo.language}\n")

                if repo.description:
                    desc = repo.description[:100] + "..." if len(repo.description) > 100 else repo.description
                    parts.append(f"   📝 描述: {desc}\n")

                if repo.updated_at:
                    parts.append(f"   🔄 最后更新: {repo.updated_at[:10]}\n")

            # 添加分页提示
            parts.append(f"\n{'─'*70}\n")
            if results.has_more:
                parts.append(f"💡 提示: 还有更多结果，可以尝试下一页 (page={page + 1})\n")
            else:
                parts.append("💡 提示: 已显示全部搜索结果\n")

            result = ResponseFormatter.build(parts)
            logger.info(
                f"✅ 成功搜索 GitHub 仓库，关键词: {keyword}，共找到 {results.total_count} 个",
            )
            return result

    except ValidationError as e:
        return ExceptionHandler.handle_validation_error("search_github_repositories", e)
    except Exception as e:
        return ExceptionHandler.handle_runtime_error("search_github_repositories", e)


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub项目Commit历史",
    description="获取GitHub项目的提交历史记录，包含提交者、时间、文件变更等详细信息，用于分析项目开发活动",
)
async def get_github_commits(
    _ctx: AgentCtx,
    github_url: str,
    per_page: int = 10,
    page: int = 1,
) -> str:
    """获取 GitHub 项目的 Commit 历史

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        per_page: 每页返回的提交数 (1-100，默认10)
        page: 页码

    Returns:
        str: 提交历史信息

    Example:
        get_github_commits("python/cpython", per_page=20)
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            commits = await client.get_commits(github_url, per_page, page)

            if not commits:
                return "⚠️ 未找到任何提交记录"

            # 构建返回信息
            info_parts = [
                "📝 GitHub 项目 Commit 历史\n",
                f"{'='*60}\n",
                f"总共获取: {len(commits)} 条提交记录\n",
                f"{'─'*60}\n",
            ]

            for idx, commit in enumerate(commits, 1):
                commit_info = [
                    f"\n{idx}. Commit SHA: {commit.sha}",
                    f"   📝 信息: {commit.message}",
                    f"   👤 作者: {commit.author_name}",
                    f"   ⏰ 时间: {commit.committed_at}",
                ]

                if commit.files_changed > 0:
                    commit_info.append(f"   📊 文件变更: {commit.files_changed} 个文件")
                    commit_info.append(f"      ✨ 新增: {commit.additions} 行，删除: {commit.deletions} 行")

                info_parts.extend(commit_info)

            result = "\n".join(info_parts)
            logger.info("✅ 成功获取 GitHub 项目提交历史")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 获取提交历史失败: {e}"
        logger.error(f"[get_github_commits] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_commits] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub项目结构",
    description="获取 GitHub 项目的目录结构和文件树，可以了解项目的组织方式和主要代码结构",
)
async def get_github_repo_structure(
    _ctx: AgentCtx,
    github_url: str,
    recursive: bool = False,
) -> str:
    """获取 GitHub 项目的目录结构

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        recursive: 是否递归获取所有文件树（默认False只获取第一层）

    Returns:
        str: 项目结构信息

    Example:
        get_github_repo_structure("nodejs/node")
        get_github_repo_structure("torvalds/linux", recursive=True)
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            structure = await client.get_repo_structure(github_url, recursive=recursive)

            if not structure:
                return "⚠️ 未找到任何文件或目录"

            # 构建返回信息
            info_parts = [
                "🗂️  GitHub 项目结构\n",
                f"{'='*60}\n",
                f"总计项目: {len(structure)} 个\n",
                f"{'─'*60}\n",
            ]

            # 按类型分类显示
            files = [item for item in structure if item.type == "blob"]
            dirs = [item for item in structure if item.type == "tree"]

            if dirs:
                info_parts.append(f"\n📁 目录 ({len(dirs)}):\n")
                for d in sorted(dirs, key=lambda x: x.path)[:20]:  # 只显示前20个
                    info_parts.append(f"  📂 {d.path}/")

            if files:
                info_parts.append(f"\n📄 文件 ({len(files)}):\n")
                for f in sorted(files, key=lambda x: x.path)[:20]:  # 只显示前20个
                    size_kb = (f.size or 0) / 1024
                    size_str = f"{size_kb:.1f}KB" if size_kb > 0 else "0B"
                    info_parts.append(f"  📝 {f.path} ({size_str})")

            if len(dirs) > 20 or len(files) > 20:
                info_parts.append("\n💡 提示: 项目包含很多文件，这里仅显示前20个。可以尝试递归模式了解完整结构。")

            result = "\n".join(info_parts)
            logger.info("✅ 成功获取项目结构")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 获取项目结构失败: {e}"
        logger.error(f"[get_github_repo_structure] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_repo_structure] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub项目分支信息",
    description="获取 GitHub 项目的所有分支信息，包括分支名、最新提交等，帮助了解项目的分支管理策略",
)
async def get_github_branches(
    _ctx: AgentCtx,
    github_url: str,
) -> str:
    """获取 GitHub 项目的分支信息

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式

    Returns:
        str: 分支信息

    Example:
        get_github_branches("python/cpython")
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            branches = await client.get_branches(github_url)

            if not branches:
                return "⚠️ 未找到任何分支"

            # 构建返回信息
            info_parts = [
                "🌳 GitHub 项目分支信息\n",
                f"{'='*60}\n",
                f"总共: {len(branches)} 个分支\n",
                f"{'─'*60}\n",
            ]

            for idx, branch in enumerate(branches, 1):
                branch_info = [
                    f"\n{idx}. {branch.name}",
                    f"   Latest SHA: {branch.commit_sha[:7]}",
                ]

                if branch.is_protected:
                    branch_info.append("   🔒 受保护分支")

                info_parts.extend(branch_info)

            result = "\n".join(info_parts)
            logger.info("✅ 成功获取项目分支信息")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 获取分支信息失败: {e}"
        logger.error(f"[get_github_branches] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_branches] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub项目发行版本",
    description="获取 GitHub 项目的发行版本历史，包括版本号、发布时间、发行说明等，用于了解项目的版本演进",
)
async def get_github_releases(
    _ctx: AgentCtx,
    github_url: str,
    per_page: int = 10,
) -> str:
    """获取 GitHub 项目的发行版本

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        per_page: 每页返回的版本数 (1-100，默认10)

    Returns:
        str: 发行版本信息

    Example:
        get_github_releases("torvalds/linux", per_page=5)
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            releases = await client.get_releases(github_url, per_page)

            if not releases:
                return "⚠️ 未找到任何发行版本"

            # 构建返回信息
            info_parts = [
                "📦 GitHub 项目发行版本\n",
                f"{'='*60}\n",
                f"获取版本数: {len(releases)}\n",
                f"{'─'*60}\n",
            ]

            for idx, release in enumerate(releases, 1):
                release_info = [
                    f"\n{idx}. 版本: {release.tag_name}",
                    f"   名称: {release.name}",
                    f"   发布者: {release.author}",
                    f"   发布时间: {release.published_at}",
                ]

                if release.is_prerelease:
                    release_info.append("   ⚠️  预发行版本")
                if release.is_draft:
                    release_info.append("   ✏️  草稿版本")

                if release.body:
                    # 截断过长的发行说明
                    body = release.body[:200] + "..." if len(release.body) > 200 else release.body
                    release_info.append(f"   📝 说明: {body}")

                info_parts.extend(release_info)

            result = "\n".join(info_parts)
            logger.info("✅ 成功获取项目发行版本")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 获取发行版本失败: {e}"
        logger.error(f"[get_github_releases] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_releases] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="查询GitHub项目的Pull Requests",
    description="查询GitHub项目的Pull Requests列表，支持按状态和时间排序，了解项目的代码贡献和改进动态",
)
async def get_github_pull_requests(
    _ctx: AgentCtx,
    github_url: str,
    state: str = "open",
    sort: str = "created",
    per_page: int = 10,
    page: int = 1,
) -> str:
    """查询 GitHub 项目的 Pull Requests

    这是一个代理方法，查询结果会交由 AI 进行分析和对话。

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        state: PR 状态，可选值：
              - open (打开的PR，默认)
              - closed (已关闭的PR)
              - all (所有PR)
        sort: 排序方式，可选值：
              - created (按创建时间排序，默认)
              - updated (按更新时间排序)
              - popularity (按热度排序)
              - long-running (按时间长度排序)
        per_page: 每页返回的 PR 数 (1-100，默认10)
        page: 页码 (默认第1页)

    Returns:
        str: Pull Requests 列表信息

    Example:
        get_github_pull_requests("python/cpython", state="open", per_page=10)
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            pull_requests = await client.get_pull_requests(
                github_url,
                state=state,
                sort=sort,
                per_page=per_page,
                page=page,
            )

            if not pull_requests:
                return f"⚠️ 未找到任何 {state} 状态的 Pull Requests"

            # 构建返回信息
            info_parts = [
                "🔀 GitHub Pull Requests\n",
                f"{'='*60}\n",
                f"状态: {state}",
                f"排序: {sort}",
                f"总获取: {len(pull_requests)} 个\n",
                f"{'─'*60}\n",
            ]

            for idx, pr in enumerate(pull_requests, 1):
                pr_info = [
                    f"\n{idx}. PR #{pr.number}: {pr.title}",
                    f"   🔗 {pr.url}",
                    f"   📊 状态: {pr.state}",
                    f"   👤 作者: {pr.author}",
                    f"   📅 创建时间: {pr.created_at[:10]}",
                ]

                if pr.merged and pr.merged_at:
                    pr_info.append(f"   ✅ 已合并 (by {pr.merged_by} 在 {pr.merged_at[:10]})")
                elif pr.state == "closed":
                    pr_info.append("   ❌ 已关闭")

                if pr.changed_files > 0:
                    pr_info.append(
                        f"   📝 变更: {pr.changed_files} 文件, +{pr.additions} -{pr.deletions} 行",
                    )

                if pr.comments > 0:
                    pr_info.append(f"   💬 评论: {pr.comments} 条")

                if pr.description:
                    # 截断过长的描述
                    desc = pr.description[:100] + "..." if len(pr.description) > 100 else pr.description
                    pr_info.append(f"   📄 描述: {desc}")

                info_parts.extend(pr_info)

            # 添加分页提示
            if per_page * page < 100:  # 粗略估算
                info_parts.append(
                    f"\n\n💡 提示: 可以尝试下一页 (page={page + 1})",
                )

            result = "\n".join(info_parts)
            logger.info(f"✅ 成功查询 GitHub PR，共 {len(pull_requests)} 个")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 查询 PR 失败: {e}"
        logger.error(f"[get_github_pull_requests] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_pull_requests] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="查询GitHub项目的Issues",
    description="查询GitHub项目的Issues列表，支持按状态、标签等方式筛选，了解项目的问题和需求",
)
async def get_github_issues(
    _ctx: AgentCtx,
    github_url: str,
    state: str = "open",
    sort: str = "created",
    per_page: int = 10,
    page: int = 1,
) -> str:
    """查询 GitHub 项目的 Issues

    这是一个代理方法，查询结果会交由 AI 进行分析和对话。

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        state: Issue 状态，可选值：
              - open (打开的Issue，默认)
              - closed (已关闭的Issue)
              - all (所有Issue)
        sort: 排序方式，可选值：
              - created (按创建时间排序，默认)
              - updated (按更新时间排序)
              - comments (按评论数排序)
        per_page: 每页返回的 Issue 数 (1-100，默认10)
        page: 页码 (默认第1页)

    Returns:
        str: Issues 列表信息

    Example:
        get_github_issues("tensorflow/tensorflow", state="open", per_page=10)
        get_github_issues("nodejs/node", state="closed", sort="updated")
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            issues = await client.get_issues(
                github_url,
                state=state,
                sort=sort,
                per_page=per_page,
                page=page,
            )

            if not issues:
                return f"⚠️ 未找到任何 {state} 状态的 Issues"

            # 构建返回信息
            info_parts = [
                "🐛 GitHub Issues\n",
                f"{'='*60}\n",
                f"状态: {state}",
                f"排序: {sort}",
                f"总获取: {len(issues)} 个\n",
                f"{'─'*60}\n",
            ]

            for idx, issue in enumerate(issues, 1):
                issue_info = [
                    f"\n{idx}. Issue #{issue.number}: {issue.title}",
                    f"   🔗 {issue.url}",
                    f"   📊 状态: {issue.state}",
                    f"   👤 创建者: {issue.author}",
                    f"   📅 创建时间: {issue.created_at[:10]}",
                ]

                if issue.closed_at:
                    issue_info.append(f"   ❌ 关闭时间: {issue.closed_at[:10]}")

                if issue.labels:
                    labels_str = ", ".join(issue.labels)
                    issue_info.append(f"   🏷️  标签: {labels_str}")

                if issue.assignees:
                    assignees_str = ", ".join(issue.assignees)
                    issue_info.append(f"   👥 分配给: {assignees_str}")

                if issue.comments > 0:
                    issue_info.append(f"   💬 评论: {issue.comments} 条")

                if issue.description:
                    # 截断过长的描述
                    desc = issue.description[:100] + "..." if len(issue.description) > 100 else issue.description
                    issue_info.append(f"   📄 描述: {desc}")

                info_parts.extend(issue_info)

            # 添加分页提示
            if per_page * page < 100:  # 粗略估算
                info_parts.append(
                    f"\n\n💡 提示: 可以尝试下一页 (page={page + 1})",
                )

            result = "\n".join(info_parts)
            logger.info(f"✅ 成功查询 GitHub Issues，共 {len(issues)} 个")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 查询 Issues 失败: {e}"
        logger.error(f"[get_github_issues] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_issues] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub Pull Request详细信息",
    description="获取GitHub项目的PR详细信息，包括修改的文件列表、commits、审查意见等",
)
async def get_github_pull_request_detail(
    _ctx: AgentCtx,
    github_url: str,
    pr_number: int,
    include_patch: bool = False,
) -> str:
    """获取 GitHub PR 的详细信息

    这是一个代理方法，PR 详细信息会交由 AI 进行分析和对话。

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        pr_number: Pull Request 编号
        include_patch: 是否包含代码 diff patch (会增加数据量，可选)

    Returns:
        str: PR 详细信息

    Example:
        get_github_pull_request_detail("torvalds/linux", pr_number=1234)
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    if not isinstance(pr_number, int) or pr_number < 0:
        return "❌ 错误：pr_number 必须是有效的正整数"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            pr_detail = await client.get_pull_request_detail(
                github_url,
                pr_number,
                include_patch=include_patch,
            )

            # 构建返回信息
            info_parts = [
                f"🔀 Pull Request #{pr_detail.pull_request.number} 详细信息\n",
                f"{'='*70}\n",
                f"标题: {pr_detail.pull_request.title}",
                f"状态: {pr_detail.pull_request.state}",
                f"作者: {pr_detail.pull_request.author}",
                f"创建于: {pr_detail.pull_request.created_at[:10]}",
            ]

            if pr_detail.pull_request.merged and pr_detail.pull_request.merged_at:
                info_parts.append(
                    f"合并于: {pr_detail.pull_request.merged_at[:10]} (by {pr_detail.pull_request.merged_by})",
                )

            info_parts.extend(
                [
                    f"\n{'─'*70}",
                    "📊 代码统计",
                    f"{'─'*70}",
                    f"总计变更: +{pr_detail.pull_request.additions} -{pr_detail.pull_request.deletions} 行",
                    f"修改文件数: {pr_detail.total_files_changed}",
                    f"Commits 数: {pr_detail.total_commits}",
                    f"评论数: {pr_detail.pull_request.comments}",
                    f"Reviews 数: {len(pr_detail.reviews)}",
                ],
            )

            if pr_detail.pull_request.description:
                desc = (
                    pr_detail.pull_request.description[:300] + "..."
                    if len(pr_detail.pull_request.description) > 300
                    else pr_detail.pull_request.description
                )
                info_parts.extend(
                    [
                        "\n📝 描述",
                        f"{'─'*70}",
                        desc,
                    ],
                )

            if pr_detail.commits:
                info_parts.extend(
                    [
                        f"\n{'─'*70}",
                        f"📋 Commits ({len(pr_detail.commits)})",
                        f"{'─'*70}",
                    ],
                )

                for idx, commit in enumerate(pr_detail.commits[:10], 1):  # 只显示前10个
                    info_parts.extend(
                        [
                            f"{idx}. {commit.sha}: {commit.message}",
                            f"   作者: {commit.author_name}",
                            f"   时间: {commit.committed_at[:10]}",
                        ],
                    )

                if len(pr_detail.commits) > 10:
                    info_parts.append(f"\n💡 还有 {len(pr_detail.commits) - 10} 个 commit 未显示")

            if pr_detail.files_changed:
                info_parts.extend(
                    [
                        f"\n{'─'*70}",
                        f"📄 修改的文件 ({len(pr_detail.files_changed)})",
                        f"{'─'*70}",
                    ],
                )

                for idx, file in enumerate(pr_detail.files_changed[:15], 1):  # 只显示前15个
                    status_emoji = {
                        "added": "➕",
                        "removed": "➖",
                        "modified": "✏️",
                        "renamed": "🔄",
                    }.get(file.status, "📝")

                    info_parts.append(
                        f"{idx}. {status_emoji} {file.filename} (+{file.additions} -{file.deletions})",
                    )

                if len(pr_detail.files_changed) > 15:
                    info_parts.append(f"\n💡 还有 {len(pr_detail.files_changed) - 15} 个文件未显示")

            if pr_detail.reviews:
                info_parts.extend(
                    [
                        f"\n{'─'*70}",
                        f"👁️  Reviews ({len(pr_detail.reviews)})",
                        f"{'─'*70}",
                    ],
                )

                for idx, review in enumerate(pr_detail.reviews, 1):
                    state_emoji = {
                        "APPROVED": "✅",
                        "CHANGES_REQUESTED": "❌",
                        "COMMENTED": "💬",
                        "PENDING": "⏳",
                    }.get(review.state, "📝")

                    info_parts.append(
                        f"{idx}. {state_emoji} {review.reviewer}: {review.state}",
                    )

                    if review.body:
                        body = review.body[:100] + "..." if len(review.body) > 100 else review.body
                        info_parts.append(f"   💭 {body}")

            result = "\n".join(info_parts)
            logger.info(f"✅ 成功获取 PR #{pr_number} 详细信息")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 获取 PR 详细信息失败: {e}"
        logger.error(f"[get_github_pull_request_detail] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_pull_request_detail] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub Issue详细信息",
    description="获取GitHub项目的Issue详细信息，包括完整描述、所有评论、标签等",
)
async def get_github_issue_detail(
    _ctx: AgentCtx,
    github_url: str,
    issue_number: int,
) -> str:
    """获取 GitHub Issue 的详细信息

    这是一个代理方法，Issue 详细信息会交由 AI 进行分析和对话。

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        issue_number: Issue 编号

    Returns:
        str: Issue 详细信息及评论

    Example:
        get_github_issue_detail("numpy/numpy", issue_number=12345)
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    if not isinstance(issue_number, int) or issue_number < 0:
        return "❌ 错误：issue_number 必须是有效的正整数"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            issue_detail = await client.get_issue_detail(
                github_url,
                issue_number,
            )

            # 构建返回信息
            info_parts = [
                f"🐛 Issue #{issue_detail.issue.number} 详细信息\n",
                f"{'='*70}\n",
                f"标题: {issue_detail.issue.title}",
                f"状态: {issue_detail.issue.state}",
                f"创建者: {issue_detail.issue.author}",
                f"创建于: {issue_detail.issue.created_at[:10]}",
            ]

            if issue_detail.issue.closed_at:
                info_parts.append(f"关闭于: {issue_detail.issue.closed_at[:10]}")

            if issue_detail.issue.labels:
                labels_str = ", ".join(issue_detail.issue.labels)
                info_parts.append(f"标签: {labels_str}")

            if issue_detail.issue.assignees:
                assignees_str = ", ".join(issue_detail.issue.assignees)
                info_parts.append(f"分配给: {assignees_str}")

            info_parts.extend(
                [
                    f"\n{'─'*70}",
                    "📊 统计信息",
                    f"{'─'*70}",
                    f"评论数: {issue_detail.total_comments}",
                ],
            )

            if issue_detail.issue.description:
                info_parts.extend(
                    [
                        "\n📝 描述",
                        f"{'─'*70}",
                        issue_detail.issue.description,
                    ],
                )

            if issue_detail.comments_list:
                info_parts.extend(
                    [
                        f"\n{'─'*70}",
                        f"💬 评论 ({len(issue_detail.comments_list)})",
                        f"{'─'*70}",
                    ],
                )

                for idx, comment in enumerate(issue_detail.comments_list[:20], 1):  # 只显示前20条评论
                    reactions_str = ""
                    if comment.reactions:
                        reactions_str = " [" + ", ".join(f"{emoji}:{count}" for emoji, count in comment.reactions.items()) + "]"

                    info_parts.extend(
                        [
                            f"\n{idx}. {comment.author} ({comment.created_at[:10]}){reactions_str}",
                            f"{'─'*70}",
                        ],
                    )

                    # 截断长评论
                    body = comment.body
                    if len(body) > 500:
                        body = body[:500] + "\n...(评论已截断)"

                    info_parts.append(body)

                if len(issue_detail.comments_list) > 20:
                    info_parts.append(
                        f"\n💡 还有 {len(issue_detail.comments_list) - 20} 条评论未显示",
                    )

            result = "\n".join(info_parts)
            logger.info(f"✅ 成功获取 Issue #{issue_number} 详细信息")
            return result

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 获取 Issue 详细信息失败: {e}"
        logger.error(f"[get_github_issue_detail] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[get_github_issue_detail] {error_msg}")
        return error_msg


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取GitHub项目贡献者列表",
    description="获取GitHub项目的贡献者列表，包括每个贡献者的用户名、贡献次数等信息，支持分页",
)
async def get_github_contributors(
    _ctx: AgentCtx,
    github_url: str,
    per_page: int = 30,
    page: int = 1,
) -> str:
    """获取 GitHub 项目的贡献者列表

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式
        per_page: 每页返回的贡献者数 (1-100，默认30)
        page: 页码 (默认第1页)

    Returns:
        str: 贡献者列表信息

    Example:
        get_github_contributors("python/cpython", per_page=20)
        get_github_contributors("django/django", page=2)
    """
    try:
        # 参数验证
        github_url = ParameterValidator.validate_github_url(github_url)
        per_page = ParameterValidator.validate_per_page(per_page, default=30)
        page = ParameterValidator.validate_page(page)

        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            contributors = await client.get_contributors(
                github_url,
                per_page=per_page,
                page=page,
            )

            if not contributors:
                return ResponseFormatter.warning("未找到任何贡献者")

            # 构建返回信息
            parts = [
                ResponseFormatter.section("👥 GitHub 项目贡献者列表"),
                f"总获取: {len(contributors)} 个贡献者\n",
                f"分页: 第 {page} 页，每页 {per_page} 个\n",
                f"{'─'*60}\n",
            ]

            for idx, contributor in enumerate(contributors, 1):
                parts.append(f"\n{idx}. {contributor.login}\n")
                parts.append(f"   🔗 {contributor.url}\n")
                parts.append(f"   📊 贡献数: {contributor.contributions}\n")

                if contributor.type and contributor.type != "User":
                    parts.append(f"   🤖 类型: {contributor.type}\n")

            # 添加分页提示
            parts.append(f"\n{'─'*60}\n")
            parts.append(f"💡 提示: 可以尝试其他页码 (page={page + 1})\n")

            result = ResponseFormatter.build(parts)
            logger.info(
                f"✅ 成功获取贡献者列表，共 {len(contributors)} 个",
            )
            return result

    except ValidationError as e:
        return ExceptionHandler.handle_validation_error("get_github_contributors", e)
    except Exception as e:
        return ExceptionHandler.handle_runtime_error("get_github_contributors", e)


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="GitHub项目质量评分",
    description="对GitHub项目进行综合质量评分（0-100分），输出简洁评估报告，包含代码质量、活跃度、社区健康度三个维度的评分及建议",
)
async def evaluate_github_project(
    _ctx: AgentCtx,
    github_url: str,
) -> str:
    """GitHub 项目综合评分与质量分析

    这个方法使用专业评分算法对 GitHub 项目进行全面评分，从代码质量、项目活跃度和社区健康度三个维度，
    生成详细的评估报告，包含：
    - 综合评分（0-100分）和评级（A+/A/B+/B/C/D）
    - 代码质量得分（文档、维护性、代码组织）
    - 活跃度得分（Commit、Issue/PR、发布频率）
    - 社区健康度得分（参与度、互动、成熟度）
    - 项目优势和不足分析
    - 使用建议（强烈推荐/推荐/可以使用/谨慎使用/不推荐）

    评估维度：
    - 代码质量 (30分): 文档完整性、项目维护性、代码组织
    - 项目活跃度 (40分): Commit 活跃度、Issue/PR 响应、发布频率
    - 社区健康度 (30分): 社区参与度、社区互动、项目成熟度

    评级标准：
    - A+ (85-100): 优秀 - 强烈推荐
    - A (75-84): 良好 - 推荐使用
    - B+ (65-74): 中上 - 可以使用
    - B (55-64): 中等 - 谨慎使用
    - C (45-54): 一般 - 需要评估风险
    - D (0-44): 较差 - 不推荐

    Args:
        github_url: GitHub 项目 URL 或 owner/repo 格式，例如：
                   - https://github.com/fastapi/fastapi
                   - python/cpython
                   - git@github.com:torvalds/linux.git

    Returns:
        str: Markdown 格式的评估报告，包含评分卡片、详细指标和建议

    Example:
        evaluate_github_project("https://github.com/fastapi/fastapi")
        evaluate_github_project("python/cpython")
        evaluate_github_project("tensorflow/tensorflow")
    """
    if not github_url or not isinstance(github_url, str):
        return "❌ 错误：github_url 参数不能为空"

    # 检查 token 配置
    if not config.GITHUB_TOKEN:
        return "❌ 错误：未配置 GitHub Token，免费 API 次数不足以完成评分\n请在配置中设置 GITHUB_TOKEN (个人访问令牌)"

    try:
        async with GitHubClient(
            token=config.GITHUB_TOKEN,
            timeout=config.GITHUB_API_TIMEOUT,
        ) as client:
            # 导入评估器和格式化器
            from .evaluator import GitHubProjectEvaluator
            from .formatter import EvaluationFormatter

            # 创建评估器并执行评估
            evaluator = GitHubProjectEvaluator(client)
            evaluation = await evaluator.evaluate_project(github_url)

            # 生成简洁报告（仅限1000字符）
            report = EvaluationFormatter.to_brief_report(evaluation)

            logger.info(
                f"✅ 成功评估项目 {evaluation.repo_full_name}，"
                f"得分 {evaluation.total_score:.1f}/100，评级 {evaluation.rating}",
            )

            return report

    except (ValueError, RuntimeError) as e:
        error_msg = f"❌ 评估失败: {e}"
        logger.error(f"[evaluate_github_project] {error_msg}")
        return error_msg

    except Exception as e:
        error_msg = f"❌ 未预期的错误: {type(e).__name__}: {e}"
        logger.exception(f"[evaluate_github_project] {error_msg}")
        return error_msg
